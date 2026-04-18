package router

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/config"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/database"
)

func New(cfg *config.Config, db *database.Postgres) *gin.Engine {
	r := gin.New()
	r.Use(gin.Logger(), gin.Recovery())

	databaseStatus := "disconnected"
	if db != nil && db.Pool != nil {
		databaseStatus = "connected"
	}

	r.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":      "ok",
			"service":     "golang-api",
			"environment": cfg.AppEnv,
			"database":    databaseStatus,
		})
	})

	api := r.Group("/api/v1")
	api.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":  "ok",
			"version": "v1",
		})
	})

	return r
}
