use tracing::info;

use backend_lib::{Context, make_router};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt::init();

    info!("Starting main-line backend...");

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await?;

    let ctx = Context::new().await?;
    let ctx = std::sync::Arc::new(ctx);

    let app = make_router(ctx)?;

    info!("Serving the app...");

    axum::serve(listener, app).await?;

    Ok(())
}
