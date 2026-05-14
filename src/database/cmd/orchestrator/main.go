// Package main is the entry point for the TechPulse VN orchestrator
package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/techpulse/graph_database/internal/entity_extractor"
	"github.com/techpulse/graph_database/internal/kafka"
	"github.com/techpulse/graph_database/internal/neo4j_writer"
	"github.com/techpulse/graph_database/internal/qdrant_writer"
	"github.com/techpulse/graph_database/pkg/config"
)

// Orchestrator manages the pipeline execution
// Note: Embedding service runs as a separate Python service
type Orchestrator struct {
	config          *config.Config
	entityExtractor *entity_extractor.Extractor
	neo4jWriter     *neo4j_writer.Writer
	qdrantWriter    *qdrant_writer.Writer
}

// NewOrchestrator creates a new orchestrator
func NewOrchestrator(cfg *config.Config) *Orchestrator {
	return &Orchestrator{
		config: cfg,
	}
}

// Initialize initializes all services
func (o *Orchestrator) Initialize(ctx context.Context) error {
	log.Println("Initializing orchestrator...")

	// Initialize entity extractor
	o.entityExtractor = entity_extractor.NewExtractor(o.config)
	o.entityExtractor.Connect()

	// Initialize Neo4j writer
	o.neo4jWriter = neo4j_writer.NewWriter(o.config)
	if err := o.neo4jWriter.Connect(ctx); err != nil {
		return fmt.Errorf("failed to connect to Neo4j: %w", err)
	}
	if err := o.neo4jWriter.CreateConstraints(ctx); err != nil {
		log.Printf("Warning: failed to create Neo4j constraints: %v", err)
	}

	// Initialize Qdrant writer
	o.qdrantWriter = qdrant_writer.NewWriter(o.config)
	if err := o.qdrantWriter.Connect(ctx); err != nil {
		log.Printf("Warning: failed to connect to Qdrant: %v", err)
	}
	if err := o.qdrantWriter.CreateCollections(ctx); err != nil {
		log.Printf("Warning: failed to create Qdrant collections: %v", err)
	}

	log.Println("Orchestrator initialized successfully")
	log.Println("Note: Embedding service runs as separate Python container")
	return nil
}

// CreateKafkaTopics creates all required Kafka topics
func (o *Orchestrator) CreateKafkaTopics() error {
	topics := []string{
		o.config.Kafka.TopicRawArticles,
		o.config.Kafka.TopicRawJobs,
		o.config.Kafka.TopicExtractedArticles,
		o.config.Kafka.TopicExtractedJobs,
		o.config.Kafka.TopicArticleVectors,
		o.config.Kafka.TopicJobVectors,
	}

	log.Println("Creating Kafka topics...")
	err := kafka.CreateTopics(o.config.Kafka.Brokers, topics, 3, 1)
	if err != nil {
		log.Printf("Warning creating Kafka topics: %v", err)
	} else {
		log.Println("Kafka topics created/verified")
	}
	return err
}

// RunAllServices starts all processing services
// Note: Embedding service (Python) runs separately via docker-compose
func (o *Orchestrator) RunAllServices(ctx context.Context) error {
	log.Println("Starting processing services (Entity Extractor + Neo4j + Qdrant)...")
	log.Println("Embedding service (Python) should be running separately")

	errChan := make(chan error, 3)

	// Entity Extractor
	go func() {
		log.Println("Starting Entity Extractor...")
		if err := o.entityExtractor.Run(ctx); err != nil && err != context.Canceled {
			errChan <- fmt.Errorf("entity extractor error: %w", err)
		}
	}()

	// Neo4j Writer
	go func() {
		log.Println("Starting Neo4j Writer...")
		if err := o.neo4jWriter.Run(ctx); err != nil && err != context.Canceled {
			errChan <- fmt.Errorf("neo4j writer error: %w", err)
		}
	}()

	// Qdrant Writer
	go func() {
		log.Println("Starting Qdrant Writer...")
		if err := o.qdrantWriter.Run(ctx); err != nil && err != context.Canceled {
			errChan <- fmt.Errorf("qdrant writer error: %w", err)
		}
	}()

	// Wait for errors or context cancellation
	select {
	case err := <-errChan:
		return err
	case <-ctx.Done():
		return ctx.Err()
	}
}

// Close closes all connections
func (o *Orchestrator) Close() {
	log.Println("Closing orchestrator...")

	if o.entityExtractor != nil {
		o.entityExtractor.Close()
	}
	if o.neo4jWriter != nil {
		o.neo4jWriter.Close()
	}
	if o.qdrantWriter != nil {
		o.qdrantWriter.Close()
	}

	log.Println("Orchestrator closed")
}

func main() {
	// Load configuration from .env
	cfg := config.Load()

	// Validate required config
	if cfg.Neo4j.URI == "" {
		log.Fatal("NEO4J_URI is required but not set")
	}
	if cfg.Neo4j.Username == "" {
		log.Fatal("NEO4J_USERNAME is required but not set")
	}
	if cfg.Neo4j.Password == "" {
		log.Fatal("NEO4J_PASSWORD is required but not set")
	}

	log.Printf("Config loaded: Neo4j URI=%s, Database=%s", cfg.Neo4j.URI, cfg.Neo4j.Database)

	// Create orchestrator
	orch := NewOrchestrator(cfg)

	// Setup context with cancellation
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Handle shutdown signals
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		<-sigChan
		log.Println("Received shutdown signal...")
		cancel()
	}()

	// Initialize
	if err := orch.Initialize(ctx); err != nil {
		log.Fatalf("Failed to initialize orchestrator: %v", err)
	}
	defer orch.Close()

	// Create Kafka topics
	orch.CreateKafkaTopics()

	// Run all services
	log.Println("Starting TechPulse VN Pipeline (Crawl -> Extract -> Neo4j + Qdrant)...")
	log.Println("Embedding service (Python/SentenceTransformers) runs as separate container")
	if err := orch.RunAllServices(ctx); err != nil {
		log.Printf("Pipeline error: %v", err)
	}

	log.Println("Pipeline shutdown complete")
}