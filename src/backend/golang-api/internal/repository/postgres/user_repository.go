package postgres

import "github.com/techpulsevn/final-data-mining/golang-api/internal/database"

type UserRepository struct {
	DB *database.Postgres
}

func NewUserRepository(db *database.Postgres) *UserRepository {
	return &UserRepository{DB: db}
}
