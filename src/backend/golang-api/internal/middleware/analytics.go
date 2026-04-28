package middleware

import (
	"context"
	"net/http"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
)

type AnalyticsRecorder interface {
	RecordVisit(ctx context.Context, ip string, t time.Time)
	RecordSearch(ctx context.Context, keyword, endpoint string)
}

func Analytics(svc AnalyticsRecorder) gin.HandlerFunc {
	return func(c *gin.Context) {
		ip := c.ClientIP()

		c.Next()

		path := c.FullPath()
		if strings.HasPrefix(path, "/api/v1/admin") {
			return
		}

		now := time.Now()
		go svc.RecordVisit(context.Background(), ip, now)

		if c.Writer.Status() != http.StatusOK {
			return
		}

		trackSearchKeywords(c, path, svc)
	}
}

func trackSearchKeywords(c *gin.Context, path string, svc AnalyticsRecorder) {
	switch path {
	case "/api/v1/radar/search":
		for _, kw := range parseKeywords(c) {
			go svc.RecordSearch(context.Background(), kw, "radar")
		}
	case "/api/v1/compare/search":
		for _, kw := range parseKeywords(c) {
			go svc.RecordSearch(context.Background(), kw, "compare")
		}
	case "/api/v1/graph/explore":
		for _, kw := range parseKeywords(c) {
			go svc.RecordSearch(context.Background(), kw, "graph_explore")
		}
	case "/api/v1/graph/road_analysis":
		if from := c.Query("from"); from != "" {
			go svc.RecordSearch(context.Background(), from, "road_analysis")
		}
		if to := c.Query("to"); to != "" {
			go svc.RecordSearch(context.Background(), to, "road_analysis")
		}
	}
}

// parseKeywords mirrors the dedup logic used in radar/compare/graph handlers.
func parseKeywords(c *gin.Context) []string {
	seen := map[string]bool{}
	var result []string
	for _, raw := range c.QueryArray("keywords") {
		for _, kw := range strings.Split(raw, ",") {
			kw = strings.TrimSpace(kw)
			if kw != "" && !seen[kw] {
				seen[kw] = true
				result = append(result, kw)
			}
		}
	}
	return result
}
