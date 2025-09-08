use axum::{
    Router,
    routing::{get, post},
};

async fn register() {}

fn user_routes<S>() -> Router<S>
where
    S: Clone + Send + Sync + 'static,
{
    Router::new().route("/register", post(register))
}

pub(in crate::requests::api) fn add_nested_routes<S>(router: axum::Router<S>) -> axum::Router<S>
where
    S: Clone + Send + Sync + 'static,
{
    router.nest("/user", user_routes())
}
