use shared_items_lib::JwtClaims;
use shared_items_lib::JwtString;
use shared_items_lib::Role;
use shared_items_lib::id::UserId;
use shared_items_lib::service_responses::PostLoginResponse;
use shared_items_lib::service_responses::PostLoginResponseSuccess;
use shared_items_lib::service_responses::PostRegisterResponse;
use shared_items_lib::service_responses::PostSaltResponse;
use shared_items_lib::service_responses::PostSaltResponseSuccess;

use crate::Context;
use crate::db;
use crate::util;

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
pub(crate) struct LoginRequest {
    username: String,
    password_hash: String,
}

fn create_jwt_claims(user_id: UserId, role: Role) -> JwtClaims {
    let iat = util::now();
    let exp = util::time_from_now(chrono::Duration::weeks(2));
    JwtClaims {
        sub: user_id,
        role,
        iat,
        exp,
    }
}

pub(crate) async fn login(ctx: &Context, request: LoginRequest) -> PostLoginResponse {
    let LoginRequest {
        username,
        password_hash,
    } = request;

    let (user_id, role) =
        match db::user::check_credentials(&ctx.db, &username, &password_hash).await {
            db::user::check_credentials::Output::UserNotFound
            | db::user::check_credentials::Output::WrongPassword => {
                return PostLoginResponse::InvalidCredentials;
            }
            db::user::check_credentials::Output::DbError { err } => {
                tracing::error!(
                    "The function {mod_path}::{fn_name}(...) failed: {err}",
                    mod_path = module_path!(),
                    fn_name = stringify!(login),
                    err = err,
                );
                return PostLoginResponse::InternalServerError;
            }
            db::user::check_credentials::Output::Valid { user_id, role } => (user_id, role),
        };

    let user_id: UserId = user_id.into();
    let role: Role = role.into();

    let claims: JwtClaims = create_jwt_claims(user_id, role);
    let jwt: JwtString = match util::sign_jwt(&claims, ctx) {
        Ok(jwt) => jwt,
        Err(e) => {
            tracing::error!(
                "The function {mod_path}::{fn_name}(...) failed while signing a JWT: {err}",
                mod_path = module_path!(),
                fn_name = stringify!(login),
                err = e,
            );
            return PostLoginResponse::InternalServerError;
        }
    };

    PostLoginResponse::Success(PostLoginResponseSuccess { jwt })
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
    PostSaltResponse::Success(PostSaltResponseSuccess { salt })
}
