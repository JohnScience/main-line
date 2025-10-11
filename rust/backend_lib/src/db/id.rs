// We created another type so that the mnln_core_items does not
// depend on sqlx crate.
#[derive(sqlx::Type, derive_more::Display, Debug, Clone, Copy)]
#[sqlx(transparent)]
pub(crate) struct UserId(pub(in crate::db) i32);

impl From<mnln_core_items::id::UserId> for UserId {
    fn from(value: mnln_core_items::id::UserId) -> Self {
        UserId(value.0)
    }
}

impl From<UserId> for mnln_core_items::id::UserId {
    fn from(value: UserId) -> Self {
        mnln_core_items::id::UserId(value.0)
    }
}
