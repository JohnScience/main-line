// We created another type so that the shared_items_lib does not
// depend on sqlx crate.
#[derive(sqlx::Type, derive_more::Display, Debug)]
#[sqlx(transparent)]
pub(crate) struct UserId(pub(in crate::db) i32);

impl From<shared_items_lib::id::UserId> for UserId {
    fn from(value: shared_items_lib::id::UserId) -> Self {
        UserId(value.0)
    }
}

impl From<UserId> for shared_items_lib::id::UserId {
    fn from(value: UserId) -> Self {
        shared_items_lib::id::UserId(value.0)
    }
}
