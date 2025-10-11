use std::sync::Arc;

use axum::extract::Path;
use axum::response::IntoResponse as _;

use axum::Extension;
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
use crate::params::UserIdPathParams;
use crate::requests::Binary;
use crate::service::user::{RegisterRequest, SaltRequest, UploadUserAvatarRequest};
use crate::service::{self, ServiceError};

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
    State(ctx): State<Arc<Context>>,
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
    State(ctx): State<Arc<Context>>,
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
    State(ctx): State<Arc<Context>>,
    Json(request): Json<service::user::SaltRequest>,
) -> Response {
    match service::user::salt(&ctx, request).await {
        PostSaltResponse::Success(resp) => (StatusCode::OK, Json(resp)).into_response(),
        PostSaltResponse::UserNotFound => StatusCode::NOT_FOUND.into_response(),
        PostSaltResponse::InternalServerError => StatusCode::INTERNAL_SERVER_ERROR.into_response(),
    }
}

#[utoipa::path(
    post,
    path = "/api/user/upload-avatar",
    tag = "user",
    responses(
        (status = 200, description = "Avatar uploaded successfully", body = ()),
        (status = 400, description = "Bad request", body = String),
        (status = 401, description = "Missing or invalid JWT", body = String),
        (status = 500, description = "Internal server error", body = Option<String>),
    ),
    request_body(content_type = "multipart/form-data", content = UploadUserAvatarRequest),
    security(
        ("bearer_auth" = [])
    )
)]
async fn post_upload_user_avatar(
    State(ctx): State<Arc<Context>>,
    Extension(claims): Extension<Option<shared_items_lib::JwtClaims>>,
    multipart: axum::extract::Multipart,
) -> Response {
    let Some(claims) = claims else {
        tracing::warn!("post_upload_user_avatar: Missing JWT claims");
        return (StatusCode::UNAUTHORIZED, "Missing or invalid JWT").into_response();
    };
    match service::user::upload_user_avatar(&ctx, claims, multipart).await {
        Ok(()) => StatusCode::OK.into_response(),
        Err(ServiceError::UserExposedError {
            status_code,
            detail,
        }) => (status_code, detail).into_response(),
        Err(ServiceError::UserOpaqueError { anyhow_err }) => {
            tracing::error!("Internal server error: {anyhow_err}");
            StatusCode::INTERNAL_SERVER_ERROR.into_response()
        }
    }
}

#[utoipa::path(
    get,
    path = "/api/user/{user_id}/avatar",
    tag = "user",
    responses(
        (
            status = 200,
            description = "Successfully retrieved png avatar",
            body = Binary,
            content_type = "image/png"
        ),
        (
            status = 200,
            description = "Successfully retrieved jpeg avatar",
            body = Binary,
            content_type = "image/jpeg"
        ),
        (status = 500, description = "Internal server error", body = Option<String>),
    ),
    params(UserIdPathParams)
)]
async fn get_user_avatar(
    State(ctx): State<Arc<Context>>,
    Path(params): Path<UserIdPathParams>,
) -> Response {
    let UserIdPathParams { user_id } = params;
    let user_id: mnln_core_items::id::UserId = user_id.into();
    service::user::get_user_avatar(&ctx, user_id).await
}

fn user_routes(ctx: Arc<Context>) -> Router<Arc<Context>> {
    Router::new()
        .route("/register", post(post_register))
        .route("/login", post(post_login))
        .route("/salt", post(post_salt))
        .route(
            "/upload-avatar",
            post(post_upload_user_avatar).layer(axum::middleware::from_fn_with_state(
                ctx,
                crate::middleware::add_jwt_claims_extension,
            )),
        )
        .route("/{user_id}/avatar", axum::routing::get(get_user_avatar))
}

pub(in crate::requests::api) fn add_nested_routes(
    router: axum::Router<Arc<Context>>,
    ctx: Arc<Context>,
) -> axum::Router<Arc<Context>> {
    router.nest("/user", user_routes(ctx))
}
