use axum::response::IntoResponse as _;

use axum::{
    Router,
    extract::{Json, State},
    http::StatusCode,
    response::Response,
    routing::post,
};

use shared_items_lib::service_responses::{
    PostLoginResponse, PostLoginResponseSuccess, PostRegisterResponse, PostSaltResponse,
    PostSaltResponseSuccess,
};

use crate::context::Context;
use crate::service;
use crate::service::user::{RegisterRequest, SaltRequest};

#[utoipa::path(
    post,
    path = "/api/user/register",
    tag = "user",
    responses(
        (status = 200, description = "User registered successfully", body = ()),
        (status = 409, description = "User already exists", body = ()),
        (status = 500, description = "Internal server error", body = ()),
    ),
    request_body = RegisterRequest,
)]
#[axum::debug_handler]
async fn post_register(
    State(ctx): State<Context>,
    Json(request): Json<RegisterRequest>,
) -> Response {
    match service::user::register(&ctx, request).await {
        PostRegisterResponse::Success => StatusCode::OK.into_response(),
        PostRegisterResponse::AlreadyExists => StatusCode::CONFLICT.into_response(),
        PostRegisterResponse::InternalServerError => {
            StatusCode::INTERNAL_SERVER_ERROR.into_response()
        }
    }
}

#[utoipa::path(
    post,
    path = "/api/user/login",
    tag = "user",
    responses(
        (status = 200, description = "Login successful", body = PostLoginResponseSuccess),
        (status = 401, description = "Invalid credentials", body = ()),
        (status = 500, description = "Internal server error", body = ()),
    ),
    request_body = service::user::LoginRequest,
)]
async fn post_login(
    State(ctx): State<Context>,
    Json(request): Json<service::user::LoginRequest>,
) -> Response {
    match service::user::login(&ctx, request).await {
        PostLoginResponse::Success(resp) => (StatusCode::OK, Json(resp)).into_response(),
        PostLoginResponse::InvalidCredentials => StatusCode::UNAUTHORIZED.into_response(),
        PostLoginResponse::InternalServerError => StatusCode::INTERNAL_SERVER_ERROR.into_response(),
    }
}

#[utoipa::path(
    post,
    path = "/api/user/salt",
    tag = "user",
    responses(
        (status = 200, description = "User salt retrieved successfully", body = PostSaltResponseSuccess),
        (status = 404, description = "User not found", body = ()),
        (status = 500, description = "Internal server error", body = ()),
    ),
    request_body = SaltRequest,
)]
async fn post_salt(
    State(ctx): State<Context>,
    Json(request): Json<service::user::SaltRequest>,
) -> Response {
    match service::user::salt(&ctx, request).await {
        PostSaltResponse::Success(resp) => (StatusCode::OK, Json(resp)).into_response(),
        PostSaltResponse::UserNotFound => StatusCode::NOT_FOUND.into_response(),
        PostSaltResponse::InternalServerError => StatusCode::INTERNAL_SERVER_ERROR.into_response(),
    }
}

fn user_routes() -> Router<Context> {
    Router::new()
        .route("/register", post(post_register))
        .route("/login", post(post_login))
        .route("/salt", post(post_salt))
}

pub(in crate::requests::api) fn add_nested_routes(
    router: axum::Router<Context>,
) -> axum::Router<Context> {
    router.nest("/user", user_routes())
}
