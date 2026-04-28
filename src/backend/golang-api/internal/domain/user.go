package domain

type User struct {
	ID               string `json:"id"`
	Email            string `json:"email"`
	FullName         string `json:"full_name"`
	SubscriptionTier string `json:"subscription_tier"`
	Role             string `json:"role"`
	PasswordHash     string `json:"-"`
}
