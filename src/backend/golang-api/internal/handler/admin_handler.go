package handler

import (
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/service"
)

type AdminHandler struct {
	analyticsService *service.AnalyticsService
}

func NewAdminHandler(analyticsService *service.AnalyticsService) *AdminHandler {
	return &AdminHandler{analyticsService: analyticsService}
}

// Stats godoc
// @Summary      Get admin dashboard stats
// @Description  Returns total users, unique visits today, and search count today
// @Tags         admin
// @Security     BearerAuth
// @Produce      json
// @Success      200 {object} dto.AdminStatsResponse
// @Failure      401 {object} dto.ErrorResponse
// @Failure      403 {object} dto.ErrorResponse
// @Router       /admin/stats [get]
func (h *AdminHandler) Stats(c *gin.Context) {
	stats, err := h.analyticsService.GetStats(c.Request.Context())
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"message": "failed to fetch stats: " + err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"data": stats})
}

// TopKeywords godoc
// @Summary      Get top searched keywords (all time)
// @Tags         admin
// @Security     BearerAuth
// @Produce      json
// @Param        limit  query  int  false  "Number of results (default 10, max 100)"
// @Success      200 {object} dto.TopKeywordsResponse
// @Failure      401 {object} dto.ErrorResponse
// @Failure      403 {object} dto.ErrorResponse
// @Router       /admin/top-keywords [get]
func (h *AdminHandler) TopKeywords(c *gin.Context) {
	limit, err := strconv.Atoi(c.DefaultQuery("limit", "10"))
	if err != nil || limit <= 0 || limit > 100 {
		limit = 10
	}

	keywords, err := h.analyticsService.GetTopKeywords(c.Request.Context(), limit)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"message": "failed to fetch top keywords: " + err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"data": keywords})
}
