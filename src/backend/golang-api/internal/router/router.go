package router

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/config"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/database"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/handler"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/middleware"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/repository/neo4jrepo"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/repository/postgres"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/service"
)

func New(cfg *config.Config, db *database.Postgres, neo4jDB *database.Neo4jDB) *gin.Engine {
	r := gin.New()
	r.Use(gin.Logger(), gin.Recovery())

	databaseStatus := "disconnected"
	if db != nil && db.Pool != nil {
		databaseStatus = "connected"
	}

	neo4jStatus := "disconnected"
	if neo4jDB != nil {
		neo4jStatus = "connected"
	}

	jwtMiddleware := middleware.NewJWTMiddleware(cfg.JWTSecret)

	userRepo := postgres.NewUserRepository(db)
	authService := service.NewAuthService(jwtMiddleware, userRepo)
	authHandler := handler.NewAuthHandler(authService)

	var radarRepo *neo4jrepo.RadarRepository
	var compareRepo *neo4jrepo.CompareRepository
	var graphRepo *neo4jrepo.GraphRepository
	if neo4jDB != nil {
		radarRepo = neo4jrepo.NewRadarRepository(neo4jDB)
		compareRepo = neo4jrepo.NewCompareRepository(neo4jDB)
		graphRepo = neo4jrepo.NewGraphRepository(neo4jDB)
	}
	radarService := service.NewRadarService(radarRepo)
	radarHandler := handler.NewRadarHandler(radarService)
	compareService := service.NewCompareService(compareRepo)
	compareHandler := handler.NewCompareHandler(compareService)
	graphService := service.NewGraphService(graphRepo)
	graphHandler := handler.NewGraphHandler(graphService)
	chatHandler := handler.NewChatHandler()

	r.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":      "ok",
			"service":     "golang-api",
			"environment": cfg.AppEnv,
			"database":    databaseStatus,
			"neo4j":       neo4jStatus,
		})
	})

	api := r.Group("/api/v1")
	{
		api.GET("/health", func(c *gin.Context) {
			c.JSON(http.StatusOK, gin.H{
				"status":  "ok",
				"version": "v1",
			})
		})

		api.GET("/radar", radarHandler.Index)
		api.GET("/compare", compareHandler.Index)
		api.GET("/graph", graphHandler.Index)
		api.GET("/chat", jwtMiddleware.RequireAuth(), chatHandler.Index)

		radar := api.Group("/radar")
		{
			radar.GET("/top4", radarHandler.Top4)
			radar.GET("/search", radarHandler.Search)
			radar.GET("/export-png", radarHandler.ExportPNG)
			radar.GET("/export-csv", radarHandler.ExportCSV)
			radar.GET("/top10", radarHandler.Top10)
		}

		compare := api.Group("/compare")
		{
			compare.GET("/search", compareHandler.Search)
			compare.GET("/llm-summary", compareHandler.LLMSummary)
		}

		graph := api.Group("/graph")
		{
			graph.GET("/explore", graphHandler.Explore)
			graph.GET("/filter", graphHandler.Filter)
		}

		auth := api.Group("/auth")
		{
			auth.POST("/register", authHandler.Register)
			auth.POST("/login", authHandler.Login)
			auth.POST("/refresh", authHandler.Refresh)
			auth.POST("/logout", jwtMiddleware.RequireAuth(), authHandler.Logout)
			auth.GET("/me", jwtMiddleware.RequireAuth(), authHandler.Me)
		}

		chat := api.Group("/chat")
		chat.Use(jwtMiddleware.RequireAuth())
		{
			chat.POST("/session", chatHandler.CreateSession)
			chat.GET("/session/:session_id/messages", chatHandler.GetMessages)
			chat.POST("/session/:session_id/messages", chatHandler.PostMessage)
		}
	}

	return r
}
