package domain

type RadarTrend struct {
	Industry        string   `json:"industry"`
	JobCount        int      `json:"job_count"`
	JobsToLastMonth int      `json:"jobs_to_last_month"`
	GrowthRate      *float64 `json:"growth_rate"` // nil nếu chưa có dữ liệu tháng trước
}
