use axum::{Router, extract::Json, routing::post};
use tracing::{debug, info};

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
        (status = 400, description = "Bad request"),
    ),
    request_body = RegisterRequest,
)]
#[axum::debug_handler]
async fn post_register(Json(req): Json<RegisterRequest>) {
    let RegisterRequest {
        username,
        password_hash,
    } = req;
    debug!(
        "TODO: add registration logic for user `{username}` with password hash `{password_hash}`"
    );
}

fn user_routes<S>() -> Router<S>
where
    S: Clone + Send + Sync + 'static,
{
    Router::new().route("/register", post(post_register))
}

pub(in crate::requests::api) fn add_nested_routes<S>(router: axum::Router<S>) -> axum::Router<S>
where
    S: Clone + Send + Sync + 'static,
{
    router.nest("/user", user_routes())
}
