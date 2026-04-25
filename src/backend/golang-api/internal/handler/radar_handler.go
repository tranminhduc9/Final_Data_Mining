package handler

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/service"
)

type RadarHandler struct {
	radarService *service.RadarService
}

func NewRadarHandler(radarService *service.RadarService) *RadarHandler {
	return &RadarHandler{radarService: radarService}
}

func (h *RadarHandler) Index(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{"message": "radar page endpoint not implemented yet"})
}

func (h *RadarHandler) Top4(c *gin.Context) {
	trends, err := h.radarService.GetTop4(c.Request.Context())
	if err != nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"message": "failed to fetch top4: " + err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"data": trends})
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
