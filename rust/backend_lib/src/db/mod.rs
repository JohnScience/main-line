use std::ops::Deref;

use tracing::info;

use crate::context::env::PgEnv;

pub(crate) mod id;
pub(crate) mod user;

#[derive(Clone)]
pub struct Db {
    pub(crate) pool: sqlx::PgPool,
}

impl Db {
    fn database_url(pg_env: &PgEnv) -> String {
        let PgEnv {
            host,
            user,
            password,
            port,
            db_name,
        } = pg_env;
        format!("postgres://{user}:{password}@{host}:{port}/{db_name}")
    }

    pub(crate) async fn new(pg_env: &PgEnv) -> anyhow::Result<Self> {
        let url: String = Self::database_url(pg_env);
        let pool = sqlx::postgres::PgPoolOptions::new()
            .max_connections(5)
            .connect(&url)
            .await?;
        let db = Db { pool };

        db.test().await?;

        sqlx::migrate!("../../migrations").run(&db.pool).await?;

        Ok(db)
    }

    pub(crate) async fn test(&self) -> anyhow::Result<()> {
        // Run a simple math query to test the connection and math
        let row: (i32,) = sqlx::query_as("SELECT 2 + 2").fetch_one(&self.pool).await?;
        anyhow::ensure!(row.0 == 4, "PostgreSQL math test failed: 2 + 2 != 4");
        info!("PostgreSQL math test succeeded");
        Ok(())
    }
}

impl Deref for Db {
    type Target = sqlx::PgPool;

    fn deref(&self) -> &Self::Target {
        &self.pool
    }
}
