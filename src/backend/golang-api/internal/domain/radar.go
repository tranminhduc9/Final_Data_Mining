package domain

type RadarTrend struct {
	Industry        string   `json:"industry"`
	JobCount        int      `json:"job_count"`
	JobsToLastMonth int      `json:"jobs_to_last_month"`
	GrowthRate      *float64 `json:"growth_rate"`
}

type RadarSearchPoint struct {
	Year     int            `json:"year"`
	Month    int            `json:"month"`
	Keywords map[string]int `json:"keywords"`
}
