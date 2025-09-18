use shared_items_lib::service_responses::PostRegisterResponse;
use shared_items_lib::service_responses::PostSaltResponse;
use shared_items_lib::service_responses::SaltResponseSuccess;

use crate::Context;
use crate::db;

#[derive(serde::Deserialize, utoipa::ToSchema)]
pub(crate) struct RegisterRequest {
    username: String,
    password_hash: String,
}

impl From<db::user::register::Output> for PostRegisterResponse {
    fn from(value: db::user::register::Output) -> Self {
        match value {
            db::user::register::Output::Success { user_id: _ } => PostRegisterResponse::Success,
            db::user::register::Output::AlreadyExists => PostRegisterResponse::AlreadyExists,
            db::user::register::Output::UnknownError { err: _ } => {
                PostRegisterResponse::InternalServerError
            }
        }
    }
}

pub(crate) async fn register(ctx: &Context, request: RegisterRequest) -> PostRegisterResponse {
    let RegisterRequest {
        username,
        password_hash,
    } = request;
    let output: db::user::register::Output =
        db::user::register(&ctx.db, &username, &password_hash).await;
    PostRegisterResponse::from(output)
}

#[derive(serde::Deserialize, utoipa::ToSchema)]
pub(crate) struct SaltRequest {
    username: String,
}

pub(crate) async fn salt(ctx: &Context, request: SaltRequest) -> PostSaltResponse {
    let SaltRequest { username } = request;
    let hash = match db::user::get_password_hash(&ctx.db, &username).await {
        Ok(hash) => hash,
        Err(e) => {
            tracing::error!(
                "The function {mod_path}::{fn_name}(...) failed: {err}",
                mod_path = module_path!(),
                fn_name = stringify!(salt),
                err = e,
            );
            return PostSaltResponse::InternalServerError;
        }
    };

    let Some(ref hash) = hash else {
        return PostSaltResponse::UserNotFound;
    };
    let hash: argon2::PasswordHash = match hash.try_into() {
        Ok(hash) => hash,
        Err(e) => {
            tracing::error!(
                "The function {mod_path}::{fn_name}(...) failed: {err}",
                mod_path = module_path!(),
                fn_name = stringify!(salt),
                err = e,
            );
            return PostSaltResponse::InternalServerError;
        }
    };

    let Some(salt) = hash.salt else {
        tracing::error!(
            "The function {mod_path}::{fn_name}(...) failed: no salt found in password hash \
            for user {username}",
            mod_path = module_path!(),
            fn_name = stringify!(salt),
        );
        return PostSaltResponse::InternalServerError;
    };

    let salt = salt.as_str().to_string();
    PostSaltResponse::Success(SaltResponseSuccess { salt })
}
