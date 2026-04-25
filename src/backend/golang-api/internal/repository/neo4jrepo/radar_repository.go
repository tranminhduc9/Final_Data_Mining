package neo4jrepo

import (
	"context"
	"fmt"

	"github.com/neo4j/neo4j-go-driver/v5/neo4j"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/database"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/domain"
)

// classifyIndustry là biểu thức CASE Cypher phân loại job title thành nhóm ngành.
// Đặt ra ngoài để dễ maintain và tái sử dụng ở các query khác.
const classifyIndustry = `
  CASE
    WHEN toLower(j.title) CONTAINS 'kinh doanh'
      OR toLower(j.title) CONTAINS 'sales'
      OR toLower(j.title) CONTAINS 'telesales'
      OR toLower(j.title) CONTAINS 'tư vấn'
      OR toLower(j.title) CONTAINS 'presale'
      OR toLower(j.title) CONTAINS 'business development'
    THEN 'Kinh doanh phần mềm'

    WHEN toLower(j.title) CONTAINS 'ai'
      OR toLower(j.title) CONTAINS 'data'
      OR toLower(j.title) CONTAINS 'dữ liệu'
      OR toLower(j.title) CONTAINS 'machine learning'
      OR toLower(j.title) CONTAINS 'trí tuệ nhân tạo'
      OR toLower(j.title) CONTAINS 'khoa học dữ liệu'
    THEN 'AI & Data'

    WHEN toLower(j.title) CONTAINS 'developer'
      OR toLower(j.title) CONTAINS 'lập trình'
      OR toLower(j.title) CONTAINS 'engineer'
      OR toLower(j.title) CONTAINS 'kỹ sư'
      OR toLower(j.title) CONTAINS 'backend'
      OR toLower(j.title) CONTAINS 'frontend'
      OR toLower(j.title) CONTAINS 'fullstack'
      OR toLower(j.title) CONTAINS 'java'
      OR toLower(j.title) CONTAINS 'python'
      OR toLower(j.title) CONTAINS 'swe'
    THEN 'Phát triển phần mềm'

    WHEN toLower(j.title) CONTAINS 'ceo'
      OR toLower(j.title) CONTAINS 'cfo'
      OR toLower(j.title) CONTAINS 'cio'
      OR toLower(j.title) CONTAINS 'coo'
      OR toLower(j.title) CONTAINS 'cto'
      OR toLower(j.title) CONTAINS 'cpo'
      OR toLower(j.title) CONTAINS 'giám đốc'
      OR toLower(j.title) CONTAINS 'director'
      OR toLower(j.title) CONTAINS 'manager'
      OR toLower(j.title) CONTAINS 'trưởng phòng'
      OR toLower(j.title) CONTAINS 'trưởng nhóm'
      OR toLower(j.title) CONTAINS 'quản lý'
      OR toLower(j.title) CONTAINS 'phó'
      OR toLower(j.title) CONTAINS 'lead'
      OR toLower(j.title) CONTAINS 'tổng'
    THEN 'Quản lý & Lãnh đạo'

    ELSE 'Khác'
  END
`

type RadarRepository struct {
	DB *database.Neo4jDB
}

func NewRadarRepository(db *database.Neo4jDB) *RadarRepository {
	return &RadarRepository{DB: db}
}

func (r *RadarRepository) GetTop4Industries(ctx context.Context) ([]domain.RadarTrend, error) {
	session := r.DB.Driver.NewSession(ctx, neo4j.SessionConfig{
		AccessMode:   neo4j.AccessModeRead,
		DatabaseName: r.DB.Database,
	})
	defer session.Close(ctx)

	query := fmt.Sprintf(`
		MATCH (j:Job)
		WHERE j.title IS NOT NULL AND j.posted_date IS NOT NULL
		WITH j, (%s) AS industry_group
		WITH industry_group,
		  count(j) AS total_jobs,
		  count(
		    CASE WHEN datetime(j.posted_date) < datetime({year: date().year, month: date().month, day: 1})
		    THEN 1 END
		  ) AS jobs_before_this_month
		WHERE industry_group <> 'Khác'
		RETURN industry_group AS industry,
		       total_jobs     AS job_count,
		       jobs_before_this_month
		ORDER BY total_jobs DESC
		LIMIT 4
	`, classifyIndustry)

	result, err := session.Run(ctx, query, nil)
	if err != nil {
		return nil, fmt.Errorf("neo4j query top4: %w", err)
	}

	var trends []domain.RadarTrend
	for result.Next(ctx) {
		rec := result.Record()

		industry, _ := rec.Get("industry")
		jobCount, _ := rec.Get("job_count")
		jobsBefore, _ := rec.Get("jobs_before_this_month")

		total := toInt(jobCount)
		before := toInt(jobsBefore)

		var growthRate *float64
		if before > 0 {
			g := float64(total-before) / float64(before) * 100
			growthRate = &g
		}

		trends = append(trends, domain.RadarTrend{
			Industry:        toString(industry),
			JobCount:        total,
			JobsToLastMonth: before,
			GrowthRate:      growthRate,
		})
	}

	if err := result.Err(); err != nil {
		return nil, fmt.Errorf("neo4j result top4: %w", err)
	}

	return trends, nil
}

func toInt(v interface{}) int {
	if i, ok := v.(int64); ok {
		return int(i)
	}
	return 0
}

func toString(v interface{}) string {
	if s, ok := v.(string); ok {
		return s
	}
	return ""
}
