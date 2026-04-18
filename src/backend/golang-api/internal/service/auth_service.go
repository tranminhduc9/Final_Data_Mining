package service

import (
	"time"

	"github.com/techpulsevn/final-data-mining/golang-api/internal/dto"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/middleware"
)

type AuthService struct {
	jwtMiddleware *middleware.JWTMiddleware
}

func NewAuthService(jwtMiddleware *middleware.JWTMiddleware) *AuthService {
	return &AuthService{jwtMiddleware: jwtMiddleware}
}

func (s *AuthService) BuildLoginResponse(email string) (dto.AuthResponse, error) {
	accessToken, err := s.jwtMiddleware.GenerateToken("demo-user-id", email, "user", time.Hour)
	if err != nil {
		return dto.AuthResponse{}, err
	}

	refreshToken, err := s.jwtMiddleware.GenerateToken("demo-user-id", email, "user", 24*time.Hour)
	if err != nil {
		return dto.AuthResponse{}, err
	}

	return dto.AuthResponse{
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
		TokenType:    "Bearer",
		ExpiresIn:    3600,
		Message:      "login scaffold success",
	}, nil
}
