package service

import (
	"context"
	"errors"
	"time"

	"github.com/techpulsevn/final-data-mining/golang-api/internal/dto"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/middleware"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/repository/postgres"
	"golang.org/x/crypto/bcrypt"
)

const (
	accessTokenTTL  = 15 * time.Minute
	refreshTokenTTL = 7 * 24 * time.Hour
)

var (
	ErrInvalidCredentials  = errors.New("invalid credentials")
	ErrDatabaseUnavailable = errors.New("database unavailable")
	ErrAccountBlocked      = errors.New("account is blocked")
)

type AuthService struct {
	jwtMiddleware *middleware.JWTMiddleware
	userRepo      *postgres.UserRepository
}

func NewAuthService(jwtMiddleware *middleware.JWTMiddleware, userRepo *postgres.UserRepository) *AuthService {
	return &AuthService{jwtMiddleware: jwtMiddleware, userRepo: userRepo}
}

func (s *AuthService) Register(ctx context.Context, email, password, fullName string) (dto.AuthResponse, error) {
	if s.userRepo == nil {
		return dto.AuthResponse{}, ErrDatabaseUnavailable
	}
	hash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return dto.AuthResponse{}, err
	}

	user, err := s.userRepo.Create(ctx, email, string(hash), fullName)
	if err != nil {
		return dto.AuthResponse{}, err
	}

	return s.buildTokenPair(user.ID, user.Email, "user")
}

func (s *AuthService) Login(ctx context.Context, email, password string) (dto.AuthResponse, error) {
	if s.userRepo == nil {
		return dto.AuthResponse{}, ErrDatabaseUnavailable
	}
	user, err := s.userRepo.FindByEmail(ctx, email)
	if err != nil {
		if errors.Is(err, postgres.ErrNotFound) {
			return dto.AuthResponse{}, ErrInvalidCredentials
		}
		return dto.AuthResponse{}, err
	}

	if err := bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(password)); err != nil {
		return dto.AuthResponse{}, ErrInvalidCredentials
	}

	if user.Status == "blocked" {
		return dto.AuthResponse{}, ErrAccountBlocked
	}

	return s.buildTokenPair(user.ID, user.Email, user.Role)
}

func (s *AuthService) Refresh(ctx context.Context, refreshToken string) (dto.AuthResponse, error) {
	claims, err := s.jwtMiddleware.ParseClaims(refreshToken)
	if err != nil {
		return dto.AuthResponse{}, errors.New("invalid refresh token")
	}

	if tokenType, _ := claims["token_type"].(string); tokenType != middleware.TokenTypeRefresh {
		return dto.AuthResponse{}, errors.New("invalid refresh token")
	}

	userID, _ := claims["sub"].(string)
	email, _ := claims["email"].(string)
	role, _ := claims["role"].(string)
	if role == "" {
		role = "user"
	}

	return s.buildTokenPair(userID, email, role)
}

func (s *AuthService) buildTokenPair(userID, email, role string) (dto.AuthResponse, error) {
	accessToken, err := s.jwtMiddleware.GenerateToken(userID, email, role, middleware.TokenTypeAccess, accessTokenTTL)
	if err != nil {
		return dto.AuthResponse{}, err
	}

	refreshToken, err := s.jwtMiddleware.GenerateToken(userID, email, role, middleware.TokenTypeRefresh, refreshTokenTTL)
	if err != nil {
		return dto.AuthResponse{}, err
	}

	return dto.AuthResponse{
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
		TokenType:    "Bearer",
		ExpiresIn:    int64(accessTokenTTL.Seconds()),
	}, nil
}
