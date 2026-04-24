package postgres

import "github.com/techpulsevn/final-data-mining/golang-api/internal/database"

type ChatMessageRepository struct {
	DB *database.Postgres
}

func NewChatMessageRepository(db *database.Postgres) *ChatMessageRepository {
	return &ChatMessageRepository{DB: db}
}
