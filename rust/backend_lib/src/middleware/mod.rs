use std::sync::Arc;

use axum::{
    extract::{Request, State},
    http::StatusCode,
    response::IntoResponse,
};
use tracing::info;

use crate::{Context, util};

pub(crate) async fn log_request(
    req: Request,
    next: axum::middleware::Next,
) -> axum::response::Response {
    info!(
        "Received request: {} {}.\nHeaders: {:?}",
        req.method(),
        req.uri(),
        req.headers()
    );
    next.run(req).await
}

pub(crate) async fn add_jwt_claims_extension(
    State(ctx): State<Arc<Context>>,
    mut req: Request,
    next: axum::middleware::Next,
) -> axum::response::Response {
    let authorization_header = req
        .headers()
        .get(axum::http::header::AUTHORIZATION)
        .and_then(|header_value| header_value.to_str().ok());

    let Some(authorization_header) = authorization_header else {
        req.extensions_mut()
            .insert(None::<shared_items_lib::JwtClaims>);
        return next.run(req).await;
    };

    let Some(token) = authorization_header.strip_prefix("Bearer ") else {
        req.extensions_mut()
            .insert(None::<shared_items_lib::JwtClaims>);
        return next.run(req).await;
    };

    let claims = match util::verify_jwt(token, &ctx) {
        Ok(claims) => claims,
        Err(err) => {
            tracing::error!("Failed to verify JWT: {err}");
            // reject with 401 Unauthorized?

            return StatusCode::UNAUTHORIZED.into_response();
        }
    };

    tracing::info!("Verified JWT claims: {claims:?}");

    req.extensions_mut().insert(Some(claims));

    // You can add the extracted claims to the request extensions if needed
    next.run(req).await
}
