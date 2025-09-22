use tracing::{error, trace};

use crate::db::id::UserId;

#[derive(sqlx::Type)]
#[sqlx(type_name = "role")]
#[sqlx(rename_all = "lowercase")]
pub(crate) enum Role {
    User,
    Admin,
}

impl From<shared_items_lib::Role> for Role {
    fn from(value: shared_items_lib::Role) -> Self {
        match value {
            shared_items_lib::Role::Admin => Role::Admin,
            shared_items_lib::Role::User => Role::User,
        }
    }
}

impl From<Role> for shared_items_lib::Role {
    fn from(value: Role) -> Self {
        match value {
            Role::Admin => shared_items_lib::Role::Admin,
            Role::User => shared_items_lib::Role::User,
        }
    }
}

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
    let res: sqlx::Result<UserId> = sqlx::query_scalar!(
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

pub(crate) mod check_credentials {
    use crate::db::id::UserId;

    use super::Role;

    pub(crate) struct User {
        pub id: UserId,
        pub role: Role,
        pub password_hash: String,
    }

    pub(crate) enum Output {
        Valid { user_id: UserId, role: Role },
        WrongPassword,
        UserNotFound,
        DbError { err: sqlx::Error },
    }
}

pub(crate) async fn check_credentials(
    pg_pool: &sqlx::PgPool,
    username: &str,
    password_hash: &str,
) -> check_credentials::Output {
    let res = sqlx::query_as!(
        check_credentials::User,
        r#"
        SELECT id as "id!: UserId", password_hash, role as "role!: Role"
        FROM users
        WHERE username = $1
        "#,
        username,
    )
    .fetch_optional(pg_pool)
    .await;

    let output = match res {
        Ok(Some(check_credentials::User {
            id: user_id,
            password_hash: stored_hash,
            role,
        })) if stored_hash == password_hash => check_credentials::Output::Valid { user_id, role },
        Ok(Some(_)) => check_credentials::Output::WrongPassword,
        Ok(None) => check_credentials::Output::UserNotFound,
        Err(err) => check_credentials::Output::DbError { err },
    };

    match &output {
        check_credentials::Output::Valid { user_id, role: _ } => trace!(
            "The function {mod_path}::{fn_name}(...) succeeded: valid credentials for user ID {user_id}",
            mod_path = module_path!(),
            fn_name = stringify!(check_credentials),
        ),
        check_credentials::Output::WrongPassword => error!(
            "The function {mod_path}::{fn_name}(...) failed: wrong password",
            mod_path = module_path!(),
            fn_name = stringify!(check_credentials),
        ),
        check_credentials::Output::UserNotFound => error!(
            "The function {mod_path}::{fn_name}(...) failed: user not found",
            mod_path = module_path!(),
            fn_name = stringify!(check_credentials),
        ),
        check_credentials::Output::DbError { err } => error!(
            "The function {mod_path}::{fn_name}(...) failed: {err}",
            mod_path = module_path!(),
            fn_name = stringify!(check_credentials),
            err = err,
        ),
    };

    output
}

pub(crate) mod get_password_hash {
    /// See <https://docs.rs/argon2/0.5.3/argon2/struct.PasswordHash.html>
    #[derive(sqlx::Type)]
    #[sqlx(transparent)]
    pub(crate) struct PHCString(pub(in crate::db) String);

    impl<'a> TryFrom<&'a PHCString> for argon2::PasswordHash<'a> {
        type Error = argon2::password_hash::Error;

        fn try_from(value: &'a PHCString) -> Result<Self, Self::Error> {
            argon2::PasswordHash::new(&value.0)
        }
    }
}

pub(crate) async fn get_password_hash(
    pg_pool: &sqlx::PgPool,
    username: &str,
) -> sqlx::Result<Option<get_password_hash::PHCString>> {
    let res: Option<String> = sqlx::query_scalar!(
        r#"
        SELECT password_hash
        FROM users
        WHERE username = $1
        "#,
        username,
    )
    .fetch_optional(pg_pool)
    .await?;

    Ok(res.map(get_password_hash::PHCString))
}
