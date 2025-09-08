use utoipa::OpenApi as _;

use axum::routing::get;
use utoipa_swagger_ui::SwaggerUi;

use crate::requests::ApiDoc;

const HEALTH_CHECK_OK: &str = r#"{
    "status": "ok"
}
"#;

pub(in crate::requests) fn add_routes<S>(router: axum::Router<S>) -> axum::Router<S>
where
    S: Clone + Send + Sync + 'static,
{
    router
        .route("/health-check", get(|| async { HEALTH_CHECK_OK }))
        .merge(SwaggerUi::new("/swagger-ui").url("/api-docs/openapi.json", ApiDoc::openapi()))
}
