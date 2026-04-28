package domain

type AdminStats struct {
	TotalUsers    int `json:"total_users"`
	VisitsToday   int `json:"visits_today"`
	SearchesToday int `json:"searches_today"`
}

type KeywordCount struct {
	Keyword string `json:"keyword"`
	Count   int    `json:"count"`
}
