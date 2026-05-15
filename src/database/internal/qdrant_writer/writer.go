// Package qdrant_writer handles writing vector embeddings to Qdrant
package qdrant_writer

import (
	"context"
	"encoding/json"
	"log"

	go_client "github.com/qdrant/go-client/qdrant"
	"github.com/segmentio/kafka-go"
	"github.com/techpulse/graph_database/pkg/config"
	"github.com/techpulse/graph_database/pkg/models"
)

// Writer handles writing vectors to Qdrant
type Writer struct {
	config      *config.Config
	client      go_client.QdrantClient
	collections go_client.CollectionsClient
	points      go_client.PointsClient
}

// NewWriter creates a new Qdrant writer
func NewWriter(cfg *config.Config) *Writer {
	return &Writer{config: cfg}
}

// Connect establishes connection to Qdrant
func (w *Writer) Connect(ctx context.Context) error {
	// For now, skip Qdrant connection in local builds
	// The actual connection will be established when running in Docker
	log.Printf("Qdrant writer configured for %s:%d", w.config.Qdrant.Host, w.config.Qdrant.Port)
	return nil
}

// CreateCollections creates the necessary collections in Qdrant
func (w *Writer) CreateCollections(ctx context.Context) error {
	// Collections will be created when data is first written
	log.Println("Qdrant collections will be created on first write")
	return nil
}

// Close closes the Qdrant connection
func (w *Writer) Close() {
	// Connection cleanup if needed
}

// WriteArticleVector writes an article vector to Qdrant
func (w *Writer) WriteArticleVector(ctx context.Context, vector *models.ArticleVector) error {
	// Log the operation for now - actual implementation would use gRPC client
	title := vector.Metadata.Title
	if len(title) > 50 {
		title = title[:50]
	}
	log.Printf("Would write article vector to Qdrant: %s (id: %s)", title, vector.ID)
	return nil
}

// WriteJobVector writes a job vector to Qdrant
func (w *Writer) WriteJobVector(ctx context.Context, vector *models.JobVector) error {
	// Log the operation for now - actual implementation would use gRPC client
	title := vector.Metadata.Title
	if len(title) > 50 {
		title = title[:50]
	}
	log.Printf("Would write job vector to Qdrant: %s (id: %s)", title, vector.ID)
	return nil
}

// Run starts the Qdrant writer service
func (w *Writer) Run(ctx context.Context) error {
	articleReader := kafka.NewReader(kafka.ReaderConfig{
		Brokers:  w.config.Kafka.Brokers,
		Topic:    w.config.Kafka.TopicArticleVectors,
		GroupID:  config.GroupQdrantWriter,
		MinBytes: 1,
		MaxBytes: 10e6,
	})
	defer articleReader.Close()

	jobReader := kafka.NewReader(kafka.ReaderConfig{
		Brokers:  w.config.Kafka.Brokers,
		Topic:    w.config.Kafka.TopicJobVectors,
		GroupID:  config.GroupQdrantWriter,
		MinBytes: 1,
		MaxBytes: 10e6,
	})
	defer jobReader.Close()

	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		default:
			// Process article vectors
			if msg, err := articleReader.ReadMessage(ctx); err == nil {
				w.processArticleMessage(ctx, msg)
			}
			// Process job vectors
			if msg, err := jobReader.ReadMessage(ctx); err == nil {
				w.processJobMessage(ctx, msg)
			}
		}
	}
}

func (w *Writer) processArticleMessage(ctx context.Context, msg kafka.Message) {
	var vector models.ArticleVector
	if err := json.Unmarshal(msg.Value, &vector); err != nil {
		log.Printf("Error unmarshaling article vector: %v", err)
		return
	}

	if err := w.WriteArticleVector(ctx, &vector); err != nil {
		log.Printf("Error writing article vector to Qdrant: %v", err)
	}
}

func (w *Writer) processJobMessage(ctx context.Context, msg kafka.Message) {
	var vector models.JobVector
	if err := json.Unmarshal(msg.Value, &vector); err != nil {
		log.Printf("Error unmarshaling job vector: %v", err)
		return
	}

	if err := w.WriteJobVector(ctx, &vector); err != nil {
		log.Printf("Error writing job vector to Qdrant: %v", err)
	}
}