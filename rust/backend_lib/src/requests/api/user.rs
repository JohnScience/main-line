use axum::response::IntoResponse as _;

use axum::{
    Router,
    extract::{Json, State},
    http::StatusCode,
    response::Response,
    routing::post,
};

use shared_items_lib::service_responses::{
    PostRegisterResponse, PostSaltResponse, SaltResponseSuccess,
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
    path = "/api/user/salt",
    tag = "user",
    responses(
        (status = 200, description = "User salt retrieved successfully", body = SaltResponseSuccess),
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
        .route("/salt", post(post_salt))
}

pub(in crate::requests::api) fn add_nested_routes(
    router: axum::Router<Context>,
) -> axum::Router<Context> {
    router.nest("/user", user_routes())
}
