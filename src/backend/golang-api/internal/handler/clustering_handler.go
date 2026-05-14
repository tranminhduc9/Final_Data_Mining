package handler

import (
	"errors"
	"net/http"
	"strconv"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/domain"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/service"
)

type ClusteringHandler struct {
	ML *service.MLClusteringClient
}

func NewClusteringHandler(ml *service.MLClusteringClient) *ClusteringHandler {
	return &ClusteringHandler{ML: ml}
}

func writeUpstreamError(c *gin.Context, err error, defaultMsg string) {
	var ue *service.UpstreamError
	if errors.As(err, &ue) {
		switch {
		case ue.StatusCode == http.StatusNotFound:
			c.JSON(http.StatusNotFound, gin.H{"message": defaultMsg + ": not found"})
		case ue.StatusCode >= 500:
			c.JSON(http.StatusServiceUnavailable, gin.H{"message": defaultMsg + ": " + err.Error()})
		default:
			c.JSON(http.StatusBadGateway, gin.H{"message": defaultMsg + ": " + err.Error()})
		}
		return
	}
	c.JSON(http.StatusServiceUnavailable, gin.H{"message": defaultMsg + ": " + err.Error()})
}

// ListClusters godoc
// @Summary      List all clusters
// @Description  Trả về toàn bộ cluster đã được phân (noise cluster -1 bị loại). Mỗi item là `ClusterSummary` (không kèm member list — dùng `/clustering/clusters/{id}` để lấy chi tiết).
// @Description
// @Description  Query param `is_coherent` là tuỳ chọn:
// @Description  - `true`  → chỉ trả cluster có nhãn coherent (đa số trường hợp dùng cho UI).
// @Description  - `false` → chỉ trả cluster bị LLM đánh giá thiếu nhất quán (dùng cho admin/debug).
// @Description  - bỏ qua → trả tất cả.
// @Description
// @Description  Upstream: GET /clusters trên ml-clustering (port 8001).
// @Tags         clustering
// @Produce      json
// @Param        is_coherent  query  bool  false  "Filter theo cờ is_coherent (bỏ qua = trả tất cả)"
// @Success      200 {object} dto.ListClustersResponse
// @Failure      400 {object} dto.ErrorResponse  "is_coherent không phải boolean"
// @Failure      502 {object} dto.ErrorResponse  "Upstream trả status không hợp lệ"
// @Failure      503 {object} dto.ErrorResponse  "ml-clustering không reachable hoặc đang maintenance"
// @Router       /clustering/clusters [get]
func (h *ClusteringHandler) ListClusters(c *gin.Context) {
	var isCoherent *bool
	if raw := strings.TrimSpace(c.Query("is_coherent")); raw != "" {
		v, err := strconv.ParseBool(raw)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"message": "is_coherent must be a boolean"})
			return
		}
		isCoherent = &v
	}

	result, err := h.ML.ListClusters(c.Request.Context(), isCoherent)
	if err != nil {
		writeUpstreamError(c, err, "failed to list clusters")
		return
	}
	c.JSON(http.StatusOK, gin.H{"data": result})
}

// GetCluster godoc
// @Summary      Get cluster detail by id
// @Description  Trả về metadata đầy đủ của 1 cluster: label, domain, description (LLM-generated), coherence_reason, outliers, và toàn bộ danh sách tech members trong cluster.
// @Description
// @Description  Lưu ý: `id = -1` là noise cluster (không có metadata) — sẽ trả 404.
// @Description
// @Description  Upstream: GET /clusters/{id} trên ml-clustering (port 8001).
// @Tags         clustering
// @Produce      json
// @Param        id   path  int  true  "Cluster ID (số nguyên, >= 0)"
// @Success      200 {object} dto.ClusterDetailResponse
// @Failure      400 {object} dto.ErrorResponse  "id không phải số nguyên"
// @Failure      404 {object} dto.ErrorResponse  "Cluster id không tồn tại"
// @Failure      502 {object} dto.ErrorResponse  "Upstream trả status không hợp lệ"
// @Failure      503 {object} dto.ErrorResponse  "ml-clustering không reachable hoặc đang maintenance"
// @Router       /clustering/clusters/{id} [get]
func (h *ClusteringHandler) GetCluster(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.Atoi(idStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"message": "id must be an integer"})
		return
	}

	result, err := h.ML.GetCluster(c.Request.Context(), id)
	if err != nil {
		writeUpstreamError(c, err, "failed to get cluster")
		return
	}
	c.JSON(http.StatusOK, gin.H{"data": result})
}

// GetTechCluster godoc
// @Summary      Get the cluster a technology belongs to
// @Description  Tra cứu cluster của 1 tech theo tên (case-insensitive).
// @Description
// @Description  Edge cases:
// @Description  - Tech không có trong snapshot hiện tại → upstream trả 404 (gateway forward thành 404).
// @Description  - Tech ở noise cluster (-1) → 200 với `cluster_id: -1` và `label: null`.
// @Description  - Tên có ký tự đặc biệt (C++, C#, khoảng trắng) → tự động URL-encode khi forward sang upstream.
// @Description
// @Description  Upstream: GET /tech/{name}/cluster trên ml-clustering (port 8001).
// @Tags         clustering
// @Produce      json
// @Param        name  path  string  true  "Tên technology (case-insensitive, ví dụ: Python, C++, NodeJS)"
// @Success      200 {object} dto.TechClusterResponse
// @Failure      400 {object} dto.ErrorResponse  "name rỗng"
// @Failure      404 {object} dto.ErrorResponse  "Tech name không có trong snapshot hiện tại"
// @Failure      502 {object} dto.ErrorResponse  "Upstream trả status không hợp lệ"
// @Failure      503 {object} dto.ErrorResponse  "ml-clustering không reachable hoặc đang maintenance"
// @Router       /clustering/tech/{name}/cluster [get]
func (h *ClusteringHandler) GetTechCluster(c *gin.Context) {
	name := strings.TrimSpace(c.Param("name"))
	if name == "" {
		c.JSON(http.StatusBadRequest, gin.H{"message": "name is required"})
		return
	}

	result, err := h.ML.GetTechCluster(c.Request.Context(), name)
	if err != nil {
		writeUpstreamError(c, err, "failed to get tech cluster")
		return
	}
	c.JSON(http.StatusOK, gin.H{"data": result})
}

// PredictBatch godoc
// @Summary      Batch lookup clusters for multiple tech names
// @Description  Tra cluster cho nhiều tech name trong 1 request. Mỗi item trong `results` luôn có field `found` để client biết tech đó có trong snapshot hay không (không bao giờ trả 404 ở level batch — chỉ trả 4xx/5xx khi request invalid hoặc upstream lỗi).
// @Description
// @Description  Field `snapshot_tag` ở response chính là phiên bản snapshot ml-clustering — client có thể dùng làm cache key.
// @Description
// @Description  Upstream: POST /predict/batch trên ml-clustering (port 8001).
// @Tags         clustering
// @Accept       json
// @Produce      json
// @Param        body  body  domain.BatchPredictRequest  true  "Danh sách tech names cần tra (không rỗng)"
// @Success      200 {object} dto.BatchPredictResponseWrapper
// @Failure      400 {object} dto.ErrorResponse  "Body không hợp lệ hoặc tech_names rỗng"
// @Failure      502 {object} dto.ErrorResponse  "Upstream trả status không hợp lệ"
// @Failure      503 {object} dto.ErrorResponse  "ml-clustering không reachable hoặc đang maintenance"
// @Router       /clustering/predict/batch [post]
func (h *ClusteringHandler) PredictBatch(c *gin.Context) {
	var req domain.BatchPredictRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"message": "invalid request body: " + err.Error()})
		return
	}
	if len(req.TechNames) == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"message": "tech_names must not be empty"})
		return
	}

	result, err := h.ML.PredictBatch(c.Request.Context(), req)
	if err != nil {
		writeUpstreamError(c, err, "failed to predict batch")
		return
	}
	c.JSON(http.StatusOK, gin.H{"data": result})
}
