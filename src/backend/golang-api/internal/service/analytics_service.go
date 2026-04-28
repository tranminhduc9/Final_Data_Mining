package service

import (
	"context"
	"time"

	"github.com/techpulsevn/final-data-mining/golang-api/internal/domain"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/repository/postgres"
)

type AnalyticsService struct {
	repo *postgres.AnalyticsRepository
}

func NewAnalyticsService(repo *postgres.AnalyticsRepository) *AnalyticsService {
	return &AnalyticsService{repo: repo}
}

func (s *AnalyticsService) RecordVisit(ctx context.Context, ip string, t time.Time) {
	if s.repo == nil {
		return
	}
	_ = s.repo.RecordVisit(ctx, ip, t)
}

func (s *AnalyticsService) RecordSearch(ctx context.Context, keyword, endpoint string) {
	if s.repo == nil {
		return
	}
	_ = s.repo.RecordSearch(ctx, keyword, endpoint)
}

func (s *AnalyticsService) GetStats(ctx context.Context) (*domain.AdminStats, error) {
	if s.repo == nil {
		return &domain.AdminStats{}, nil
	}
	return s.repo.GetStats(ctx)
}

func (s *AnalyticsService) GetTopKeywords(ctx context.Context, limit int) ([]domain.KeywordCount, error) {
	if s.repo == nil {
		return []domain.KeywordCount{}, nil
	}
	return s.repo.GetTopKeywords(ctx, limit)
}
