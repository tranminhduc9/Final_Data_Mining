package postgres

import "github.com/techpulsevn/final-data-mining/golang-api/internal/database"

type GraphRepository struct {
	DB *database.Postgres
}

func NewGraphRepository(db *database.Postgres) *GraphRepository {
	return &GraphRepository{DB: db}
}
