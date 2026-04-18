package postgres

import "github.com/techpulsevn/final-data-mining/golang-api/internal/database"

type CompareRepository struct {
	DB *database.Postgres
}

func NewCompareRepository(db *database.Postgres) *CompareRepository {
	return &CompareRepository{DB: db}
}
