use axum::http::StatusCode;

pub(crate) mod bff;
pub(crate) mod user;

pub(crate) enum ServiceError {
    /// This error is intended to be shown to the user
    UserExposedError {
        status_code: StatusCode,
        detail: String,
    },
    /// This error is not intended to be shown to the user
    UserOpaqueError { anyhow_err: anyhow::Error },
}

pub(crate) type ServiceResult<T> = Result<T, ServiceError>;

pub(crate) trait MapErrorToUserOpaque<T> {
    fn map_error_to_user_opaque(self) -> ServiceResult<T>;
}

impl<T, E> MapErrorToUserOpaque<T> for Result<T, E>
where
    E: Into<anyhow::Error> + std::fmt::Debug,
{
    fn map_error_to_user_opaque(self) -> ServiceResult<T> {
        match self {
            Ok(v) => return Ok(v),
            Err(e) => {
                tracing::error!("Error converted to user-opaque: {e:?}");
                Err(ServiceError::UserOpaqueError {
                    anyhow_err: e.into(),
                })
            }
        }
    }
}

pub(crate) trait MapErrorToUserExposed<T> {
    fn map_error_to_user_exposed(self, status_code: StatusCode, detail: String)
    -> ServiceResult<T>;
}

impl<T, E> MapErrorToUserExposed<T> for Result<T, E>
where
    E: Into<anyhow::Error> + std::fmt::Debug,
{
    fn map_error_to_user_exposed(
        self,
        status_code: StatusCode,
        detail: String,
    ) -> ServiceResult<T> {
        match self {
            Ok(v) => return Ok(v),
            Err(e) => {
                tracing::error!(
                    "Error converted to user-exposed: {e:?}. Status code: {status_code}, detail: {detail}"
                );
                Err(ServiceError::UserExposedError {
                    status_code,
                    detail,
                })
            }
        }
    }
}
