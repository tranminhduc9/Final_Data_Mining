package service

import (
	"context"
	"errors"

	"github.com/techpulsevn/final-data-mining/golang-api/internal/repository/postgres"
)

var ErrInvalidSettingKey = errors.New("invalid setting key")

var validSettingKeys = map[string]bool{
	"maintenance_web":    true,
	"maintenance_mobile": true,
	"feature_graph":      true,
}

var settingDefaults = map[string]string{
	"maintenance_web":    "false",
	"maintenance_mobile": "false",
	"feature_graph":      "true",
}

type SettingsService struct {
	repo *postgres.SettingsRepository
}

func NewSettingsService(repo *postgres.SettingsRepository) *SettingsService {
	return &SettingsService{repo: repo}
}

func (s *SettingsService) Get(ctx context.Context, key string) (string, error) {
	if s.repo == nil {
		if v, ok := settingDefaults[key]; ok {
			return v, nil
		}
		return "", ErrInvalidSettingKey
	}
	return s.repo.Get(ctx, key)
}

func (s *SettingsService) Set(ctx context.Context, key, value string) error {
	if !validSettingKeys[key] {
		return ErrInvalidSettingKey
	}
	if s.repo == nil {
		return errors.New("database unavailable")
	}
	return s.repo.Set(ctx, key, value)
}

func (s *SettingsService) GetAll(ctx context.Context) (map[string]string, error) {
	if s.repo == nil {
		result := map[string]string{}
		for k, v := range settingDefaults {
			result[k] = v
		}
		return result, nil
	}
	return s.repo.GetAll(ctx)
}
