#[derive(sqlx::Type, derive_more::Display)]
#[sqlx(transparent)]
pub(crate) struct UserId(pub(in crate::db) i32);
