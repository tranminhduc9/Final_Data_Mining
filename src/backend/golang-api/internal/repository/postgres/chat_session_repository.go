package postgres

import "github.com/techpulsevn/final-data-mining/golang-api/internal/database"

type ChatSessionRepository struct {
	DB *database.Postgres
}

func NewChatSessionRepository(db *database.Postgres) *ChatSessionRepository {
	return &ChatSessionRepository{DB: db}
}
