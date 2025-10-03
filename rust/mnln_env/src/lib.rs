use anyhow::Context as _;
use std::env;

mod minio;
mod pg;

use minio::MinioEnv;
pub use pg::PgEnv;

#[derive(Debug, Clone)]
pub struct Env {
    pub base_frontend_url: String,
    /// <https://www.jwt.io/introduction>
    pub jwt_signing_key: String,
    /// <https://www.postgresql.org/>
    pub pg: PgEnv,
    /// <https://github.com/minio/minio>
    pub minio: MinioEnv,
}

impl Env {
    pub fn from_env() -> anyhow::Result<Self> {
        let base_frontend_url =
            env::var("BASE_FRONTEND_URL").context("Missing BASE_FRONTEND_URL")?;
        let jwt_signing_key = env::var("JWT_SIGNING_KEY").context("Missing JWT_SIGNING_KEY")?;
        let pg = PgEnv::from_env()?;
        let minio = MinioEnv::from_env()?;
        Ok(Env {
            pg,
            base_frontend_url,
            jwt_signing_key,
            minio,
        })
    }

    pub fn dev() -> anyhow::Result<Self> {
        let repo_root = git_repo_root::git_repo_root()?;
        let repo_root: std::path::PathBuf = repo_root.into();
        let jwt_secrets_path = repo_root.join("secrets").join("jwt_signing_key.env");

        let base_frontend_url = "http://localhost:3001".to_string();
        dotenv::from_path(jwt_secrets_path)?;
        let jwt_signing_key = env::var("JWT_SIGNING_KEY").context("Missing JWT_SIGNING_KEY")?;
        let pg = PgEnv::dev()?;
        let minio = MinioEnv::dev()?;
        Ok(Env {
            pg,
            base_frontend_url,
            jwt_signing_key,
            minio,
        })
    }
}
