#[derive(sqlx::Type)]
#[sqlx(transparent)]
pub(crate) struct UserId(i64);
