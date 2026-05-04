package domain

type User struct {
	ID               string `json:"id"`
	Email            string `json:"email"`
	FullName         string `json:"full_name"`
	SubscriptionTier string `json:"subscription_tier"`
	Role             string `json:"role"`
	Status           string `json:"status"`
	PasswordHash     string `json:"-"`
}

type UserProfile struct {
	UserID       string   `json:"user_id"`
	JobRole      *string  `json:"job_role"`
	Technologies []string `json:"technologies"`
	Location     *string  `json:"location"`
	Bio          *string  `json:"bio"`
}
