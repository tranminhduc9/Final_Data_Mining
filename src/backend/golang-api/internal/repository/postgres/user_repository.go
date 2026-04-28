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
		 RETURNING id, email, full_name, subscription_tier, role, status`,
		email, passwordHash, fullName,
	).Scan(&u.ID, &u.Email, &u.FullName, &u.SubscriptionTier, &u.Role, &u.Status)
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
		`SELECT id, email, full_name, subscription_tier, password_hash, role, status
		 FROM users WHERE email = $1`,
		email,
	).Scan(&u.ID, &u.Email, &u.FullName, &u.SubscriptionTier, &u.PasswordHash, &u.Role, &u.Status)
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
		`SELECT id, email, full_name, subscription_tier, role, status
		 FROM users WHERE id = $1`,
		id,
	).Scan(&u.ID, &u.Email, &u.FullName, &u.SubscriptionTier, &u.Role, &u.Status)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, ErrNotFound
		}
		return nil, fmt.Errorf("find user by id: %w", err)
	}
	return &u, nil
}

func (r *UserRepository) CreateFull(ctx context.Context, email, passwordHash, fullName, role, status string) (*domain.User, error) {
	var u domain.User
	err := r.DB.Pool.QueryRow(ctx,
		`INSERT INTO users (email, password_hash, full_name, role, status)
		 VALUES ($1, $2, $3, $4, $5)
		 RETURNING id, email, full_name, role, status`,
		email, passwordHash, fullName, role, status,
	).Scan(&u.ID, &u.Email, &u.FullName, &u.Role, &u.Status)
	if err != nil {
		var pgErr *pgconn.PgError
		if errors.As(err, &pgErr) && pgErr.Code == "23505" {
			return nil, ErrEmailTaken
		}
		return nil, fmt.Errorf("create user: %w", err)
	}
	return &u, nil
}

func (r *UserRepository) UpdateUser(ctx context.Context, id, fullName, email, role, status string) (*domain.User, error) {
	var u domain.User
	err := r.DB.Pool.QueryRow(ctx,
		`UPDATE users SET full_name=$2, email=$3, role=$4, status=$5
		 WHERE id=$1
		 RETURNING id, email, full_name, role, status`,
		id, fullName, email, role, status,
	).Scan(&u.ID, &u.Email, &u.FullName, &u.Role, &u.Status)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, ErrNotFound
		}
		var pgErr *pgconn.PgError
		if errors.As(err, &pgErr) && pgErr.Code == "23505" {
			return nil, ErrEmailTaken
		}
		return nil, fmt.Errorf("update user: %w", err)
	}
	return &u, nil
}

func (r *UserRepository) DeleteByID(ctx context.Context, id string) error {
	tag, err := r.DB.Pool.Exec(ctx, `DELETE FROM users WHERE id=$1`, id)
	if err != nil {
		return fmt.Errorf("delete user: %w", err)
	}
	if tag.RowsAffected() == 0 {
		return ErrNotFound
	}
	return nil
}

func (r *UserRepository) ListAll(ctx context.Context) ([]domain.User, error) {
	rows, err := r.DB.Pool.Query(ctx,
		`SELECT id, email, full_name, role, status
		 FROM users
		 ORDER BY CASE WHEN role = 'admin' THEN 0 ELSE 1 END, email ASC`,
	)
	if err != nil {
		return nil, fmt.Errorf("list users: %w", err)
	}
	defer rows.Close()

	users := []domain.User{}
	for rows.Next() {
		var u domain.User
		if err := rows.Scan(&u.ID, &u.Email, &u.FullName, &u.Role, &u.Status); err != nil {
			return nil, fmt.Errorf("list users scan: %w", err)
		}
		users = append(users, u)
	}
	return users, rows.Err()
}
