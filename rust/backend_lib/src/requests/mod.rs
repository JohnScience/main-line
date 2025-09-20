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

pub fn make_router(ctx: Context) -> anyhow::Result<axum::Router> {
    let router = axum::Router::new();
    let router = general::add_routes(router);
    let router = api::add_nested_routes(router);

    let base_frontend_url: axum::http::HeaderValue = ctx.env.base_frontend_url.parse()?;

    let cors_layer = tower_http::cors::CorsLayer::new()
        .allow_origin(base_frontend_url)
        .allow_methods(tower_http::cors::Any)
        .allow_headers([
            axum::http::header::CONTENT_TYPE,
            axum::http::header::AUTHORIZATION,
        ]);

    let router = router
        .layer(axum::middleware::from_fn(crate::middleware::log_request))
        .layer(cors_layer)
        .with_state(ctx);
    Ok(router)
}
