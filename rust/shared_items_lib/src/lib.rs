pub mod id;
pub mod service_responses;

#[derive(specta::Type, serde::Serialize, utoipa::ToSchema)]
#[serde(transparent)]
pub struct JwtString(pub String);

/// A UNIX timestamp in milliseconds (UTC).
#[derive(specta::Type, serde::Serialize, serde::Deserialize, Clone, Copy, Debug)]
#[serde(transparent)]
#[repr(transparent)]
pub struct Timestamp(pub u64);

impl From<mnln_core_items::Timestamp> for Timestamp {
    fn from(value: mnln_core_items::Timestamp) -> Self {
        Timestamp(value.0)
    }
}

impl From<Timestamp> for mnln_core_items::Timestamp {
    fn from(value: Timestamp) -> Self {
        mnln_core_items::Timestamp(value.0)
    }
}

#[derive(specta::Type, serde::Serialize, serde::Deserialize, Clone, Debug)]
pub struct JwtClaims {
    /// Subject of the JWT (the user)
    pub sub: id::UserId,
    /// Expiration time
    pub exp: Timestamp,
    /// Issued at
    pub iat: Timestamp,
    /// Role of the user
    pub role: Role,
}

#[derive(specta::Type, serde::Serialize, serde::Deserialize, Clone, Copy, Debug)]
pub enum Role {
    Admin,
    User,
}

// We export this function because
// it depends on the `TYPES` static
// populated with `#[ctor]` functions
// defined in the `specta::Type` macro.
//
// See more at https://docs.rs/specta/latest/specta/export/static.TYPES.html
pub fn export_shared_types(file_path: &str) -> Result<(), specta::ts::TsExportError> {
    let cfg =
        specta::ts::ExportConfiguration::default().bigint(specta::ts::BigIntExportBehavior::BigInt);
    specta::export::ts_with_cfg(file_path, &cfg)
}
