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

func (r *AnalyticsRepository) GetUserCount(ctx context.Context) (int, error) {
	var count int
	err := r.DB.Pool.QueryRow(ctx, `SELECT COUNT(*) FROM users`).Scan(&count)
	return count, err
}

func (r *AnalyticsRepository) GetVisitsToday(ctx context.Context) (int, error) {
	var count int
	err := r.DB.Pool.QueryRow(ctx,
		`SELECT COUNT(*) FROM page_visits WHERE visit_date = CURRENT_DATE`,
	).Scan(&count)
	return count, err
}

func (r *AnalyticsRepository) GetSearchesToday(ctx context.Context) (int, error) {
	var count int
	err := r.DB.Pool.QueryRow(ctx,
		`SELECT COUNT(*) FROM keyword_searches WHERE searched_at::date = CURRENT_DATE`,
	).Scan(&count)
	return count, err
}

// GetMonthlyVisits returns unique visitor counts per month for the last `months` months.
func (r *AnalyticsRepository) GetMonthlyVisits(ctx context.Context, months int) ([]domain.MonthlyVisit, error) {
	rows, err := r.DB.Pool.Query(ctx, `
		SELECT
			TO_CHAR(gs.month, 'YYYY-MM') AS month,
			COUNT(DISTINCT pv.ip_address) AS count
		FROM generate_series(
			DATE_TRUNC('month', CURRENT_DATE) - $1 * INTERVAL '1 month',
			DATE_TRUNC('month', CURRENT_DATE),
			INTERVAL '1 month'
		) AS gs(month)
		LEFT JOIN page_visits pv
			ON pv.visit_date >= gs.month::date
			AND pv.visit_date < (gs.month + INTERVAL '1 month')::date
		GROUP BY gs.month
		ORDER BY gs.month ASC
	`, months-1)
	if err != nil {
		return nil, fmt.Errorf("monthly visits: %w", err)
	}
	defer rows.Close()

	var results []domain.MonthlyVisit
	for rows.Next() {
		var mv domain.MonthlyVisit
		if err := rows.Scan(&mv.Month, &mv.Count); err != nil {
			return nil, err
		}
		results = append(results, mv)
	}
	if results == nil {
		results = []domain.MonthlyVisit{}
	}
	return results, rows.Err()
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
