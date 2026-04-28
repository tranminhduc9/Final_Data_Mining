package handler

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/service"
)

type AdminHandler struct {
	analyticsService *service.AnalyticsService
}

func NewAdminHandler(analyticsService *service.AnalyticsService) *AdminHandler {
	return &AdminHandler{analyticsService: analyticsService}
}

// DashboardUserCount godoc
// @Summary      Total registered user accounts
// @Tags         admin
// @Security     BearerAuth
// @Produce      json
// @Success      200 {object} dto.CountResponse
// @Failure      401 {object} dto.ErrorResponse
// @Failure      403 {object} dto.ErrorResponse
// @Router       /admin/dashboard/user-count [get]
func (h *AdminHandler) DashboardUserCount(c *gin.Context) {
	count, err := h.analyticsService.GetUserCount(c.Request.Context())
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"message": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"data": count})
}

// DashboardVisitsToday godoc
// @Summary      Number of unique visitors today
// @Tags         admin
// @Security     BearerAuth
// @Produce      json
// @Success      200 {object} dto.CountResponse
// @Failure      401 {object} dto.ErrorResponse
// @Failure      403 {object} dto.ErrorResponse
// @Router       /admin/dashboard/visits-today [get]
func (h *AdminHandler) DashboardVisitsToday(c *gin.Context) {
	count, err := h.analyticsService.GetVisitsToday(c.Request.Context())
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"message": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"data": count})
}

// DashboardSearchesToday godoc
// @Summary      Number of searches performed today
// @Tags         admin
// @Security     BearerAuth
// @Produce      json
// @Success      200 {object} dto.CountResponse
// @Failure      401 {object} dto.ErrorResponse
// @Failure      403 {object} dto.ErrorResponse
// @Router       /admin/dashboard/searches-today [get]
func (h *AdminHandler) DashboardSearchesToday(c *gin.Context) {
	count, err := h.analyticsService.GetSearchesToday(c.Request.Context())
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"message": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"data": count})
}

// DashboardMonthlyVisits godoc
// @Summary      Unique visitor count per month for the last 4 months
// @Tags         admin
// @Security     BearerAuth
// @Produce      json
// @Success      200 {object} dto.MonthlyVisitsResponse
// @Failure      401 {object} dto.ErrorResponse
// @Failure      403 {object} dto.ErrorResponse
// @Router       /admin/dashboard/monthly-visits [get]
func (h *AdminHandler) DashboardMonthlyVisits(c *gin.Context) {
	visits, err := h.analyticsService.GetMonthlyVisits(c.Request.Context(), 4)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"message": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"data": visits})
}

// DashboardTopKeywords godoc
// @Summary      Top 4 most searched keywords of all time
// @Tags         admin
// @Security     BearerAuth
// @Produce      json
// @Success      200 {object} dto.TopKeywordsResponse
// @Failure      401 {object} dto.ErrorResponse
// @Failure      403 {object} dto.ErrorResponse
// @Router       /admin/dashboard/top-keywords [get]
func (h *AdminHandler) DashboardTopKeywords(c *gin.Context) {
	keywords, err := h.analyticsService.GetTopKeywords(c.Request.Context(), 4)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"message": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"data": keywords})
}
