use std::sync::Arc;

use axum::Router;

use crate::context::Context;

pub(crate) mod bff;
pub(crate) mod user;

fn api_routes(ctx: Arc<Context>) -> Router<Arc<Context>> {
    let router = Router::new();
    let router = user::add_nested_routes(router, ctx);
    bff::add_nested_routes(router)
}

pub(in crate::requests) fn add_nested_routes(
    router: Router<Arc<Context>>,
    ctx: Arc<Context>,
) -> Router<Arc<Context>> {
    router.nest("/api", api_routes(ctx))
}
