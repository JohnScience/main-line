pub(crate) mod env;

use env::Env;

use crate::db::Db;

#[derive(Clone)]
pub(crate) struct Context {
    pub(crate) env: Env,
    pub(crate) db: Db,
}
