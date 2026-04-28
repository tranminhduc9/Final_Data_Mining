package postgres

import (
	"context"
	"fmt"
	"time"

	"github.com/techpulsevn/final-data-mining/golang-api/internal/database"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/domain"
)

type AnalyticsRepository struct {
	DB *database.Postgres
}

func NewAnalyticsRepository(db *database.Postgres) *AnalyticsRepository {
	return &AnalyticsRepository{DB: db}
}

func (r *AnalyticsRepository) RecordVisit(ctx context.Context, ip string, t time.Time) error {
	_, err := r.DB.Pool.Exec(ctx,
		`INSERT INTO page_visits (visit_date, ip_address) VALUES ($1, $2) ON CONFLICT DO NOTHING`,
		t.UTC().Format("2006-01-02"), ip,
	)
	return err
}

func (r *AnalyticsRepository) RecordSearch(ctx context.Context, keyword, endpoint string) error {
	_, err := r.DB.Pool.Exec(ctx,
		`INSERT INTO keyword_searches (keyword, endpoint) VALUES ($1, $2)`,
		keyword, endpoint,
	)
	return err
}

func (r *AnalyticsRepository) GetStats(ctx context.Context) (*domain.AdminStats, error) {
	today := time.Now().UTC().Format("2006-01-02")
	var stats domain.AdminStats

	if err := r.DB.Pool.QueryRow(ctx, `SELECT COUNT(*) FROM users`).Scan(&stats.TotalUsers); err != nil {
		return nil, fmt.Errorf("count users: %w", err)
	}
	if err := r.DB.Pool.QueryRow(ctx,
		`SELECT COUNT(*) FROM page_visits WHERE visit_date = $1`, today,
	).Scan(&stats.VisitsToday); err != nil {
		return nil, fmt.Errorf("count visits: %w", err)
	}
	if err := r.DB.Pool.QueryRow(ctx,
		`SELECT COUNT(*) FROM keyword_searches WHERE searched_at::date = $1`, today,
	).Scan(&stats.SearchesToday); err != nil {
		return nil, fmt.Errorf("count searches: %w", err)
	}

	return &stats, nil
}

func (r *AnalyticsRepository) GetTopKeywords(ctx context.Context, limit int) ([]domain.KeywordCount, error) {
	rows, err := r.DB.Pool.Query(ctx,
		`SELECT keyword, COUNT(*) AS count
		 FROM keyword_searches
		 GROUP BY keyword
		 ORDER BY count DESC
		 LIMIT $1`,
		limit,
	)
	if err != nil {
		return nil, fmt.Errorf("top keywords: %w", err)
	}
	defer rows.Close()

	var results []domain.KeywordCount
	for rows.Next() {
		var kc domain.KeywordCount
		if err := rows.Scan(&kc.Keyword, &kc.Count); err != nil {
			return nil, err
		}
		results = append(results, kc)
	}
	if results == nil {
		results = []domain.KeywordCount{}
	}
	return results, rows.Err()
}
