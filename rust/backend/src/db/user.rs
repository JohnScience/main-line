use tracing::{error, trace};

use crate::db::id::UserId;

pub(crate) mod register {
    use crate::db::id::UserId;

    pub(crate) enum Output {
        Success { user_id: UserId },
        AlreadyExists,
        UnknownError { err: sqlx::Error },
    }

    impl From<sqlx::Result<UserId>> for Output {
        fn from(value: sqlx::Result<UserId>) -> Self {
            match value {
                Ok(user_id) => Self::Success { user_id },
                Err(err)
                    if err.as_database_error().is_some_and(|db_err| {
                        matches!(db_err.kind(), sqlx::error::ErrorKind::UniqueViolation)
                    }) =>
                {
                    Self::AlreadyExists
                }
                Err(err) => Self::UnknownError { err },
            }
        }
    }
}

pub(crate) async fn register(
    pg_pool: &sqlx::PgPool,
    username: &str,
    password_hash: &str,
) -> register::Output {
    let res = sqlx::query_scalar!(
        r#"
        INSERT INTO users (username, password_hash)
        VALUES ($1, $2)
        RETURNING id as "id!: UserId"
        "#,
        username,
        password_hash,
    )
    .fetch_one(pg_pool)
    .await;

    let output = register::Output::from(res);

    match &output {
        register::Output::Success { user_id } => trace!(
            "The function {mod_path}::{fn_name}(...) succeeded: registered user with ID {user_id}",
            mod_path = module_path!(),
            fn_name = stringify!(register),
        ),
        register::Output::AlreadyExists => error!(
            "The function {mod_path}::{fn_name}(...) failed: user already exists",
            mod_path = module_path!(),
            fn_name = stringify!(register),
        ),
        register::Output::UnknownError { err } => error!(
            "The function {mod_path}::{fn_name}(...) failed: {err}",
            mod_path = module_path!(),
            fn_name = stringify!(register),
            err = err,
        ),
    };

    output
}
