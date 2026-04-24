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

	ctx := context.Background()

	db, err := database.NewPostgres(ctx, cfg.PostgresConnectionString)
	if err != nil {
		log.Fatalf("connect postgres: %v", err)
	}
	defer db.Close()

	neo4jDB, err := database.NewNeo4j(ctx, cfg.Neo4jURI, cfg.Neo4jUsername, cfg.Neo4jPassword, cfg.Neo4jDatabase)
	if err != nil {
		log.Printf("WARNING: neo4j unavailable — graph features disabled: %v", err)
	} else {
		defer neo4jDB.Close(ctx)
		log.Println("neo4j connected")
	}

	engine := router.New(cfg, db, neo4jDB)
	log.Printf("golang-api started on :%s (%s)", cfg.Port, cfg.AppEnv)

	if err := engine.Run(":" + cfg.Port); err != nil {
		log.Fatalf("run server: %v", err)
	}
}
