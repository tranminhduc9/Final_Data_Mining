package handler

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

type ChatHandler struct{}

func NewChatHandler() *ChatHandler {
	return &ChatHandler{}
}

func (h *ChatHandler) Index(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{"message": "chat page endpoint not implemented yet"})
}

func (h *ChatHandler) CreateSession(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{"message": "create session endpoint not implemented yet"})
}

func (h *ChatHandler) GetMessages(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{"message": "get session messages endpoint not implemented yet"})
}

func (h *ChatHandler) PostMessage(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{"message": "post session message endpoint not implemented yet"})
}
