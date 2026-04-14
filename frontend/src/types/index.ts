export interface User {
	user_id: string;
	email: string | null;
	role: "student" | "admin";
}

export interface AuthTokens {
	access_token: string;
	refresh_token: string;
	token_type: string;
}

export interface ApiKey {
	id: string;
	key_prefix: string;
	name: string;
	is_active: boolean;
	expires_at: string | null;
	created_at: string;
}

export interface ApiKeyGenerated {
	id: string;
	key: string;
	key_prefix: string;
	name: string;
}

export interface HealthResponse {
	status: string;
	service: string;
}
