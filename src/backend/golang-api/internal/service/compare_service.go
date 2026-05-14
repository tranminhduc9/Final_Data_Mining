package service

import (
	"context"
	"fmt"
	"time"

	"github.com/techpulsevn/final-data-mining/golang-api/internal/domain"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/repository/neo4jrepo"
)

type CompareService struct {
	compareRepo *neo4jrepo.CompareRepository
}

func NewCompareService(compareRepo *neo4jrepo.CompareRepository) *CompareService {
	return &CompareService{compareRepo: compareRepo}
}

func (s *CompareService) Compare(ctx context.Context, keywords []string, months int) ([]domain.CompareResult, error) {
	if s.compareRepo == nil {
		return nil, fmt.Errorf("neo4j unavailable")
	}

	now := time.Now()
	windowStart := time.Date(now.Year(), now.Month(), 1, 0, 0, 0, 0, time.UTC).AddDate(0, -months, 0)

	monthly, err := s.compareRepo.GetMonthlyByKeywords(ctx, keywords, windowStart)
	if err != nil {
		return nil, err
	}
	yoyMap, err := s.compareRepo.GetSameMonthLastYear(ctx, keywords)
	if err != nil {
		return nil, err
	}

	thisYear := now.Year()
	thisMonth := int(now.Month())
	lastMonthTime := now.AddDate(0, -1, 0)
	lastYear := lastMonthTime.Year()
	lastMonth := int(lastMonthTime.Month())

	// Build full month spine for the window (filled with zeros)
	type monthKey struct{ y, m int }
	var spine []monthKey
	cur := windowStart
	for !cur.After(now) {
		spine = append(spine, monthKey{cur.Year(), int(cur.Month())})
		cur = cur.AddDate(0, 1, 0)
	}

	results := make([]domain.CompareResult, 0, len(keywords))
	for _, kw := range keywords {
		// Index actual counts by (year, month)
		countMap := make(map[monthKey]int)
		for _, mc := range monthly[kw] {
			countMap[monthKey{mc.Year, mc.Month}] = mc.JobCount
		}

		// Fill complete monthly series
		filled := make([]domain.CompareMonthlyCount, 0, len(spine))
		totalJobs := 0
		jobsExcludingThisMonth := 0
		thisMonthCount := 0
		lastMonthCount := 0
		for _, mk := range spine {
			c := countMap[mk]
			filled = append(filled, domain.CompareMonthlyCount{Year: mk.y, Month: mk.m, JobCount: c})
			totalJobs += c
			if mk.y == thisYear && mk.m == thisMonth {
				thisMonthCount = c
			} else {
				jobsExcludingThisMonth += c
				if mk.y == lastYear && mk.m == lastMonth {
					lastMonthCount = c
				}
			}
		}

		var growthRate *float64
		if jobsExcludingThisMonth > 0 {
			g := float64(thisMonthCount) / float64(jobsExcludingThisMonth) * 100
			growthRate = &g
		}

		var momRate *float64
		if lastMonthCount > 0 {
			m := float64(thisMonthCount-lastMonthCount) / float64(lastMonthCount) * 100
			momRate = &m
		}

		var yoyRate *float64
		if sameLastYear := yoyMap[kw]; sameLastYear > 0 {
			y := float64(thisMonthCount-sameLastYear) / float64(sameLastYear) * 100
			yoyRate = &y
		}

		results = append(results, domain.CompareResult{
			Keyword:    kw,
			JobCount:   totalJobs,
			GrowthRate: growthRate,
			MoMRate:    momRate,
			YoYRate:    yoyRate,
			Monthly:    filled,
		})
	}

	return results, nil
}
