use anyhow::Context as _;
use std::env;

#[derive(Debug, Clone)]
pub(crate) struct PgEnv {
    pub(crate) host: String,
    pub(crate) user: String,
    pub(crate) password: String,
    pub(crate) port: u16,
    pub(crate) db_name: String,
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

    pub(crate) fn dev() -> Self {
        PgEnv {
            // host is the name of the Docker service in docker-compose.yml
            host: "db".into(),
            user: "tester".into(),
            password: "tester".into(),
            port: 5432,
            db_name: "tester".into(),
        }
    }
}

#[derive(Debug, Clone)]
pub(crate) struct Env {
    pub(crate) pg: PgEnv,
}

impl Env {
    pub(crate) fn from_env() -> anyhow::Result<Self> {
        let pg = PgEnv::from_env()?;
        Ok(Env { pg })
    }
}
