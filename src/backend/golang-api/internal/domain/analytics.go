package domain

type KeywordCount struct {
	Keyword string `json:"keyword"`
	Count   int    `json:"count"`
}

type MonthlyVisit struct {
	Month string `json:"month"` // "YYYY-MM"
	Count int    `json:"count"`
}
