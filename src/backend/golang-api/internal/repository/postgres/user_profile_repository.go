package postgres

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"strings"

	"github.com/jackc/pgx/v5"
	"github.com/lib/pq"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/database"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/domain"
)

type UserProfileRepository struct {
	DB *database.Postgres
}

func NewUserProfileRepository(db *database.Postgres) *UserProfileRepository {
	return &UserProfileRepository{DB: db}
}

func (r *UserProfileRepository) FindByUserID(ctx context.Context, userID string) (*domain.UserProfile, error) {
	var p domain.UserProfile
	var techJSON *string
	err := r.DB.Pool.QueryRow(ctx,
		`SELECT user_id, job_role, technologies::text, location, bio
		 FROM user_profile WHERE user_id = $1`,
		userID,
	).Scan(&p.UserID, &p.JobRole, &techJSON, &p.Location, &p.Bio)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, ErrNotFound
		}
		return nil, fmt.Errorf("find user profile: %w", err)
	}
	p.Technologies = parseTechnologies(techJSON)
	return &p, nil
}

func (r *UserProfileRepository) CreateProfile(ctx context.Context, userID string) (*domain.UserProfile, error) {
	var p domain.UserProfile
	var techJSON *string
	err := r.DB.Pool.QueryRow(ctx,
		`INSERT INTO user_profile (user_id)
		 VALUES ($1)
		 ON CONFLICT (user_id) DO NOTHING
		 RETURNING user_id, job_role, technologies::text, location, bio`,
		userID,
	).Scan(&p.UserID, &p.JobRole, &techJSON, &p.Location, &p.Bio)
	if err != nil && !errors.Is(err, pgx.ErrNoRows) {
		return nil, fmt.Errorf("create profile: %w", err)
	}
	p.Technologies = parseTechnologies(techJSON)
	if errors.Is(err, pgx.ErrNoRows) {
		p = domain.UserProfile{UserID: userID, Technologies: []string{}}
	}
	return &p, nil
}

func (r *UserProfileRepository) UpdateProfile(ctx context.Context, userID string, jobRole *string, technologies []string, location, bio *string) (*domain.UserProfile, error) {
	var p domain.UserProfile
	var techJSON *string

	if technologies == nil {
		technologies = []string{}
	}

	err := r.DB.Pool.QueryRow(ctx,
		`INSERT INTO user_profile (user_id, job_role, technologies, location, bio)
		 VALUES ($1, $2, $3, $4, $5)
		 ON CONFLICT (user_id) DO UPDATE
		 SET job_role = COALESCE($2, user_profile.job_role),
		     technologies = CASE WHEN $3::text IS NOT NULL THEN $3::text[] ELSE user_profile.technologies END,
		     location = COALESCE($4, user_profile.location),
		     bio = COALESCE($5, user_profile.bio)
		 RETURNING user_id, job_role, technologies::text, location, bio`,
		userID, jobRole, pq.Array(technologies), location, bio,
	).Scan(&p.UserID, &p.JobRole, &techJSON, &p.Location, &p.Bio)
	if err != nil {
		return nil, fmt.Errorf("update profile: %w", err)
	}
	p.Technologies = parseTechnologies(techJSON)
	return &p, nil
}

func parseTechnologies(techJSON *string) []string {
	if techJSON == nil || *techJSON == "" {
		return []string{}
	}

	// Xử lý format: ['python', 'java'] hoặc {python,java}
	str := *techJSON
	if strings.HasPrefix(str, "[") && strings.HasSuffix(str, "]") {
		// JSON array format
		var techs []string
		if err := json.Unmarshal([]byte(str), &techs); err == nil {
			return techs
		}
	} else if strings.HasPrefix(str, "{") && strings.HasSuffix(str, "}") {
		// PostgreSQL array format {a,b,c}
		inner := strings.TrimPrefix(strings.TrimSuffix(str, "}"), "{")
		if inner == "" {
			return []string{}
		}
		return strings.Split(inner, ",")
	}

	return []string{}
}
