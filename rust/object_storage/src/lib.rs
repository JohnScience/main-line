use anyhow::Context as _;

use awsregion::Region;
use futures_core::stream::Stream;
use s3::{Bucket, CreateBucketOptions};

use browser_supported_img_format::BrowserSupportedImgFormat;
use mnln_core_items::Timestamp;
use mnln_core_items::id::UserId;
use mnln_env::Env;

fn creds(env: &Env) -> anyhow::Result<awscreds::Credentials> {
    let creds = awscreds::Credentials::new(
        Some(&env.minio.user),
        Some(&env.minio.password),
        None,
        None,
        None,
    )?;
    Ok(creds)
}

fn default_region(env: &Env) -> Region {
    let endpoint = format!("https://{}:{}", env.minio.host, env.minio.port);
    // Any region works for minio
    Region::Custom {
        region: "us-east-1".to_string(),
        endpoint,
    }
}

pub async fn init(env: &Env) -> anyhow::Result<()> {
    let avatar_bucket = avatar_bucket(env).await?;
    if !avatar_bucket.exists().await? {
        tracing::info!(
            "Avatar bucket `{}` does not exist. Creating...",
            &env.minio.avatar_bucket
        );
        let mut opts =
            CreateBucketOptions::new(&env.minio.avatar_bucket, default_region(env), creds(env)?);
        opts.path_style = true;
        opts.set_dangerous_config(true, true);
        let _create_bucket_response = Bucket::create_with_opts(opts).await?;
        tracing::info!("Created avatar bucket: `{}`", &env.minio.avatar_bucket);
    } else {
        tracing::info!(
            "Avatar bucket `{}` already exists. Skipping creation.",
            &env.minio.avatar_bucket
        );
    };
    Ok(())
}

async fn avatar_bucket(env: &Env) -> anyhow::Result<Box<Bucket>> {
    let creds = creds(env)?;
    let bucket = Bucket::new(
        &env.minio.avatar_bucket.as_str(),
        default_region(env),
        creds,
    )?
    .set_dangereous_config(true, true)?
    .with_path_style();
    Ok(bucket)
}

// TODO: implement extras, such as S3Key and S3Path
fn avatar_key(user_id: UserId, format: BrowserSupportedImgFormat) -> String {
    let timestamp: Timestamp = mnln_time::now();
    format!("avatars/{user_id}/{timestamp}.{}", format.ext())
}

pub async fn save_avatar<B, E>(
    env: &Env,
    user_id: UserId,
    avatar: B,
    avatar_format: BrowserSupportedImgFormat,
) -> anyhow::Result<String>
where
    B: Stream<Item = Result<bytes::Bytes, E>> + Send + Unpin,
    E: Into<std::io::Error>,
{
    let bucket = avatar_bucket(env)
        .await
        .context("Failed to get avatar bucket")?;
    let key = avatar_key(user_id, avatar_format);

    let mut reader = tokio_util::io::StreamReader::new(avatar);
    bucket
        .put_object_stream(&mut reader, &key)
        .await
        .context("put_object_stream failed")?;

    Ok(key)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn it_works() {
        let env = Env::dev().unwrap();
        init(&env).await.unwrap();
    }
}
