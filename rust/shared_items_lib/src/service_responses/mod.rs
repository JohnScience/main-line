use crate::JwtString;

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
pub struct PostLoginResponseSuccess {
    pub jwt: JwtString,
}

#[derive(specta::Type)]
#[serde(tag = "kind")]
pub enum PostLoginResponse {
    /// Login successful
    Success(PostLoginResponseSuccess),
    /// Invalid credentials
    InvalidCredentials,
    /// Internal server error
    InternalServerError,
}

#[derive(specta::Type, serde::Serialize, utoipa::ToSchema)]
pub struct PostSaltResponseSuccess {
    pub salt: String,
}

/// Responses for retrieving user salt
#[derive(specta::Type)]
#[serde(tag = "kind")]
pub enum PostSaltResponse {
    /// Salt retrieved successfully
    Success(PostSaltResponseSuccess),
    /// User not found
    UserNotFound,
    /// Internal server error
    InternalServerError,
}

#[derive(specta::Type)]
pub struct LikelySuccess<T> {
    pub value: T,
}

#[derive(specta::Type)]
#[serde(tag = "kind")]
pub enum LikelyResponse<T> {
    Success(LikelySuccess<T>),
    InternalServerError,
}

#[derive(specta::Type, serde::Serialize, utoipa::ToSchema)]
pub struct UserPageData {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub avatar_url: Option<String>,
    pub username: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub email: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub chess_dot_com_profile: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub lichess_profile: Option<String>,
}

#[derive(specta::Type)]
#[serde(tag = "kind")]
pub enum GetUserPageDataResponse {
    Success(UserPageData),
    NotFound,
    InternalServerError,
}
