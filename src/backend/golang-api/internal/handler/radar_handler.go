package handler

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

type RadarHandler struct{}

func NewRadarHandler() *RadarHandler {
	return &RadarHandler{}
}

func (h *RadarHandler) Index(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{"message": "radar page endpoint not implemented yet"})
}

func (h *RadarHandler) Top4(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{"message": "radar top4 endpoint not implemented yet"})
}

func (h *RadarHandler) Search(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{"message": "radar search endpoint not implemented yet"})
}

func (h *RadarHandler) ExportPNG(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{"message": "radar export png endpoint not implemented yet"})
}

func (h *RadarHandler) ExportCSV(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{"message": "radar export csv endpoint not implemented yet"})
}

func (h *RadarHandler) Top10(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{"message": "radar top10 endpoint not implemented yet"})
}
