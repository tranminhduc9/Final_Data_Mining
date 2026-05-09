package postgres

import "github.com/techpulsevn/final-data-mining/golang-api/internal/database"

type RadarRepository struct {
	DB *database.Postgres
}

func NewRadarRepository(db *database.Postgres) *RadarRepository {
	return &RadarRepository{DB: db}
}
