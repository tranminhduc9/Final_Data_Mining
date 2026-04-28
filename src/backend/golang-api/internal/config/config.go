package config

import (
	"fmt"
	"os"
	"strings"

	"github.com/joho/godotenv"
)

type Config struct {
	AppEnv                   string
	Port                     string
	PostgresConnectionString string
	PythonAIBaseURL          string
	JWTSecret                string
	Neo4jURI                 string
	Neo4jUsername            string
	Neo4jPassword            string
	Neo4jDatabase            string
	AllowedOrigins           []string
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
		JWTSecret:                getEnv("JWT_SECRET", "change-this-in-production"),
		Neo4jURI:                 getEnv("NEO4J_URI", ""),
		Neo4jUsername:            getEnv("NEO4J_USERNAME", ""),
		Neo4jPassword:            getEnv("NEO4J_PASSWORD", ""),
		Neo4jDatabase:            getEnv("NEO4J_DATABASE", ""),
		AllowedOrigins:           parseOrigins(getEnv("ALLOWED_ORIGINS", "*")),
	}

	if cfg.PostgresConnectionString == "" {
		return nil, fmt.Errorf("missing PostgreSQL_CONNECTION_STRING")
	}

	return cfg, nil
}

func parseOrigins(raw string) []string {
	var origins []string
	for _, o := range strings.Split(raw, ",") {
		o = strings.TrimSpace(o)
		if o != "" {
			origins = append(origins, o)
		}
	}
	if len(origins) == 0 {
		return []string{"*"}
	}
	return origins
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
