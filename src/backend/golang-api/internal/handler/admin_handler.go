package handler

import (
	"errors"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/dto"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/repository/postgres"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/service"
	"golang.org/x/crypto/bcrypt"
)

type AdminHandler struct {
	analyticsService *service.AnalyticsService
	userRepo         *postgres.UserRepository
}

func NewAdminHandler(analyticsService *service.AnalyticsService, userRepo *postgres.UserRepository) *AdminHandler {
	return &AdminHandler{analyticsService: analyticsService, userRepo: userRepo}
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

// ListUsers godoc
// @Summary      List all users (admins first)
// @Tags         admin
// @Security     BearerAuth
// @Produce      json
// @Success      200 {object} dto.ListUsersResponse
// @Failure      401 {object} dto.ErrorResponse
// @Failure      403 {object} dto.ErrorResponse
// @Router       /admin/users [get]
func (h *AdminHandler) ListUsers(c *gin.Context) {
	if h.userRepo == nil {
		c.JSON(http.StatusOK, dto.ListUsersResponse{Data: []dto.UserItem{}})
		return
	}
	users, err := h.userRepo.ListAll(c.Request.Context())
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"message": err.Error()})
		return
	}
	items := make([]dto.UserItem, len(users))
	for i, u := range users {
		items[i] = dto.UserItem{
			ID:       u.ID,
			FullName: u.FullName,
			Email:    u.Email,
			Role:     u.Role,
			Status:   u.Status,
		}
	}
	c.JSON(http.StatusOK, dto.ListUsersResponse{Data: items})
}

// InsertUser godoc
// @Summary      Create a new user account
// @Tags         admin
// @Security     BearerAuth
// @Accept       json
// @Produce      json
// @Param        body body dto.InsertUserRequest true "New user payload"
// @Success      201 {object} dto.UserItem
// @Failure      400 {object} dto.ErrorResponse
// @Failure      401 {object} dto.ErrorResponse
// @Failure      403 {object} dto.ErrorResponse
// @Failure      409 {object} dto.ErrorResponse
// @Router       /admin/users [post]
func (h *AdminHandler) InsertUser(c *gin.Context) {
	var req dto.InsertUserRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"message": err.Error()})
		return
	}
	if h.userRepo == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"message": "database unavailable"})
		return
	}
	hash, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"message": "failed to hash password"})
		return
	}
	user, err := h.userRepo.CreateFull(c.Request.Context(), req.Email, string(hash), req.FullName, req.Role, req.Status)
	if err != nil {
		if errors.Is(err, postgres.ErrEmailTaken) {
			c.JSON(http.StatusConflict, gin.H{"message": "email already registered"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"message": err.Error()})
		return
	}
	c.JSON(http.StatusCreated, dto.UserItem{
		ID:       user.ID,
		FullName: user.FullName,
		Email:    user.Email,
		Role:     user.Role,
		Status:   user.Status,
	})
}

// AlterUser godoc
// @Summary      Update a user's information
// @Tags         admin
// @Security     BearerAuth
// @Accept       json
// @Produce      json
// @Param        id   path string              true "User ID"
// @Param        body body dto.AlterUserRequest true "Updated user data"
// @Success      200 {object} dto.UserItem
// @Failure      400 {object} dto.ErrorResponse
// @Failure      401 {object} dto.ErrorResponse
// @Failure      403 {object} dto.ErrorResponse
// @Failure      404 {object} dto.ErrorResponse
// @Failure      409 {object} dto.ErrorResponse
// @Router       /admin/users/{id} [put]
func (h *AdminHandler) AlterUser(c *gin.Context) {
	id := c.Param("id")
	var req dto.AlterUserRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"message": err.Error()})
		return
	}
	if h.userRepo == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"message": "database unavailable"})
		return
	}
	user, err := h.userRepo.UpdateUser(c.Request.Context(), id, req.FullName, req.Email, req.Role, req.Status)
	if err != nil {
		if errors.Is(err, postgres.ErrNotFound) {
			c.JSON(http.StatusNotFound, gin.H{"message": "user not found"})
			return
		}
		if errors.Is(err, postgres.ErrEmailTaken) {
			c.JSON(http.StatusConflict, gin.H{"message": "email already registered"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"message": err.Error()})
		return
	}
	c.JSON(http.StatusOK, dto.UserItem{
		ID:       user.ID,
		FullName: user.FullName,
		Email:    user.Email,
		Role:     user.Role,
		Status:   user.Status,
	})
}

// DeleteUser godoc
// @Summary      Delete a user account
// @Tags         admin
// @Security     BearerAuth
// @Produce      json
// @Param        id path string true "User ID"
// @Success      200 {object} map[string]string
// @Failure      401 {object} dto.ErrorResponse
// @Failure      403 {object} dto.ErrorResponse
// @Failure      404 {object} dto.ErrorResponse
// @Router       /admin/users/{id} [delete]
func (h *AdminHandler) DeleteUser(c *gin.Context) {
	id := c.Param("id")
	if h.userRepo == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"message": "database unavailable"})
		return
	}
	if err := h.userRepo.DeleteByID(c.Request.Context(), id); err != nil {
		if errors.Is(err, postgres.ErrNotFound) {
			c.JSON(http.StatusNotFound, gin.H{"message": "user not found"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"message": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"message": "user deleted"})
}
