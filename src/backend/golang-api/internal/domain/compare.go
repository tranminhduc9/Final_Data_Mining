package domain

type CompareMetric struct {
	Technology string  `json:"technology"`
	GrowthRate float64 `json:"growth_rate"`
	YoY        float64 `json:"yoy"`
	MoM        float64 `json:"mom"`
	Jobs       int     `json:"jobs"`
}
