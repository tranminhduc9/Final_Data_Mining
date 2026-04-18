package main

import (
	"context"
	"log"

	"github.com/techpulsevn/final-data-mining/golang-api/internal/config"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/database"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/router"
)

func main() {
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("load config: %v", err)
	}

	db, err := database.NewPostgres(context.Background(), cfg.PostgresConnectionString)
	if err != nil {
		log.Fatalf("connect postgres: %v", err)
	}
	defer db.Close()

	engine := router.New(cfg, db)
	log.Printf("golang-api started on :%s (%s)", cfg.Port, cfg.AppEnv)

	if err := engine.Run(":" + cfg.Port); err != nil {
		log.Fatalf("run server: %v", err)
	}
}
