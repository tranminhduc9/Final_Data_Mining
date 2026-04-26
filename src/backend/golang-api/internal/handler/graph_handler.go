package handler

import (
	"net/http"
	"strconv"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/service"
)

type GraphHandler struct {
	graphService *service.GraphService
}

func NewGraphHandler(graphService *service.GraphService) *GraphHandler {
	return &GraphHandler{graphService: graphService}
}

func (h *GraphHandler) Index(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{"message": "graph page endpoint not implemented yet"})
}

// Explore godoc
// @Summary      Explore knowledge graph starting from keyword nodes
// @Tags         graph
// @Produce      json
// @Param        keywords  query  []string  true   "Keywords (Technology or Skill names)"  collectionFormat(multi)
// @Param        depth     query  int       false  "Traversal depth: 1 or 2 (default 1)"
// @Success      200 {object} dto.GraphExploreResponse
// @Failure      400 {object} dto.ErrorResponse
// @Failure      503 {object} dto.ErrorResponse
// @Router       /graph/explore [get]
func (h *GraphHandler) Explore(c *gin.Context) {
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

	depthStr := c.DefaultQuery("depth", "1")
	depth, err := strconv.Atoi(depthStr)
	if err != nil || (depth != 1 && depth != 2) {
		c.JSON(http.StatusBadRequest, gin.H{"message": "depth must be 1 or 2"})
		return
	}

	result, err := h.graphService.Explore(c.Request.Context(), keywords, depth)
	if err != nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"message": "failed to explore graph: " + err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"data": result})
}

func (h *GraphHandler) Filter(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{"message": "graph filter endpoint not implemented yet"})
}
