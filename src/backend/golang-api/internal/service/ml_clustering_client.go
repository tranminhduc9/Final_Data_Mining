package service

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"time"

	"github.com/techpulsevn/final-data-mining/golang-api/internal/domain"
)

type MLClusteringClient struct {
	BaseURL    string
	HTTPClient *http.Client
}

func NewMLClusteringClient(baseURL string) *MLClusteringClient {
	return &MLClusteringClient{
		BaseURL:    strings.TrimRight(baseURL, "/"),
		HTTPClient: &http.Client{Timeout: 60 * time.Second},
	}
}

type UpstreamError struct {
	StatusCode int
	Body       string
	Path       string
}

func (e *UpstreamError) Error() string {
	return fmt.Sprintf("ml-clustering %s %d: %s", e.Path, e.StatusCode, e.Body)
}

func (c *MLClusteringClient) doJSON(ctx context.Context, method, path string, body any, out any) error {
	var reader io.Reader
	if body != nil {
		buf, err := json.Marshal(body)
		if err != nil {
			return err
		}
		reader = bytes.NewReader(buf)
	}
	req, err := http.NewRequestWithContext(ctx, method, c.BaseURL+path, reader)
	if err != nil {
		return err
	}
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 300 {
		raw, _ := io.ReadAll(resp.Body)
		return &UpstreamError{StatusCode: resp.StatusCode, Body: string(raw), Path: path}
	}
	if out == nil {
		return nil
	}
	return json.NewDecoder(resp.Body).Decode(out)
}

func (c *MLClusteringClient) ListClusters(ctx context.Context, isCoherent *bool) ([]domain.ClusterSummary, error) {
	path := "/clusters"
	if isCoherent != nil {
		path += "?is_coherent=" + strconv.FormatBool(*isCoherent)
	}
	var out []domain.ClusterSummary
	if err := c.doJSON(ctx, http.MethodGet, path, nil, &out); err != nil {
		return nil, err
	}
	return out, nil
}

func (c *MLClusteringClient) GetCluster(ctx context.Context, clusterID int) (*domain.ClusterDetail, error) {
	path := "/clusters/" + strconv.Itoa(clusterID)
	var out domain.ClusterDetail
	if err := c.doJSON(ctx, http.MethodGet, path, nil, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

func (c *MLClusteringClient) GetTechCluster(ctx context.Context, techName string) (*domain.TechClusterResult, error) {
	path := "/tech/" + url.PathEscape(techName) + "/cluster"
	var out domain.TechClusterResult
	if err := c.doJSON(ctx, http.MethodGet, path, nil, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

func (c *MLClusteringClient) PredictBatch(ctx context.Context, req domain.BatchPredictRequest) (*domain.BatchPredictResponse, error) {
	var out domain.BatchPredictResponse
	if err := c.doJSON(ctx, http.MethodPost, "/predict/batch", req, &out); err != nil {
		return nil, err
	}
	return &out, nil
}
