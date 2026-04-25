package handler

import (
	"net/http"
	"strconv"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/service"
)

type CompareHandler struct {
	compareService *service.CompareService
}

func NewCompareHandler(compareService *service.CompareService) *CompareHandler {
	return &CompareHandler{compareService: compareService}
}

func (h *CompareHandler) Index(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{"message": "compare page endpoint not implemented yet"})
}

func (h *CompareHandler) Search(c *gin.Context) {
	var keywords []string
	seen := map[string]bool{}
	for _, raw := range c.QueryArray("keywords") {
		for _, kw := range strings.Split(raw, ",") {
			kw = strings.TrimSpace(kw)
			if kw != "" && !seen[kw] {
				seen[kw] = true
				keywords = append(keywords, kw)
			}
		}
	}
	if len(keywords) == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"message": "keywords is required"})
		return
	}

	monthsStr := c.DefaultQuery("months", "6")
	months, err := strconv.Atoi(monthsStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"message": "months must be an integer"})
		return
	}
	validMonths := map[int]bool{3: true, 6: true, 12: true, 24: true}
	if !validMonths[months] {
		c.JSON(http.StatusBadRequest, gin.H{"message": "months must be one of: 3, 6, 12, 24"})
		return
	}

	results, err := h.compareService.Compare(c.Request.Context(), keywords, months)
	if err != nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"message": "failed to compare: " + err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"data": results})
}

func (h *CompareHandler) LLMSummary(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{"message": "compare llm summary endpoint not implemented yet"})
}
