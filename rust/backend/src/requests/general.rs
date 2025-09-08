use axum::routing::get;

const HEALTH_CHECK_OK: &str = r#"{
    "status": "ok"
}
"#;

pub(in crate::requests) fn add_routes<S>(router: axum::Router<S>) -> axum::Router<S>
where
    S: Clone + Send + Sync + 'static,
{
    router.route("/health-check", get(|| async { HEALTH_CHECK_OK }))
}
