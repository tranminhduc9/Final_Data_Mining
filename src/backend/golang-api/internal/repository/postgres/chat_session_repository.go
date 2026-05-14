package postgres

import (
	"context"
	"fmt"
	"time"

	"github.com/techpulsevn/final-data-mining/golang-api/internal/database"
)

type ChatSessionRepository struct {
	DB *database.Postgres
}

func NewChatSessionRepository(db *database.Postgres) *ChatSessionRepository {
	return &ChatSessionRepository{DB: db}
}

type ChatSessionRow struct {
	ID        string
	Title     *string
	CreatedAt time.Time
}

func (r *ChatSessionRepository) ListByUserID(ctx context.Context, userID string) ([]ChatSessionRow, error) {
	rows, err := r.DB.Pool.Query(ctx,
		`SELECT id, title, created_at FROM chat_session WHERE user_id = $1 ORDER BY created_at DESC`,
		userID,
	)
	if err != nil {
		return nil, fmt.Errorf("chat_session list: %w", err)
	}
	defer rows.Close()

	var result []ChatSessionRow
	for rows.Next() {
		var s ChatSessionRow
		if err := rows.Scan(&s.ID, &s.Title, &s.CreatedAt); err != nil {
			return nil, fmt.Errorf("chat_session scan: %w", err)
		}
		result = append(result, s)
	}
	return result, rows.Err()
}
