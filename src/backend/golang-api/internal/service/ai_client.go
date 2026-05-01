package service

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"
)

type AIClient struct {
	BaseURL    string
	HTTPClient *http.Client // dùng cho non-stream (timeout 60s)
	StreamHTTP *http.Client // dùng cho SSE (no timeout)
}

func NewAIClient(baseURL string) *AIClient {
	return &AIClient{
		BaseURL: strings.TrimRight(baseURL, "/"),
		HTTPClient: &http.Client{
			Timeout: 60 * time.Second,
		},
		StreamHTTP: &http.Client{}, // no timeout cho SSE
	}
}

// ── DTOs mirror schema FastAPI (app/api/schemas.py) ────────────────────────────

type ChatRequest struct {
	Query     string  `json:"query"`
	SessionID *string `json:"session_id,omitempty"`
	UserID    *string `json:"user_id,omitempty"`
}

type SourceItem struct {
	Title         *string  `json:"title"`
	PublishedDate *string  `json:"published_date"`
	Source        *string  `json:"source"`
	RerankScore   *float64 `json:"rerank_score"`
}

type ChatResponse struct {
	Answer    string       `json:"answer"`
	SessionID string       `json:"session_id"`
	Sources   []SourceItem `json:"sources"`
	Entities  []string     `json:"entities"`
	JobTitles []string     `json:"job_titles"`
	Query     string       `json:"query"`
}

type ChatMessageItem struct {
	ID      int    `json:"id"`
	Role    string `json:"role"`
	Content string `json:"content"`
}

type HealthResponse struct {
	Status  string `json:"status"`
	Neo4j   bool   `json:"neo4j"`
	Version string `json:"version"`
}

// ── Methods ────────────────────────────────────────────────────────────────────

func (c *AIClient) Health(ctx context.Context) (*HealthResponse, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, c.BaseURL+"/health", nil)
	if err != nil {
		return nil, err
	}
	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 300 {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("rag /health %d: %s", resp.StatusCode, body)
	}
	var out HealthResponse
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return nil, err
	}
	return &out, nil
}

func (c *AIClient) Chat(ctx context.Context, body ChatRequest) (*ChatResponse, error) {
	buf, err := json.Marshal(body)
	if err != nil {
		return nil, err
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.BaseURL+"/chat", bytes.NewReader(buf))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 300 {
		raw, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("rag /chat %d: %s", resp.StatusCode, raw)
	}
	var out ChatResponse
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return nil, err
	}
	return &out, nil
}

func (c *AIClient) ListMessages(ctx context.Context, sessionID string) ([]ChatMessageItem, error) {
	url := c.BaseURL + "/chat/session/" + sessionID + "/messages"
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, err
	}
	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 300 {
		raw, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("rag list messages %d: %s", resp.StatusCode, raw)
	}
	var out []ChatMessageItem
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return nil, err
	}
	return out, nil
}

// ChatStream proxy SSE: gọi POST /chat/stream rồi forward từng SSE frame
// (event:/data:/blank-line) ra writer. flusher.Flush() được gọi sau mỗi frame.
func (c *AIClient) ChatStream(
	ctx context.Context,
	body ChatRequest,
	w io.Writer,
	flusher http.Flusher,
) error {
	buf, err := json.Marshal(body)
	if err != nil {
		return err
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.BaseURL+"/chat/stream", bytes.NewReader(buf))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "text/event-stream")
	req.Header.Set("Cache-Control", "no-cache")

	resp, err := c.StreamHTTP.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 300 {
		raw, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("rag /chat/stream %d: %s", resp.StatusCode, raw)
	}

	scanner := bufio.NewScanner(resp.Body)
	scanner.Buffer(make([]byte, 64*1024), 1024*1024)

	for scanner.Scan() {
		if err := ctx.Err(); err != nil {
			return nil // client disconnected
		}
		line := scanner.Text()
		if _, err := io.WriteString(w, line+"\n"); err != nil {
			return err
		}
		if line == "" && flusher != nil {
			flusher.Flush() // flush sau mỗi blank line (kết thúc 1 SSE frame)
		}
	}
	if err := scanner.Err(); err != nil && ctx.Err() == nil {
		return err
	}
	return nil
}
