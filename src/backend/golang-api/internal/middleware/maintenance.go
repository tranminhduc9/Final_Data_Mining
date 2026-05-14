package middleware

import (
	"context"
	"net/http"

	"github.com/gin-gonic/gin"
)

// SettingsGetter is implemented by service.SettingsService.
type SettingsGetter interface {
	Get(ctx context.Context, key string) (string, error)
}

// MaintenanceCheck blocks requests when maintenance mode is active.
// Reads X-Client-Type header: "mobile" → checks maintenance_mobile, anything else → maintenance_web.
// Fails open (does not block) if the settings DB is unavailable.
func MaintenanceCheck(settings SettingsGetter) gin.HandlerFunc {
	return func(c *gin.Context) {
		clientType := c.GetHeader("X-Client-Type")
		if clientType != "mobile" {
			clientType = "web"
		}
		val, err := settings.Get(c.Request.Context(), "maintenance_"+clientType)
		if err == nil && val == "true" {
			c.JSON(http.StatusServiceUnavailable, gin.H{"message": "Service is under maintenance. Please try again later."})
			c.Abort()
			return
		}
		c.Next()
	}
}

// FeatureEnabled blocks requests when the given feature flag is set to "false".
// Fails open (does not block) if the settings DB is unavailable.
func FeatureEnabled(settings SettingsGetter, featureKey string) gin.HandlerFunc {
	return func(c *gin.Context) {
		val, err := settings.Get(c.Request.Context(), featureKey)
		if err == nil && val == "false" {
			c.JSON(http.StatusForbidden, gin.H{"message": "This feature is currently disabled."})
			c.Abort()
			return
		}
		c.Next()
	}
}
