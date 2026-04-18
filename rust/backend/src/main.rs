use axum::{Router, routing::get};
use opentelemetry::trace::TracerProvider as _;
use opentelemetry_otlp::SpanExporter;
use opentelemetry_sdk::trace::SdkTracerProvider;
use tracing::info;
use tracing_subscriber::{EnvFilter, layer::SubscriberExt, util::SubscriberInitExt};

const HEALTH_CHECK_OK: &str = r#"{"status": "ok"}"#;

/// Initialises a layered tracing subscriber:
///   - EnvFilter (reads RUST_LOG)
///   - JSON formatter (structured logs for Loki)
///   - OpenTelemetry layer (traces → OTLP gRPC, reads OTEL_EXPORTER_OTLP_ENDPOINT)
///
/// Returns the SdkTracerProvider so it can be shut down cleanly on exit.
fn init_tracing() -> SdkTracerProvider {
    let exporter = SpanExporter::builder()
        .with_tonic()
        .build()
        .expect("failed to build OTLP span exporter");

    // Resource::default() reads OTEL_SERVICE_NAME and OTEL_RESOURCE_ATTRIBUTES.
    let provider = SdkTracerProvider::builder()
        .with_batch_exporter(exporter)
        .build();

    let tracer = provider.tracer("backend");
    let otel_layer = tracing_opentelemetry::layer().with_tracer(tracer);

    let env_filter = EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info"));

    tracing_subscriber::registry()
        .with(env_filter)
        .with(tracing_subscriber::fmt::layer().json())
        .with(otel_layer)
        .init();

    provider
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let provider = init_tracing();

    info!("Starting main-line backend...");

    let port = std::env::var("PORT").unwrap_or_else(|_| "3000".to_string());
    let addr = format!("0.0.0.0:{port}");

    let app = Router::new()
        .route("/health-check", get(|| async { HEALTH_CHECK_OK }))
        .layer(tower_http::trace::TraceLayer::new_for_http());

    let listener = tokio::net::TcpListener::bind(&addr).await?;
    info!("Serving on {addr}");

    axum::serve(listener, app)
        .with_graceful_shutdown(shutdown_signal())
        .await?;

    // Flush pending spans before the process exits.
    provider.shutdown().ok();

    Ok(())
}

/// Waits for SIGTERM (Kubernetes pod termination) or SIGINT (Ctrl-C in dev).
/// In-flight requests are allowed to complete before the process exits.
async fn shutdown_signal() {
    #[cfg(unix)]
    {
        use tokio::signal::unix::{SignalKind, signal};
        let mut sigterm =
            signal(SignalKind::terminate()).expect("failed to register SIGTERM handler");
        tokio::select! {
            _ = sigterm.recv() => { info!("received SIGTERM, shutting down"); },
            _ = tokio::signal::ctrl_c() => { info!("received SIGINT, shutting down"); },
        }
    }
    #[cfg(not(unix))]
    {
        tokio::signal::ctrl_c()
            .await
            .expect("failed to register SIGINT handler");
        info!("received SIGINT, shutting down");
    }
}
