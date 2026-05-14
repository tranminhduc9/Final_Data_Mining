package domain

type CompareMonthlyCount struct {
	Year     int `json:"year"`
	Month    int `json:"month"`
	JobCount int `json:"job_count"`
}

type CompareResult struct {
	Keyword    string                `json:"keyword"`
	JobCount   int                   `json:"job_count"`
	GrowthRate *float64              `json:"growth_rate"`
	MoMRate    *float64              `json:"mom_rate"`
	YoYRate    *float64              `json:"yoy_rate"`
	Monthly    []CompareMonthlyCount `json:"monthly"`
}
