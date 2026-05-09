package handler

import (
	"errors"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/dto"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/service"
)

type SettingsHandler struct {
	settingsService *service.SettingsService
}

func NewSettingsHandler(settingsService *service.SettingsService) *SettingsHandler {
	return &SettingsHandler{settingsService: settingsService}
}

// Status godoc
// @Summary      Public system status (maintenance flags, feature toggles)
// @Tags         system
// @Produce      json
// @Success      200 {object} dto.StatusResponse
// @Router       /status [get]
func (h *SettingsHandler) Status(c *gin.Context) {
	settings, err := h.settingsService.GetAll(c.Request.Context())
	if err != nil {
		c.JSON(http.StatusOK, dto.StatusResponse{
			MaintenanceWeb:    false,
			MaintenanceMobile: false,
			FeatureGraph:      true,
		})
		return
	}
	c.JSON(http.StatusOK, dto.StatusResponse{
		MaintenanceWeb:    settings["maintenance_web"] == "true",
		MaintenanceMobile: settings["maintenance_mobile"] == "true",
		FeatureGraph:      settings["feature_graph"] != "false",
	})
}

// GetSettings godoc
// @Summary      Get all feature flags and maintenance settings
// @Tags         admin
// @Security     BearerAuth
// @Produce      json
// @Success      200 {object} dto.SettingsResponse
// @Failure      401 {object} dto.ErrorResponse
// @Failure      403 {object} dto.ErrorResponse
// @Router       /admin/settings [get]
func (h *SettingsHandler) GetSettings(c *gin.Context) {
	settings, err := h.settingsService.GetAll(c.Request.Context())
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"message": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"data": settings})
}

// UpdateSetting godoc
// @Summary      Update a feature flag or maintenance setting
// @Tags         admin
// @Security     BearerAuth
// @Accept       json
// @Produce      json
// @Param        key  path  string                   true  "Setting key: maintenance_web | maintenance_mobile | feature_graph"
// @Param        body body  dto.UpdateSettingRequest  true  "New value (true or false)"
// @Success      200 {object} map[string]string
// @Failure      400 {object} dto.ErrorResponse
// @Failure      401 {object} dto.ErrorResponse
// @Failure      403 {object} dto.ErrorResponse
// @Router       /admin/settings/{key} [put]
func (h *SettingsHandler) UpdateSetting(c *gin.Context) {
	key := c.Param("key")
	var req dto.UpdateSettingRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"message": err.Error()})
		return
	}
	if err := h.settingsService.Set(c.Request.Context(), key, req.Value); err != nil {
		if errors.Is(err, service.ErrInvalidSettingKey) {
			c.JSON(http.StatusBadRequest, gin.H{"message": "invalid setting key; valid keys: maintenance_web, maintenance_mobile, feature_graph"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"message": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"data": gin.H{key: req.Value}})
}
