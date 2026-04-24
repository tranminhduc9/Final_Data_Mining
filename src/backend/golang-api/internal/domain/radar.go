package domain

type RadarTrend struct {
	Technology string  `json:"technology"`
	Sentiment  float64 `json:"sentiment"`
	JobCount   int     `json:"job_count"`
	YoY        float64 `json:"yoy"`
	GrowthRate float64 `json:"growth_rate"`
}
