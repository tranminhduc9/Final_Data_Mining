package neo4jrepo

import (
	"context"
	"fmt"
	"time"

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
		  ) AS jobs_before_this_month,
		  count(
		    CASE WHEN datetime(j.posted_date) >= datetime({year: date().year, month: date().month, day: 1})
		    THEN 1 END
		  ) AS jobs_this_month,
		  count(
		    CASE WHEN datetime(j.posted_date) >= datetime({year: date().year, month: date().month, day: 1}) - duration({months: 1})
		      AND datetime(j.posted_date) < datetime({year: date().year, month: date().month, day: 1})
		    THEN 1 END
		  ) AS jobs_last_month
		WHERE industry_group <> 'Khác'
		RETURN industry_group AS industry,
		       total_jobs            AS job_count,
		       jobs_before_this_month,
		       jobs_this_month,
		       jobs_last_month
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
		jobsThis, _ := rec.Get("jobs_this_month")
		jobsLast, _ := rec.Get("jobs_last_month")

		total := toInt(jobCount)
		before := toInt(jobsBefore)
		thisMonth := toInt(jobsThis)
		lastMonth := toInt(jobsLast)

		var growthRate *float64
		if before > 0 {
			g := float64(total-before) / float64(before) * 100
			growthRate = &g
		}

		var momRate *float64
		if lastMonth > 0 {
			m := float64(thisMonth-lastMonth) / float64(lastMonth) * 100
			momRate = &m
		}

		trends = append(trends, domain.RadarTrend{
			Industry:        toString(industry),
			JobCount:        total,
			JobsToLastMonth: before,
			GrowthRate:      growthRate,
			JobsThisMonth:   thisMonth,
			JobsLastMonth:   lastMonth,
			MoMRate:         momRate,
		})
	}

	if err := result.Err(); err != nil {
		return nil, fmt.Errorf("neo4j result top4: %w", err)
	}

	return trends, nil
}

func (r *RadarRepository) GetTop10Keywords(ctx context.Context) ([]domain.RadarKeywordCount, error) {
	session := r.DB.Driver.NewSession(ctx, neo4j.SessionConfig{
		AccessMode:   neo4j.AccessModeRead,
		DatabaseName: r.DB.Database,
	})
	defer session.Close(ctx)

	query := `
		MATCH (t:Technology)<-[:REQUIRES]-(j:Job)
		WHERE t.name IS NOT NULL
		RETURN t.name AS keyword, count(j) AS job_count
		ORDER BY job_count DESC
		LIMIT 10
	`

	result, err := session.Run(ctx, query, nil)
	if err != nil {
		return nil, fmt.Errorf("neo4j query top10: %w", err)
	}

	var counts []domain.RadarKeywordCount
	for result.Next(ctx) {
		rec := result.Record()
		keyword, _ := rec.Get("keyword")
		jobCount, _ := rec.Get("job_count")
		counts = append(counts, domain.RadarKeywordCount{
			Keyword:  toString(keyword),
			JobCount: toInt(jobCount),
		})
	}

	if err := result.Err(); err != nil {
		return nil, fmt.Errorf("neo4j result top10: %w", err)
	}

	return counts, nil
}

func (r *RadarRepository) SearchByKeywords(ctx context.Context, keywords []string, months int) ([]domain.RadarSearchPoint, error) {
	session := r.DB.Driver.NewSession(ctx, neo4j.SessionConfig{
		AccessMode:   neo4j.AccessModeRead,
		DatabaseName: r.DB.Database,
	})
	defer session.Close(ctx)

	cutoff := time.Now().AddDate(0, -months, 0).Format("2006-01-02")

	query := `
		UNWIND $keywords AS kw
		MATCH (j:Job)
		WHERE j.title IS NOT NULL
		  AND j.posted_date IS NOT NULL
		  AND datetime(j.posted_date) >= datetime($cutoff)
		  AND toLower(j.title) CONTAINS toLower(kw)
		WITH kw,
		     date(datetime(j.posted_date)).year  AS year,
		     date(datetime(j.posted_date)).month AS month,
		     j
		RETURN year, month, kw AS keyword, count(j) AS job_count
		ORDER BY year, month, keyword
	`

	result, err := session.Run(ctx, query, map[string]interface{}{
		"keywords": keywords,
		"cutoff":   cutoff,
	})
	if err != nil {
		return nil, fmt.Errorf("neo4j query search: %w", err)
	}

	type monthKey struct{ year, month int }
	pointMap := map[monthKey]*domain.RadarSearchPoint{}
	var order []monthKey

	for result.Next(ctx) {
		rec := result.Record()

		yearVal, _ := rec.Get("year")
		monthVal, _ := rec.Get("month")
		keywordVal, _ := rec.Get("keyword")
		countVal, _ := rec.Get("job_count")

		y := toInt(yearVal)
		m := toInt(monthVal)
		k := toString(keywordVal)
		c := toInt(countVal)

		key := monthKey{y, m}
		if _, ok := pointMap[key]; !ok {
			pointMap[key] = &domain.RadarSearchPoint{
				Year:     y,
				Month:    m,
				Keywords: make(map[string]int),
			}
			order = append(order, key)
		}
		pointMap[key].Keywords[k] = c
	}

	if err := result.Err(); err != nil {
		return nil, fmt.Errorf("neo4j result search: %w", err)
	}

	points := make([]domain.RadarSearchPoint, 0, len(order))
	for _, key := range order {
		points = append(points, *pointMap[key])
	}
	return points, nil
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
