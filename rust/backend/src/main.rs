use tracing::info;

pub(crate) mod context;
pub(crate) mod db;
pub(crate) mod middleware;

mod requests;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt::init();

    info!("Starting main-line backend...");

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await?;

    let env = context::env::Env::from_env()?;
    let db = db::Db::new(&env.pg).await?;

    let ctx = context::Context { env, db };

    let app = requests::make_router(ctx);

    info!("Serving the app...");

    axum::serve(listener, app).await?;

    Ok(())
}
