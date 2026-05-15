// Package kafka provides Kafka producer and consumer implementations
package kafka

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"time"

	"github.com/segmentio/kafka-go"
)

// Producer wraps kafka.Writer with convenience methods
type Producer struct {
	writer *kafka.Writer
}

// NewProducer creates a new Kafka producer
func NewProducer(brokers []string) *Producer {
	return &Producer{
		writer: &kafka.Writer{
			Addr:         kafka.TCP(brokers...),
			Balancer:     &kafka.LeastBytes{},
			RequiredAcks: kafka.RequireOne,
			Async:        false,
			Compression:  kafka.Snappy,
		},
	}
}

// Publish sends a message to a Kafka topic
func (p *Producer) Publish(ctx context.Context, topic string, key []byte, value interface{}) error {
	data, err := json.Marshal(value)
	if err != nil {
		return fmt.Errorf("failed to marshal message: %w", err)
	}

	msg := kafka.Message{
		Topic: topic,
		Key:   key,
		Value: data,
		Time:  time.Now(),
	}

	if err := p.writer.WriteMessages(ctx, msg); err != nil {
		return fmt.Errorf("failed to publish message: %w", err)
	}

	return nil
}

// PublishBatch sends multiple messages to a Kafka topic
func (p *Producer) PublishBatch(ctx context.Context, topic string, messages []kafka.Message) error {
	for i := range messages {
		messages[i].Topic = topic
		if messages[i].Time.IsZero() {
			messages[i].Time = time.Now()
		}
	}

	if err := p.writer.WriteMessages(ctx, messages...); err != nil {
		return fmt.Errorf("failed to publish batch: %w", err)
	}

	return nil
}

// Close closes the producer
func (p *Producer) Close() error {
	return p.writer.Close()
}

// Consumer wraps kafka.Reader with convenience methods
type Consumer struct {
	reader *kafka.Reader
}

// NewConsumer creates a new Kafka consumer
func NewConsumer(brokers []string, topic, groupID string) *Consumer {
	return &Consumer{
		reader: kafka.NewReader(kafka.ReaderConfig{
			Brokers:        brokers,
			Topic:          topic,
			GroupID:        groupID,
			MinBytes:       1,
			MaxBytes:       10e6, // 10MB
			CommitInterval: time.Second,
			StartOffset:    kafka.LastOffset,
		}),
	}
}

// Read reads a single message from the topic
func (c *Consumer) Read(ctx context.Context) (kafka.Message, error) {
	return c.reader.ReadMessage(ctx)
}

// FetchMessage fetches a message without committing
func (c *Consumer) FetchMessage(ctx context.Context) (kafka.Message, error) {
	return c.reader.FetchMessage(ctx)
}

// CommitMessages commits the given messages
func (c *Consumer) CommitMessages(ctx context.Context, msgs ...kafka.Message) error {
	return c.reader.CommitMessages(ctx, msgs...)
}

// Close closes the consumer
func (c *Consumer) Close() error {
	return c.reader.Close()
}

// ConsumeLoop runs a continuous consumption loop with handler function
func (c *Consumer) ConsumeLoop(ctx context.Context, handler func(msg kafka.Message) error) error {
	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		default:
			msg, err := c.reader.ReadMessage(ctx)
			if err != nil {
				log.Printf("Error reading message: %v", err)
				continue
			}

			if err := handler(msg); err != nil {
				log.Printf("Error handling message: %v", err)
				// Continue processing other messages
			}
		}
	}
}

// CreateTopics creates Kafka topics if they don't exist
func CreateTopics(brokers []string, topics []string, partitions, replicationFactor int) error {
	conn, err := kafka.Dial("tcp", brokers[0])
	if err != nil {
		return fmt.Errorf("failed to connect to Kafka: %w", err)
	}
	defer conn.Close()

	controller, err := conn.Controller()
	if err != nil {
		return fmt.Errorf("failed to get controller: %w", err)
	}

	controllerConn, err := kafka.Dial("tcp", fmt.Sprintf("%s:%d", controller.Host, controller.Port))
	if err != nil {
		return fmt.Errorf("failed to connect to controller: %w", err)
	}
	defer controllerConn.Close()

	var topicConfigs []kafka.TopicConfig
	for _, topic := range topics {
		topicConfigs = append(topicConfigs, kafka.TopicConfig{
			Topic:             topic,
			NumPartitions:     partitions,
			ReplicationFactor: replicationFactor,
		})
	}

	if err := controllerConn.CreateTopics(topicConfigs...); err != nil {
		// Ignore "topic already exists" error
		if err.Error() != "Topic with this name already exists" {
			return fmt.Errorf("failed to create topics: %w", err)
		}
	}

	return nil
}