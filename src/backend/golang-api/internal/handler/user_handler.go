package handler

import (
	"errors"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/dto"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/repository/postgres"
	"golang.org/x/crypto/bcrypt"
)

type UserHandler struct {
	userRepo        *postgres.UserRepository
	profileRepo     *postgres.UserProfileRepository
}

func NewUserHandler(userRepo *postgres.UserRepository, profileRepo *postgres.UserProfileRepository) *UserHandler {
	return &UserHandler{
		userRepo:    userRepo,
		profileRepo: profileRepo,
	}
}

// GetProfile godoc
// @Summary      Get current user's profile information
// @Tags         user
// @Security     BearerAuth
// @Produce      json
// @Success      200 {object} dto.GetProfileResponse
// @Failure      401 {object} dto.ErrorResponse
// @Failure      404 {object} dto.ErrorResponse
// @Router       /user/profile [get]
func (h *UserHandler) GetProfile(c *gin.Context) {
	userID, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"message": "user_id not found in context"})
		return
	}
	userIDStr := userID.(string)

	user, err := h.userRepo.FindByID(c.Request.Context(), userIDStr)
	if err != nil {
		if errors.Is(err, postgres.ErrNotFound) {
			c.JSON(http.StatusNotFound, gin.H{"message": "user not found"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"message": err.Error()})
		return
	}

	var profileData dto.ProfileData
	profile, err := h.profileRepo.FindByUserID(c.Request.Context(), userIDStr)
	if err != nil {
		if errors.Is(err, postgres.ErrNotFound) {
			profileData = dto.ProfileData{
				JobRole:      nil,
				Technologies: []string{},
				Location:     nil,
				Bio:          nil,
			}
		} else {
			c.JSON(http.StatusInternalServerError, gin.H{"message": err.Error()})
			return
		}
	} else {
		if profile.Technologies == nil {
			profile.Technologies = []string{}
		}
		profileData = dto.ProfileData{
			JobRole:      profile.JobRole,
			Technologies: profile.Technologies,
			Location:     profile.Location,
			Bio:          profile.Bio,
		}
	}

	c.JSON(http.StatusOK, dto.GetProfileResponse{
		User: dto.ProfileUserData{
			ID:       user.ID,
			Email:    user.Email,
			FullName: user.FullName,
		},
		Profile: profileData,
	})
}

// UpdateProfile godoc
// @Summary      Update current user's profile information
// @Tags         user
// @Security     BearerAuth
// @Accept       json
// @Produce      json
// @Param        body body dto.UpdateProfileRequest true "Updated profile data"
// @Success      200 {object} dto.UpdateProfileResponse
// @Failure      400 {object} dto.ErrorResponse
// @Failure      401 {object} dto.ErrorResponse
// @Failure      404 {object} dto.ErrorResponse
// @Router       /user/profile [put]
func (h *UserHandler) UpdateProfile(c *gin.Context) {
	userID, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"message": "user_id not found in context"})
		return
	}
	userIDStr := userID.(string)

	var req dto.UpdateProfileRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"message": err.Error()})
		return
	}

	var passwordHash *string
	if req.Password != nil {
		hash, err := bcrypt.GenerateFromPassword([]byte(*req.Password), bcrypt.DefaultCost)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"message": "failed to hash password"})
			return
		}
		s := string(hash)
		passwordHash = &s
	}

	currentUser, err := h.userRepo.FindByID(c.Request.Context(), userIDStr)
	if err != nil {
		if errors.Is(err, postgres.ErrNotFound) {
			c.JSON(http.StatusNotFound, gin.H{"message": "user not found"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"message": err.Error()})
		return
	}

	user, err := h.userRepo.UpdateUser(c.Request.Context(), userIDStr, req.FullName, passwordHash, currentUser.Role, currentUser.Status)
	if err != nil {
		if errors.Is(err, postgres.ErrNotFound) {
			c.JSON(http.StatusNotFound, gin.H{"message": "user not found"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"message": err.Error()})
		return
	}

	profile, err := h.profileRepo.UpdateProfile(c.Request.Context(), userIDStr, req.JobRole, req.Technologies, req.Location, req.Bio)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"message": err.Error()})
		return
	}

	if profile.Technologies == nil {
		profile.Technologies = []string{}
	}
	c.JSON(http.StatusOK, dto.UpdateProfileResponse{
		User: dto.ProfileUserData{
			ID:       user.ID,
			Email:    user.Email,
			FullName: user.FullName,
		},
		Profile: dto.ProfileData{
			JobRole:      profile.JobRole,
			Technologies: profile.Technologies,
			Location:     profile.Location,
			Bio:          profile.Bio,
		},
	})
}
