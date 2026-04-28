package postgres

import (
	"context"
	"fmt"

	"github.com/techpulsevn/final-data-mining/golang-api/internal/database"
)

type SettingsRepository struct {
	DB *database.Postgres
}

func NewSettingsRepository(db *database.Postgres) *SettingsRepository {
	return &SettingsRepository{DB: db}
}

func (r *SettingsRepository) Get(ctx context.Context, key string) (string, error) {
	var value string
	err := r.DB.Pool.QueryRow(ctx,
		`SELECT value FROM settings WHERE key = $1`, key,
	).Scan(&value)
	if err != nil {
		return "", fmt.Errorf("settings get %s: %w", key, err)
	}
	return value, nil
}

func (r *SettingsRepository) Set(ctx context.Context, key, value string) error {
	tag, err := r.DB.Pool.Exec(ctx,
		`UPDATE settings SET value = $2, updated_at = NOW() WHERE key = $1`,
		key, value,
	)
	if err != nil {
		return fmt.Errorf("settings set %s: %w", key, err)
	}
	if tag.RowsAffected() == 0 {
		return ErrNotFound
	}
	return nil
}

func (r *SettingsRepository) GetAll(ctx context.Context) (map[string]string, error) {
	rows, err := r.DB.Pool.Query(ctx, `SELECT key, value FROM settings`)
	if err != nil {
		return nil, fmt.Errorf("settings get all: %w", err)
	}
	defer rows.Close()

	result := map[string]string{}
	for rows.Next() {
		var k, v string
		if err := rows.Scan(&k, &v); err != nil {
			return nil, fmt.Errorf("settings scan: %w", err)
		}
		result[k] = v
	}
	return result, rows.Err()
}
