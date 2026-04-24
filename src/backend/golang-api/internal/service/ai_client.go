package service

import (
	"net/http"
	"time"
)

type AIClient struct {
	BaseURL    string
	HTTPClient *http.Client
}

func NewAIClient(baseURL string) *AIClient {
	return &AIClient{
		BaseURL: baseURL,
		HTTPClient: &http.Client{
			Timeout: 60 * time.Second,
		},
	}
}
