#[derive(
    specta::Type, serde::Serialize, serde::Deserialize, utoipa::ToSchema, Clone, Copy, Debug,
)]
#[serde(transparent)]
pub struct UserId(pub i32);

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
