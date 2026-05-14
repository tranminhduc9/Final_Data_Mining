package dto

type GetProfileResponse struct {
	User    ProfileUserData    `json:"user"`
	Profile ProfileData        `json:"profile"`
}

type ProfileUserData struct {
	ID       string `json:"id"`
	Email    string `json:"email"`
	FullName string `json:"full_name"`
}

type ProfileData struct {
	JobRole      *string  `json:"job_role"`
	Technologies []string `json:"technologies"`
	Location     *string  `json:"location"`
	Bio          *string  `json:"bio"`
}

type UpdateProfileRequest struct {
	FullName     string   `json:"full_name" binding:"required"`
	Password     *string  `json:"password" binding:"omitempty,min=8"`
	JobRole      *string  `json:"job_role" binding:"omitempty"`
	Technologies []string `json:"technologies" binding:"omitempty"`
	Location     *string  `json:"location" binding:"omitempty"`
	Bio          *string  `json:"bio" binding:"omitempty"`
}

type UpdateProfileResponse struct {
	User    ProfileUserData `json:"user"`
	Profile ProfileData     `json:"profile"`
}
