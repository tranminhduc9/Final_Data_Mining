package handler

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/service"
)

type AuthHandler struct {
	authService *service.AuthService
}

func NewAuthHandler(authService *service.AuthService) *AuthHandler {
	return &AuthHandler{authService: authService}
}

func (h *AuthHandler) Register(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{"message": "register endpoint not implemented yet"})
}

func (h *AuthHandler) Login(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{"message": "login endpoint not implemented yet"})
}

func (h *AuthHandler) Refresh(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{"message": "refresh endpoint not implemented yet"})
}

func (h *AuthHandler) Logout(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{"message": "logout endpoint not implemented yet"})
}

func (h *AuthHandler) Me(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{"message": "me endpoint not implemented yet"})
}
