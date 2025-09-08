use utoipa::OpenApi;
use utoipauto::utoipauto;

mod api;
mod general;

#[utoipauto(paths = "./backend/src")]
#[derive(OpenApi)]
#[openapi(
    tags(
        (name = "todo", description = "Todo management endpoints.")
    ),
)]
pub(crate) struct ApiDoc;

pub(crate) fn make_router<S>() -> axum::Router<S>
where
    S: Clone + Send + Sync + 'static,
{
    let router = axum::Router::new();
    let router = general::add_routes(router);
    let router = api::add_nested_routes(router);
    router.layer(axum::middleware::from_fn(crate::middleware::log_request))
}
