use axum::extract::Request;
use tracing::info;

pub(crate) async fn log_request(
    req: Request,
    next: axum::middleware::Next,
) -> axum::response::Response {
    info!("Received request: {} {}", req.method(), req.uri());
    next.run(req).await
}
