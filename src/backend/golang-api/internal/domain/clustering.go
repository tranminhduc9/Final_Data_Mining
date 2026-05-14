package domain

// ClusterSummary là metadata gọn của 1 cluster (không kèm danh sách members).
type ClusterSummary struct {
	ClusterID  int     `json:"cluster_id" example:"0"`
	Label      string  `json:"label" example:"Lập trình Backend Python"`
	LabelEn    string  `json:"label_en" example:"Python Backend Programming"`
	Domain     string  `json:"domain" example:"Backend"`
	Confidence float64 `json:"confidence" example:"0.87"`
	IsCoherent bool    `json:"is_coherent" example:"true"`
	NMembers   int     `json:"n_members" example:"42"`
}

// ClusterDetail mở rộng ClusterSummary kèm description, coherence_reason, outliers và danh sách tech members.
type ClusterDetail struct {
	ClusterSummary
	Description     string   `json:"description" example:"Cluster chứa các công nghệ phía backend dùng Python."`
	CoherenceReason *string  `json:"coherence_reason" extensions:"x-nullable=true"`
	Outliers        []string `json:"outliers" example:"jQuery,WordPress"`
	Members         []string `json:"members" example:"Python,Django,FastAPI,Flask"`
}

// TechClusterResult là kết quả tra cluster cho 1 tech name (case-insensitive).
// Khi không tìm thấy: found=false và mọi field cluster đều null.
type TechClusterResult struct {
	TechName  string  `json:"tech_name" example:"Python"`
	TechID    *string `json:"tech_id" extensions:"x-nullable=true"`
	ClusterID *int    `json:"cluster_id" extensions:"x-nullable=true"`
	Label     *string `json:"label" extensions:"x-nullable=true"`
	LabelEn   *string `json:"label_en" extensions:"x-nullable=true"`
	Domain    *string `json:"domain" extensions:"x-nullable=true"`
	Found     bool    `json:"found" example:"true"`
}

// BatchPredictRequest — body cho POST /clustering/predict/batch.
type BatchPredictRequest struct {
	TechNames []string `json:"tech_names" binding:"required" example:"Python,NodeJS,Rust"`
}

// BatchPredictResponse — kết quả batch lookup. snapshot_tag dùng để frontend cache invalidation.
type BatchPredictResponse struct {
	Results     []TechClusterResult `json:"results"`
	NFound      int                 `json:"n_found" example:"2"`
	NNotFound   int                 `json:"n_not_found" example:"1"`
	SnapshotTag string              `json:"snapshot_tag" example:"2025-05-01"`
}
