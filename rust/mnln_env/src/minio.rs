use anyhow::Context as _;
use std::env;

#[derive(Debug, Clone)]
pub struct MinioEnv {
    pub user: String,
    pub password: String,
    pub host: String,
    pub port: String,
    pub avatar_bucket: String,
}

impl MinioEnv {
    pub(crate) fn from_env() -> anyhow::Result<Self> {
        let host = env::var("MINIO_HOST").context("Missing MINIO_HOST")?;
        let port = env::var("MINIO_PORT").context("Missing MINIO_PORT")?;
        let user = env::var("MINIO_ROOT_USER").context("Missing MINIO_USER")?;
        let password = env::var("MINIO_ROOT_PASSWORD").context("Missing MINIO_PASSWORD")?;
        let avatar_bucket =
            env::var("MINIO_AVATAR_BUCKET").context("Missing MINIO_AVATAR_BUCKET")?;
        Ok(MinioEnv {
            host,
            port,
            user,
            password,
            avatar_bucket,
        })
    }

    pub(crate) fn dev() -> anyhow::Result<Self> {
        let repo_root: String = git_repo_root::git_repo_root()?;

        let repo_root: std::path::PathBuf = repo_root.into();
        let minio_secrets_path = repo_root.join("secrets").join("minio_config.env");
        let minio_buckets_path = repo_root.join("secrets").join("minio_buckets.env");

        dotenv::from_path(minio_secrets_path)?;
        dotenv::from_path(minio_buckets_path)?;
        let host = "localhost".to_string();
        let port = "9000".to_string();
        let user = env::var("MINIO_ROOT_USER").context("Missing MINIO_USER")?;
        let password = env::var("MINIO_ROOT_PASSWORD").context("Missing MINIO_PASSWORD")?;
        let avatar_bucket =
            env::var("MINIO_AVATAR_BUCKET").context("Missing MINIO_AVATAR_BUCKET")?;
        Ok(MinioEnv {
            host,
            port,
            user,
            password,
            avatar_bucket,
        })
    }
}
