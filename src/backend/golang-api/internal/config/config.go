package config

import (
	"fmt"
	"os"
	"strings"

	"github.com/joho/godotenv"
)

type Config struct {
	AppEnv                     string
	Port                       string
	PostgresConnectionString   string
	PythonAIBaseURL            string
}

func Load() (*Config, error) {
	_ = godotenv.Load(".env")
	_ = godotenv.Load("../.env")
	_ = godotenv.Load(".env.example")
	_ = godotenv.Load("../.env.example")

	cfg := &Config{
		AppEnv:                   getEnv("APP_ENV", "development"),
		Port:                     getEnv("PORT", "8080"),
		PostgresConnectionString: normalize(getEnv("PostgreSQL_CONNECTION_STRING", "")),
		PythonAIBaseURL:          getEnv("PYTHON_AI_BASE_URL", "http://localhost:8001"),
	}

	if cfg.PostgresConnectionString == "" {
		return nil, fmt.Errorf("missing PostgreSQL_CONNECTION_STRING")
	}

	return cfg, nil
}

func getEnv(key, fallback string) string {
	value := strings.TrimSpace(os.Getenv(key))
	if value == "" {
		return fallback
	}
	return value
}

func normalize(value string) string {
	value = strings.ReplaceAll(value, "\n", "")
	value = strings.ReplaceAll(value, "\r", "")
	return strings.TrimSpace(value)
}
