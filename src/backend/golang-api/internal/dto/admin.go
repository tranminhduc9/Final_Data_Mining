package dto

type UpdateSettingRequest struct {
	Value string `json:"value" binding:"required,oneof=true false"`
}

type AlterUserRequest struct {
	FullName string  `json:"full_name" binding:"required"`
	Password *string `json:"password"  binding:"omitempty,min=8"`
	Role     string  `json:"role"      binding:"required,oneof=admin user"`
	Status   string  `json:"status"    binding:"required,oneof=active blocked"`
}

type InsertUserRequest struct {
	FullName string `json:"full_name" binding:"required"`
	Email    string `json:"email"     binding:"required,email"`
	Password string `json:"password"  binding:"required,min=8"`
	Role     string `json:"role"      binding:"required,oneof=admin user"`
	Status   string `json:"status"    binding:"required,oneof=active blocked"`
}
