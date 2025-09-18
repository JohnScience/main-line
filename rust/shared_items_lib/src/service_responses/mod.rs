/// Responses for user registration
#[derive(specta::Type)]
pub enum PostRegisterResponse {
    /// User registered successfully
    Success,
    /// User already exists
    AlreadyExists,
    /// Internal server error
    InternalServerError,
}

#[derive(specta::Type, serde::Serialize, utoipa::ToSchema)]
pub struct SaltResponseSuccess {
    pub salt: String,
}

/// Responses for retrieving user salt
#[derive(specta::Type)]
#[serde(tag = "kind")]
pub enum PostSaltResponse {
    /// Salt retrieved successfully
    Success(SaltResponseSuccess),
    /// User not found
    UserNotFound,
    /// Internal server error
    InternalServerError,
}
