package handler

import (
	"net/http"
	"strconv"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/service"
)

type RadarHandler struct {
	radarService *service.RadarService
}

func NewRadarHandler(radarService *service.RadarService) *RadarHandler {
	return &RadarHandler{radarService: radarService}
}

func (h *RadarHandler) Index(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{"message": "radar page endpoint not implemented yet"})
}

// Top4 godoc
// @Summary      Top 4 technologies by job count with growth metrics
// @Tags         radar
// @Produce      json
// @Success      200 {object} dto.Top4Response
// @Failure      503 {object} dto.ErrorResponse
// @Router       /radar/top4 [get]
func (h *RadarHandler) Top4(c *gin.Context) {
	trends, err := h.radarService.GetTop4(c.Request.Context())
	if err != nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"message": "failed to fetch top4: " + err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"data": trends})
}

// Search godoc
// @Summary      Monthly job counts per keyword over a time window
// @Tags         radar
// @Produce      json
// @Param        keywords  query  []string  true   "Keywords (repeat or comma-separated)"  collectionFormat(multi)
// @Param        months    query  int       false  "Time window in months: 3, 6, 12, 24 (default 6)"
// @Success      200 {object} dto.RadarSearchResponse
// @Failure      400 {object} dto.ErrorResponse
// @Failure      503 {object} dto.ErrorResponse
// @Router       /radar/search [get]
func (h *RadarHandler) Search(c *gin.Context) {
	// Collect keywords — supports repeated params and comma-separated values
	var keywords []string
	seen := map[string]bool{}
	for _, raw := range c.QueryArray("keywords") {
		for _, kw := range strings.Split(raw, ",") {
			kw = strings.TrimSpace(kw)
			if kw != "" && !seen[kw] {
				seen[kw] = true
				keywords = append(keywords, kw)
			}
		}
	}
	if len(keywords) == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"message": "keywords is required"})
		return
	}

	monthsStr := c.DefaultQuery("months", "6")
	months, err := strconv.Atoi(monthsStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"message": "months must be an integer"})
		return
	}
	validMonths := map[int]bool{3: true, 6: true, 12: true, 24: true}
	if !validMonths[months] {
		c.JSON(http.StatusBadRequest, gin.H{"message": "months must be one of: 3, 6, 12, 24"})
		return
	}

	results, err := h.radarService.Search(c.Request.Context(), keywords, months)
	if err != nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"message": "failed to search: " + err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"data": results})
}

func (h *RadarHandler) ExportPNG(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{"message": "radar export png endpoint not implemented yet"})
}

func (h *RadarHandler) ExportCSV(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{"message": "radar export csv endpoint not implemented yet"})
}

// Top10 godoc
// @Summary      Top 10 technologies by total job count
// @Tags         radar
// @Produce      json
// @Success      200 {object} dto.Top10Response
// @Failure      503 {object} dto.ErrorResponse
// @Router       /radar/top10 [get]
func (h *RadarHandler) Top10(c *gin.Context) {
	counts, err := h.radarService.GetTop10(c.Request.Context())
	if err != nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"message": "failed to fetch top10: " + err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"data": counts})
}
