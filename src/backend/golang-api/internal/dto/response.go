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

type RoadAnalysisResponse struct {
	Data domain.RoadAnalysisResult `json:"data"`
}

// --- Admin ---

type CountResponse struct {
	Data int `json:"data"`
}

type MonthlyVisitsResponse struct {
	Data []domain.MonthlyVisit `json:"data"`
}

type TopKeywordsResponse struct {
	Data []domain.KeywordCount `json:"data"`
}

type UserItem struct {
	FullName string `json:"full_name"`
	Email    string `json:"email"`
	Role     string `json:"role"`
	Status   string `json:"status"`
}

type ListUsersResponse struct {
	Data []UserItem `json:"data"`
}

// --- Generic error ---

type ErrorResponse struct {
	Message string `json:"message"`
}
