package router

import (
	"net/http"
	"time"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	swaggerFiles "github.com/swaggo/files"
	ginSwagger "github.com/swaggo/gin-swagger"
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

	r.Use(cors.New(cors.Config{
		AllowOrigins:     cfg.AllowedOrigins,
		AllowMethods:     []string{"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"},
		AllowHeaders:     []string{"Origin", "Content-Type", "Authorization", "X-Client-Type"},
		ExposeHeaders:    []string{"Content-Length"},
		AllowCredentials: true,
		MaxAge:           12 * time.Hour,
	}))

	databaseStatus := "disconnected"
	if db != nil && db.Pool != nil {
		databaseStatus = "connected"
	}

	neo4jStatus := "disconnected"
	if neo4jDB != nil {
		neo4jStatus = "connected"
	}

	jwtMiddleware := middleware.NewJWTMiddleware(cfg.JWTSecret)

	var userRepo *postgres.UserRepository
	var analyticsRepo *postgres.AnalyticsRepository
	var settingsRepo *postgres.SettingsRepository
	if db != nil {
		userRepo = postgres.NewUserRepository(db)
		analyticsRepo = postgres.NewAnalyticsRepository(db)
		settingsRepo = postgres.NewSettingsRepository(db)
	}
	authService := service.NewAuthService(jwtMiddleware, userRepo)
	authHandler := handler.NewAuthHandler(authService)

	analyticsService := service.NewAnalyticsService(analyticsRepo)
	adminHandler := handler.NewAdminHandler(analyticsService, userRepo)

	settingsService := service.NewSettingsService(settingsRepo)
	settingsHandler := handler.NewSettingsHandler(settingsService)

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
	aiClient := service.NewAIClient(cfg.PythonAIBaseURL)
	chatHandler := handler.NewChatHandler(aiClient)

	r.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))

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
	api.Use(middleware.Analytics(analyticsService))
	{
		api.GET("/health", func(c *gin.Context) {
			c.JSON(http.StatusOK, gin.H{
				"status":  "ok",
				"version": "v1",
			})
		})

		// Public: returns maintenance flags and feature toggles (no auth, no maintenance block)
		api.GET("/status", settingsHandler.Status)

		api.GET("/radar", radarHandler.Index)
		api.GET("/compare", compareHandler.Index)
		api.GET("/graph", graphHandler.Index)
		api.GET("/chat", jwtMiddleware.RequireAuth(), chatHandler.Index)

		radar := api.Group("/radar")
		radar.Use(middleware.MaintenanceCheck(settingsService))
		{
			radar.GET("/top4", radarHandler.Top4)
			radar.GET("/search", radarHandler.Search)
			radar.GET("/export-png", radarHandler.ExportPNG)
			radar.GET("/export-csv", radarHandler.ExportCSV)
			radar.GET("/top10", radarHandler.Top10)
		}

		compare := api.Group("/compare")
		compare.Use(middleware.MaintenanceCheck(settingsService))
		{
			compare.GET("/search", compareHandler.Search)
			compare.GET("/llm-summary", compareHandler.LLMSummary)
		}

		graph := api.Group("/graph")
		graph.Use(middleware.MaintenanceCheck(settingsService))
		graph.Use(middleware.FeatureEnabled(settingsService, "feature_graph"))
		{
			graph.GET("/explore", graphHandler.Explore)
			graph.GET("/road_analysis", graphHandler.RoadAnalysis)
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
		chat.Use(middleware.MaintenanceCheck(settingsService))
		{
			chat.POST("/session", chatHandler.CreateSession)
			chat.GET("/session/:session_id/messages", chatHandler.GetMessages)
			chat.POST("/session/:session_id/messages", chatHandler.PostMessage)
			chat.POST("/session/:session_id/messages/stream", chatHandler.PostMessageStream)
		}

		admin := api.Group("/admin")
		admin.Use(jwtMiddleware.RequireAdmin())
		{
			admin.GET("/users", adminHandler.ListUsers)
			admin.POST("/users", adminHandler.InsertUser)
			admin.PUT("/users/:id", adminHandler.AlterUser)
			admin.DELETE("/users/:id", adminHandler.DeleteUser)

			admin.GET("/settings", settingsHandler.GetSettings)
			admin.PUT("/settings/:key", settingsHandler.UpdateSetting)

			dashboard := admin.Group("/dashboard")
			{
				dashboard.GET("/user-count", adminHandler.DashboardUserCount)
				dashboard.GET("/visits-today", adminHandler.DashboardVisitsToday)
				dashboard.GET("/searches-today", adminHandler.DashboardSearchesToday)
				dashboard.GET("/monthly-visits", adminHandler.DashboardMonthlyVisits)
				dashboard.GET("/top-keywords", adminHandler.DashboardTopKeywords)
			}
		}
	}

	return r
}
