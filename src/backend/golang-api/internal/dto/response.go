package dto

import "github.com/techpulsevn/final-data-mining/golang-api/internal/domain"

// --- Radar ---

type Top4Response struct {
	Data []domain.RadarTrend `json:"data"`
}

type RadarSearchResponse struct {
	Data []domain.RadarSearchPoint `json:"data"`
}

type Top10Response struct {
	Data []domain.RadarKeywordCount `json:"data"`
}

// --- Compare ---

type CompareSearchResponse struct {
	Data []domain.CompareResult `json:"data"`
}

// --- Graph ---

type GraphExploreResponse struct {
	Data domain.GraphResult `json:"data"`
}

// --- Generic error ---

type ErrorResponse struct {
	Message string `json:"message"`
}
