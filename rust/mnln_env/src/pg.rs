use anyhow::Context as _;
use std::env;

#[derive(Debug, Clone)]
pub struct PgEnv {
    pub host: String,
    pub user: String,
    pub password: String,
    pub port: u16,
    pub db_name: String,
}

impl PgEnv {
    pub(crate) fn from_env() -> anyhow::Result<Self> {
        let host = env::var("POSTGRES_HOST").context("Missing POSTGRES_HOST")?;
        let user = env::var("POSTGRES_USER").context("Missing POSTGRES_USER")?;
        let password = env::var("POSTGRES_PASSWORD").context("Missing POSTGRES_PASSWORD")?;
        let port = env::var("POSTGRES_PORT")
            .context("Missing POSTGRES_PORT")?
            .parse::<u16>()
            .context("Couldn't parse POSTGRES_PORT as u16")?;
        let db_name = env::var("POSTGRES_DB").context("Missing POSTGRES_DB")?;
        Ok(PgEnv {
            host,
            user,
            password,
            port,
            db_name,
        })
    }

    // This function is meant to be used for tests happening
    // as a part of local development only.
    pub(crate) fn dev() -> anyhow::Result<Self> {
        let repo_root: String = git_repo_root::git_repo_root()?;

        let repo_root: std::path::PathBuf = repo_root.into();
        let pg_secrets_path = repo_root.join("secrets").join("pg_config.env");

        let host = "localhost".to_string();
        let port = 5432_u16;

        dotenv::from_path(pg_secrets_path)?;
        let user = env::var("POSTGRES_USER").context("Missing POSTGRES_USER")?;
        let password = env::var("POSTGRES_PASSWORD").context("Missing POSTGRES_PASSWORD")?;
        let db_name = env::var("POSTGRES_DB").context("Missing POSTGRES_DB")?;
        Ok(PgEnv {
            host,
            user,
            password,
            port,
            db_name,
        })
    }
}
