use axum::response::IntoResponse as _;

use axum::{
    Router,
    extract::{Json, State},
    http::StatusCode,
    response::Response,
    routing::post,
};

use crate::{context::Context, db};

#[derive(serde::Deserialize, utoipa::ToSchema)]
pub(crate) struct RegisterRequest {
    username: String,
    password_hash: String,
}

#[utoipa::path(
    post,
    path = "/api/user/register",
    tag = "user",
    responses(
        (status = 200, description = "User registered successfully"),
        (status = 409, description = "User already exists"),
        (status = 500, description = "Internal server error"),
    ),
    request_body = RegisterRequest,
)]
#[axum::debug_handler]
async fn post_register(State(ctx): State<Context>, Json(req): Json<RegisterRequest>) -> Response {
    let RegisterRequest {
        username,
        password_hash,
    } = req;
    match db::user::register(&ctx.db, &username, &password_hash).await {
        db::user::register::Output::Success { user_id: _ } => (StatusCode::OK).into_response(),
        db::user::register::Output::AlreadyExists => (StatusCode::CONFLICT).into_response(),
        db::user::register::Output::UnknownError { err: _ } => {
            (StatusCode::INTERNAL_SERVER_ERROR).into_response()
        }
    }
}

fn user_routes() -> Router<Context> {
    Router::new().route("/register", post(post_register))
}

pub(in crate::requests::api) fn add_nested_routes(
    router: axum::Router<Context>,
) -> axum::Router<Context> {
    router.nest("/user", user_routes())
}
