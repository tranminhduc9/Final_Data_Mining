package domain

type RadarTrend struct {
	Industry        string   `json:"industry"`
	JobCount        int      `json:"job_count"`
	JobsToLastMonth int      `json:"jobs_to_last_month"`
	GrowthRate      *float64 `json:"growth_rate"`
	JobsThisMonth   int      `json:"jobs_this_month"`
	JobsLastMonth   int      `json:"jobs_last_month"`
	MoMRate         *float64 `json:"mom_rate"` // nil nếu tháng trước không có job nào
}

type RadarSearchPoint struct {
	Date     string         `json:"date" example:"2026-03-18"`
	Year     int            `json:"year"`
	Month    int            `json:"month"`
	Day      int            `json:"day"`
	Keywords map[string]int `json:"keywords"`
}

type RadarKeywordCount struct {
	Keyword  string `json:"keyword"`
	JobCount int    `json:"job_count"`
}
