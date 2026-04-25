package service

import (
	"context"
	"fmt"

	"github.com/techpulsevn/final-data-mining/golang-api/internal/domain"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/repository/neo4jrepo"
)

type RadarService struct {
	radarRepo *neo4jrepo.RadarRepository
}

func NewRadarService(radarRepo *neo4jrepo.RadarRepository) *RadarService {
	return &RadarService{radarRepo: radarRepo}
}

func (s *RadarService) GetTop4(ctx context.Context) ([]domain.RadarTrend, error) {
	if s.radarRepo == nil {
		return nil, fmt.Errorf("neo4j unavailable")
	}
	return s.radarRepo.GetTop4Industries(ctx)
}
