package handler

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

type CompareHandler struct{}

func NewCompareHandler() *CompareHandler {
	return &CompareHandler{}
}

func (h *CompareHandler) Index(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{"message": "compare page endpoint not implemented yet"})
}

func (h *CompareHandler) Search(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{"message": "compare search endpoint not implemented yet"})
}

func (h *CompareHandler) LLMSummary(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{"message": "compare llm summary endpoint not implemented yet"})
}
