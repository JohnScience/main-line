use tracing::info;

pub(crate) mod context;
pub(crate) mod db;
pub(crate) mod middleware;

mod requests;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt::init();

    info!("Starting main-line backend...");

    let app = requests::make_router();

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await?;
    let context = context::Context {
        env: context::env::Env::from_env()?,
    };
    let db = db::Db::new(&context.env.pg).await?;

    db.test().await?;

    info!("Serving the app...");

    axum::serve(listener, app).await?;

    Ok(())
}
