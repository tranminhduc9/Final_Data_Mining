package handler

import (
	"errors"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/dto"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/middleware"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/repository/postgres"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/service"
)

type AuthHandler struct {
	authService *service.AuthService
}

func NewAuthHandler(authService *service.AuthService) *AuthHandler {
	return &AuthHandler{authService: authService}
}

// Register godoc
// @Summary      Register a new user
// @Tags         auth
// @Accept       json
// @Produce      json
// @Param        body body dto.RegisterRequest true "Register payload"
// @Success      201 {object} dto.AuthResponse
// @Failure      400 {object} dto.ErrorResponse
// @Failure      409 {object} dto.ErrorResponse
// @Router       /auth/register [post]
func (h *AuthHandler) Register(c *gin.Context) {
	var req dto.RegisterRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"message": err.Error()})
		return
	}

	resp, err := h.authService.Register(c.Request.Context(), req.Email, req.Password, req.FullName)
	if err != nil {
		if errors.Is(err, service.ErrDatabaseUnavailable) {
			c.JSON(http.StatusServiceUnavailable, gin.H{"message": "database unavailable"})
			return
		}
		if errors.Is(err, postgres.ErrEmailTaken) {
			c.JSON(http.StatusConflict, gin.H{"message": "email already registered"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"message": "registration failed"})
		return
	}

	c.JSON(http.StatusCreated, resp)
}

// Login godoc
// @Summary      Login with email and password
// @Tags         auth
// @Accept       json
// @Produce      json
// @Param        body body dto.LoginRequest true "Login payload"
// @Success      200 {object} dto.AuthResponse
// @Failure      400 {object} dto.ErrorResponse
// @Failure      401 {object} dto.ErrorResponse
// @Router       /auth/login [post]
func (h *AuthHandler) Login(c *gin.Context) {
	var req dto.LoginRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"message": err.Error()})
		return
	}

	resp, err := h.authService.Login(c.Request.Context(), req.Email, req.Password)
	if err != nil {
		if errors.Is(err, service.ErrDatabaseUnavailable) {
			c.JSON(http.StatusServiceUnavailable, gin.H{"message": "database unavailable"})
			return
		}
		if errors.Is(err, service.ErrInvalidCredentials) {
			c.JSON(http.StatusUnauthorized, gin.H{"message": "invalid email or password"})
			return
		}
		if errors.Is(err, service.ErrAccountBlocked) {
			c.JSON(http.StatusForbidden, gin.H{"message": "account is blocked"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"message": "login failed"})
		return
	}

	c.JSON(http.StatusOK, resp)
}

// Refresh godoc
// @Summary      Refresh access token
// @Tags         auth
// @Accept       json
// @Produce      json
// @Param        body body dto.RefreshTokenRequest true "Refresh token payload"
// @Success      200 {object} dto.AuthResponse
// @Failure      400 {object} dto.ErrorResponse
// @Failure      401 {object} dto.ErrorResponse
// @Router       /auth/refresh [post]
func (h *AuthHandler) Refresh(c *gin.Context) {
	var req dto.RefreshTokenRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"message": err.Error()})
		return
	}

	resp, err := h.authService.Refresh(c.Request.Context(), req.RefreshToken)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"message": "invalid or expired refresh token"})
		return
	}

	c.JSON(http.StatusOK, resp)
}

// Logout godoc
// @Summary      Logout (invalidates client-side token)
// @Tags         auth
// @Security     BearerAuth
// @Produce      json
// @Success      200 {object} map[string]string
// @Failure      401 {object} dto.ErrorResponse
// @Router       /auth/logout [post]
func (h *AuthHandler) Logout(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"message": "logged out"})
}

// Me godoc
// @Summary      Get current authenticated user info
// @Tags         auth
// @Security     BearerAuth
// @Produce      json
// @Success      200 {object} dto.MeResponse
// @Failure      401 {object} dto.ErrorResponse
// @Router       /auth/me [get]
func (h *AuthHandler) Me(c *gin.Context) {
	c.JSON(http.StatusOK, dto.MeResponse{
		UserID: c.GetString(middleware.ContextUserIDKey),
		Email:  c.GetString(middleware.ContextEmailKey),
		Role:   c.GetString(middleware.ContextRoleKey),
	})
}
