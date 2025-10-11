use std::sync::Arc;

use utoipa::{OpenApi, ToSchema};
use utoipauto::utoipauto;

use shared_items_lib::id::UserId;

use crate::context::Context;

mod api;
mod general;

#[derive(ToSchema)]
pub(crate) struct Binary {
    /// The uploaded file content
    #[schema(format = "binary")]
    #[allow(dead_code)]
    pub content: String, // Or Vec<u8> depending on your implementation
}

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
    components(schemas(UserId))
    modifiers(&SecurityAddon)
)]
pub struct ApiDoc;

macro_rules! make_trace_layer {
    () => {
        tower_http::trace::TraceLayer::new_for_http()
            .on_request(|request: &axum::http::Request<_>, _span: &tracing::Span| {
                tracing::info!(
                    "Received request: {} {}. Headers: {:?}",
                    request.method(),
                    request.uri(),
                    request.headers()
                );
            })
            .on_response(
                |response: &axum::http::Response<_>,
                 latency: std::time::Duration,
                 _span: &tracing::Span| {
                    let message = format!(
                        "Response generated: {} in {} ms. Headers: {:?}",
                        response.status(),
                        latency.as_millis(),
                        response.headers()
                    );

                    if response.status().is_success() {
                        tracing::info!(message);
                        return;
                    } else if response.status().is_client_error() {
                        tracing::warn!(message);
                        return;
                    } else if response.status().is_server_error() {
                        tracing::error!(message);
                        return;
                    }
                },
            )
    };
}

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
        .layer(make_trace_layer!())
        .layer(cors_layer)
        .with_state(ctx);
    Ok(router)
}
