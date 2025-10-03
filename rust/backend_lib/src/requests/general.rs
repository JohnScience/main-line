use utoipa::OpenApi as _;

use axum::routing::get;
use utoipa_swagger_ui::SwaggerUi;

use crate::requests::ApiDoc;

const HEALTH_CHECK_OK: &str = r#"{
    "status": "ok"
}
"#;

#[utoipa::path(
    get,
    path = "/supported-img-formats",
    tag = "user",
    responses(
        (status = 200, description = "Supported image formats (as in <https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/accept>) retrieved successfully", body = String),
        (status = 500, description = "Internal server error", body = ()),
    )
)]
async fn get_supported_img_formats() -> &'static str {
    browser_supported_img_format::BrowserSupportedImgFormat::accept_str()
}

pub(in crate::requests) fn add_routes<S>(router: axum::Router<S>) -> axum::Router<S>
where
    S: Clone + Send + Sync + 'static,
{
    router
        .route("/health-check", get(|| async { HEALTH_CHECK_OK }))
        .route("/supported-img-formats", get(get_supported_img_formats))
        .merge(SwaggerUi::new("/swagger-ui").url("/api-docs/openapi.json", ApiDoc::openapi()))
}
