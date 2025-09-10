pub(crate) mod env;

use env::Env;

use crate::db::Db;

#[derive(Clone)]
pub struct Context {
    pub env: Env,
    pub db: Db,
}

impl Context {
    pub async fn new() -> anyhow::Result<Self> {
        let env = Env::from_env()?;
        let db = Db::new(&env.pg).await?;

        let ctx = Self { env, db };
        Ok(ctx)
    }
}
