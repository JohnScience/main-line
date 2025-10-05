use std::sync::Arc;

use utoipa::OpenApi;
use utoipauto::utoipauto;

use crate::context::Context;

mod api;
mod general;

struct SecurityAddon;

impl utoipa::Modify for SecurityAddon {
    fn modify(&self, openapi: &mut utoipa::openapi::OpenApi) {
        if openapi.components.is_none() {
            openapi.components = Some(utoipa::openapi::Components::new());
        }

        openapi.components.as_mut().unwrap().add_security_scheme(
            "bearerAuth",
            utoipa::openapi::security::SecurityScheme::Http(
                utoipa::openapi::security::HttpBuilder::new()
                    .scheme(utoipa::openapi::security::HttpAuthScheme::Bearer)
                    .bearer_format("JWT")
                    .build(),
            ),
        );
    }
}

#[utoipauto(paths = "./backend_lib/src")]
#[derive(OpenApi)]
#[openapi(
    tags(
        (name = "todo", description = "Todo management endpoints.")
    ),
    modifiers(&SecurityAddon)
)]
pub struct ApiDoc;

pub fn make_router(ctx: Arc<Context>) -> anyhow::Result<axum::Router> {
    let router = axum::Router::new();
    let router = general::add_routes(router);
    let router = api::add_nested_routes(router, ctx.clone());

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
