use utoipa::OpenApi;
use utoipauto::utoipauto;

use crate::context::Context;

mod api;
mod general;

#[utoipauto(paths = "./backend_lib/src")]
#[derive(OpenApi)]
#[openapi(
    tags(
        (name = "todo", description = "Todo management endpoints.")
    ),
)]
pub struct ApiDoc;

pub fn make_router(ctx: Context) -> axum::Router {
    let router = axum::Router::new();
    let router = general::add_routes(router);
    let router = api::add_nested_routes(router);
    router
        .layer(axum::middleware::from_fn(crate::middleware::log_request))
        .with_state(ctx)
}
