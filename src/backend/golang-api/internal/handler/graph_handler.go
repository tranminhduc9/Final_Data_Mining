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
// @Param        depth     query  int       false  "Traversal depth: 1 or 2 (default 1). Ignored when location is set."
// @Param        location  query  string    false  "Filter by company location (partial, case-insensitive). When set, requires exactly one keyword."
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

	location := strings.TrimSpace(c.Query("location"))
	if location != "" {
		if len(keywords) != 1 {
			c.JSON(http.StatusBadRequest, gin.H{"message": "exactly one keyword is required when location filter is used"})
			return
		}
		result, err := h.graphService.ExploreByLocation(c.Request.Context(), keywords[0], location)
		if err != nil {
			c.JSON(http.StatusServiceUnavailable, gin.H{"message": "failed to explore graph: " + err.Error()})
			return
		}
		c.JSON(http.StatusOK, gin.H{"data": result})
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

// RoadAnalysis godoc
// @Summary      Find shortest path between two Technology/Skill nodes
// @Description  Uses undirected shortest path (max 6 hops). Among all shortest paths, prefers one that passes through a Company node. Returns ordered nodes and edges.
// @Tags         graph
// @Produce      json
// @Param        from  query  string  true  "Start keyword (Technology or Skill name)"
// @Param        to    query  string  true  "End keyword (Technology or Skill name)"
// @Success      200 {object} dto.RoadAnalysisResponse
// @Failure      400 {object} dto.ErrorResponse
// @Failure      503 {object} dto.ErrorResponse
// @Router       /graph/road_analysis [get]
func (h *GraphHandler) RoadAnalysis(c *gin.Context) {
	from := strings.TrimSpace(c.Query("from"))
	to := strings.TrimSpace(c.Query("to"))
	if from == "" || to == "" {
		c.JSON(http.StatusBadRequest, gin.H{"message": "from and to are required"})
		return
	}
	if from == to {
		c.JSON(http.StatusBadRequest, gin.H{"message": "from and to must be different"})
		return
	}

	result, err := h.graphService.RoadAnalysis(c.Request.Context(), from, to)
	if err != nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"message": "road analysis failed: " + err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"data": result})
}

func (h *GraphHandler) Filter(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{"message": "graph filter endpoint not implemented yet"})
}
