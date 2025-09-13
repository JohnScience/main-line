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
