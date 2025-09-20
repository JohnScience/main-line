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
}

#[derive(Debug, Clone)]
pub struct Env {
    pub base_frontend_url: String,
    pub pg: PgEnv,
}

impl Env {
    pub(crate) fn from_env() -> anyhow::Result<Self> {
        let pg = PgEnv::from_env()?;
        let base_frontend_url =
            env::var("BASE_FRONTEND_URL").context("Missing BASE_FRONTEND_URL")?;
        Ok(Env {
            pg,
            base_frontend_url,
        })
    }
}
