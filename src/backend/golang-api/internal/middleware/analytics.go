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
		if kw := c.Query("keyword"); kw != "" {
			go svc.RecordSearch(context.Background(), kw, "radar")
		}
	case "/api/v1/compare/search":
		if kw := c.Query("keyword"); kw != "" {
			go svc.RecordSearch(context.Background(), kw, "compare")
		}
	case "/api/v1/graph/explore":
		if kws := c.QueryArray("keywords"); len(kws) > 0 && kws[0] != "" {
			go svc.RecordSearch(context.Background(), kws[0], "graph_explore")
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
