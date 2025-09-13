pub mod service_responses;

// We export this function because
// it depends on the `TYPES` static
// populated with `#[ctor]` functions
// defined in the `specta::Type` macro.
//
// See more at https://docs.rs/specta/latest/specta/export/static.TYPES.html
pub fn export_shared_types(file_path: &str) -> Result<(), specta::ts::TsExportError> {
    specta::export::ts(file_path)
}
