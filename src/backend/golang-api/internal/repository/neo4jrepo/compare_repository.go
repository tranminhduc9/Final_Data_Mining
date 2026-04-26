package neo4jrepo

import (
	"context"
	"fmt"
	"time"

	"github.com/neo4j/neo4j-go-driver/v5/neo4j"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/database"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/domain"
)

type CompareRepository struct {
	DB *database.Neo4jDB
}

func NewCompareRepository(db *database.Neo4jDB) *CompareRepository {
	return &CompareRepository{DB: db}
}

// GetMonthlyByKeywords returns monthly job counts per keyword within [windowStart, now].
func (r *CompareRepository) GetMonthlyByKeywords(ctx context.Context, keywords []string, windowStart time.Time) (map[string][]domain.CompareMonthlyCount, error) {
	session := r.DB.Driver.NewSession(ctx, neo4j.SessionConfig{
		AccessMode:   neo4j.AccessModeRead,
		DatabaseName: r.DB.Database,
	})
	defer session.Close(ctx)

	query := `
		UNWIND $keywords AS kw
		MATCH (j:Job)
		WHERE j.title IS NOT NULL
		  AND j.posted_date IS NOT NULL
		  AND datetime(j.posted_date) >= datetime($window_start)
		  AND toLower(j.title) CONTAINS toLower(kw)
		WITH kw, date(datetime(j.posted_date)).year AS year, date(datetime(j.posted_date)).month AS month, j
		RETURN kw AS keyword, year, month, count(j) AS job_count
		ORDER BY keyword, year, month
	`

	result, err := session.Run(ctx, query, map[string]interface{}{
		"keywords":     keywords,
		"window_start": windowStart.Format("2006-01-02"),
	})
	if err != nil {
		return nil, fmt.Errorf("neo4j query compare monthly: %w", err)
	}

	out := make(map[string][]domain.CompareMonthlyCount)
	for result.Next(ctx) {
		rec := result.Record()
		kw := toString(rec.Values[0])
		y := toInt(rec.Values[1])
		m := toInt(rec.Values[2])
		c := toInt(rec.Values[3])
		out[kw] = append(out[kw], domain.CompareMonthlyCount{Year: y, Month: m, JobCount: c})
	}
	if err := result.Err(); err != nil {
		return nil, fmt.Errorf("neo4j result compare monthly: %w", err)
	}

	return out, nil
}

// GetSameMonthLastYear returns job counts for the same month of last year, per keyword.
func (r *CompareRepository) GetSameMonthLastYear(ctx context.Context, keywords []string) (map[string]int, error) {
	session := r.DB.Driver.NewSession(ctx, neo4j.SessionConfig{
		AccessMode:   neo4j.AccessModeRead,
		DatabaseName: r.DB.Database,
	})
	defer session.Close(ctx)

	query := `
		UNWIND $keywords AS kw
		MATCH (j:Job)
		WHERE j.title IS NOT NULL
		  AND j.posted_date IS NOT NULL
		  AND date(datetime(j.posted_date)).year  = date().year - 1
		  AND date(datetime(j.posted_date)).month = date().month
		  AND toLower(j.title) CONTAINS toLower(kw)
		RETURN kw AS keyword, count(j) AS job_count
	`

	result, err := session.Run(ctx, query, map[string]interface{}{
		"keywords": keywords,
	})
	if err != nil {
		return nil, fmt.Errorf("neo4j query compare yoy: %w", err)
	}

	out := make(map[string]int)
	for result.Next(ctx) {
		rec := result.Record()
		kw := toString(rec.Values[0])
		c := toInt(rec.Values[1])
		out[kw] = c
	}
	if err := result.Err(); err != nil {
		return nil, fmt.Errorf("neo4j result compare yoy: %w", err)
	}

	return out, nil
}
