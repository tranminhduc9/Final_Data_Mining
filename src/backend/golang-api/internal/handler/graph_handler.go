package handler

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

type GraphHandler struct{}

func NewGraphHandler() *GraphHandler {
	return &GraphHandler{}
}

func (h *GraphHandler) Index(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{"message": "graph page endpoint not implemented yet"})
}

func (h *GraphHandler) Explore(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{"message": "graph explore endpoint not implemented yet"})
}

func (h *GraphHandler) Filter(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{"message": "graph filter endpoint not implemented yet"})
}
