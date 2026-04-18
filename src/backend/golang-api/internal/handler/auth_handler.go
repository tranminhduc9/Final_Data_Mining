package handler

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/dto"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/middleware"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/service"
)

type AuthHandler struct {
	authService *service.AuthService
}

func NewAuthHandler(authService *service.AuthService) *AuthHandler {
	return &AuthHandler{authService: authService}
}

func (h *AuthHandler) Register(c *gin.Context) {
	var req dto.RegisterRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"message": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, gin.H{
		"message": "register scaffold success",
		"data": gin.H{
			"email":     req.Email,
			"full_name": req.FullName,
		},
	})
}

func (h *AuthHandler) Login(c *gin.Context) {
	var req dto.LoginRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"message": err.Error()})
		return
	}

	resp, err := h.authService.BuildLoginResponse(req.Email)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"message": "failed to build login response"})
		return
	}

	c.JSON(http.StatusOK, resp)
}

func (h *AuthHandler) Refresh(c *gin.Context) {
	var req dto.RefreshTokenRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"message": err.Error()})
		return
	}

	c.JSON(http.StatusOK, dto.AuthResponse{
		TokenType: "Bearer",
		Message:   "refresh scaffold success",
		ExpiresIn: 3600,
	})
}

func (h *AuthHandler) Logout(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"message": "logout scaffold success"})
}

func (h *AuthHandler) Me(c *gin.Context) {
	c.JSON(http.StatusOK, dto.MeResponse{
		UserID: c.GetString(middleware.ContextUserIDKey),
		Email:  c.GetString(middleware.ContextEmailKey),
		Role:   c.GetString(middleware.ContextRoleKey),
	})
}
