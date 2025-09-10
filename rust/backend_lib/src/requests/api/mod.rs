use axum::Router;

use crate::context::Context;

pub(crate) mod user;

fn api_routes() -> Router<Context> {
    let router = Router::new();
    user::add_nested_routes(router)
}

pub(in crate::requests) fn add_nested_routes(router: Router<Context>) -> Router<Context> {
    router.nest("/api", api_routes())
}
