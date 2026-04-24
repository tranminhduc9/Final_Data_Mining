package postgres

import (
	"context"
	"errors"
	"fmt"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgconn"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/database"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/domain"
)

var (
	ErrNotFound   = errors.New("not found")
	ErrEmailTaken = errors.New("email already taken")
)

type UserRepository struct {
	DB *database.Postgres
}

func NewUserRepository(db *database.Postgres) *UserRepository {
	return &UserRepository{DB: db}
}

func (r *UserRepository) Create(ctx context.Context, email, passwordHash, fullName string) (*domain.User, error) {
	var u domain.User
	err := r.DB.Pool.QueryRow(ctx,
		`INSERT INTO users (email, password_hash, full_name)
		 VALUES ($1, $2, $3)
		 RETURNING id, email, full_name, subscription_tier`,
		email, passwordHash, fullName,
	).Scan(&u.ID, &u.Email, &u.FullName, &u.SubscriptionTier)
	if err != nil {
		var pgErr *pgconn.PgError
		if errors.As(err, &pgErr) && pgErr.Code == "23505" {
			return nil, ErrEmailTaken
		}
		return nil, fmt.Errorf("create user: %w", err)
	}
	return &u, nil
}

func (r *UserRepository) FindByEmail(ctx context.Context, email string) (*domain.User, error) {
	var u domain.User
	err := r.DB.Pool.QueryRow(ctx,
		`SELECT id, email, full_name, subscription_tier, password_hash
		 FROM users WHERE email = $1`,
		email,
	).Scan(&u.ID, &u.Email, &u.FullName, &u.SubscriptionTier, &u.PasswordHash)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, ErrNotFound
		}
		return nil, fmt.Errorf("find user by email: %w", err)
	}
	return &u, nil
}

func (r *UserRepository) FindByID(ctx context.Context, id string) (*domain.User, error) {
	var u domain.User
	err := r.DB.Pool.QueryRow(ctx,
		`SELECT id, email, full_name, subscription_tier
		 FROM users WHERE id = $1`,
		id,
	).Scan(&u.ID, &u.Email, &u.FullName, &u.SubscriptionTier)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, ErrNotFound
		}
		return nil, fmt.Errorf("find user by id: %w", err)
	}
	return &u, nil
}
