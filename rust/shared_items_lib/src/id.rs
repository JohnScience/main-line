#[derive(specta::Type, serde::Serialize, serde::Deserialize, utoipa::ToSchema)]
#[serde(transparent)]
pub struct UserId(pub i32);
