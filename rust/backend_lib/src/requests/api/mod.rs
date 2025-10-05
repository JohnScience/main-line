use std::sync::Arc;

use axum::Router;

use crate::context::Context;

pub(crate) mod user;

fn api_routes(ctx: Arc<Context>) -> Router<Arc<Context>> {
    let router = Router::new();
    user::add_nested_routes(router, ctx)
}

pub(in crate::requests) fn add_nested_routes(
    router: Router<Arc<Context>>,
    ctx: Arc<Context>,
) -> Router<Arc<Context>> {
    router.nest("/api", api_routes(ctx))
}
