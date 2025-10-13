use crate::links;
use axum::response::IntoResponse as _;

use axum::http::StatusCode;
use axum::response::Response;

use browser_supported_img_format::BrowserSupportedImgFormat;
use futures_core::Stream;
use shared_items_lib::JwtClaims;
use shared_items_lib::JwtString;
use shared_items_lib::Role;
use shared_items_lib::id::UserId;
use shared_items_lib::service_responses::PostLoginResponse;
use shared_items_lib::service_responses::PostLoginResponseSuccess;
use shared_items_lib::service_responses::PostRegisterResponse;
use shared_items_lib::service_responses::PostSaltResponse;
use shared_items_lib::service_responses::PostSaltResponseSuccess;
use shared_items_lib::service_responses::PostUploadUserAvatarResponse;
use shared_items_lib::service_responses::PostUploadUserAvatarSuccess;

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

    let user_id: mnln_core_items::id::UserId = user_id.into();
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

    tracing::trace!(
        "The function {mod_path}::{fn_name}(...) progress: retrieved password hash for user {username}. Hash: {hash}",
        mod_path = module_path!(),
        fn_name = stringify!(salt),
        username = username,
    );

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

    tracing::trace!(
        "The function {mod_path}::{fn_name}(...) succeeded: retrieved salt for user {username}. Salt: {salt}",
        mod_path = module_path!(),
        fn_name = stringify!(salt),
    );

    PostSaltResponse::Success(PostSaltResponseSuccess { salt })
}

// We don't decode in anywhere because we work on streams
// as opposed to Vec<u8>
#[allow(unused)]
#[derive(utoipa::ToSchema)]
pub struct UploadUserAvatarRequest {
    // https://github.com/juhaku/utoipa/issues/197
    #[schema(value_type = String, format = Binary)]
    pub avatar: bytes::Bytes,
}

async fn avatar_byte_stream_from_multipart<'m>(
    multipart: &'m mut axum::extract::Multipart,
) -> Result<
    (
        impl Stream<Item = Result<bytes::Bytes, std::io::Error>> + Send + Unpin,
        BrowserSupportedImgFormat,
    ),
    PostUploadUserAvatarResponse,
> {
    use futures_util::stream::TryStreamExt as _;

    let field = match multipart.next_field().await {
        Ok(Some(field)) => field,
        Ok(None) => {
            tracing::error!(
                "The function {mod_path}::{fn_name}(...) failed: missing the avatar field",
                mod_path = module_path!(),
                fn_name = stringify!(avatar_byte_stream_from_multipart),
            );
            return Err(PostUploadUserAvatarResponse::BadRequest {
                detail: "Missing the avatar field".to_string(),
            });
        }
        Err(err) => {
            tracing::error!(
                "The function {mod_path}::{fn_name}(...) failed: {err}",
                mod_path = module_path!(),
                fn_name = stringify!(avatar_byte_stream_from_multipart),
                err = err,
            );
            return Err(PostUploadUserAvatarResponse::InternalServerError { detail: None });
        }
    };

    let field_name: Option<&str> = field.name();

    let Some(field_name) = field_name else {
        tracing::error!(
            "The function {mod_path}::{fn_name}(...) failed: missing the field name",
            mod_path = module_path!(),
            fn_name = stringify!(avatar_byte_stream_from_multipart),
        );
        return Err(PostUploadUserAvatarResponse::BadRequest {
            detail: "Missing the field name".to_string(),
        });
    };

    if field_name != "avatar" {
        tracing::error!(
            "The function {mod_path}::{fn_name}(...) failed: unexpected field name: `{field_name}`",
            mod_path = module_path!(),
            fn_name = stringify!(avatar_byte_stream_from_multipart),
            field_name = field_name,
        );
        return Err(PostUploadUserAvatarResponse::BadRequest {
            detail: format!("Unexpected field name: `{field_name}`"),
        });
    };

    let file_name: Option<&str> = field.file_name();

    let Some(file_name) = file_name else {
        return Err(PostUploadUserAvatarResponse::BadRequest {
            detail: "Missing file name".to_string(),
        });
    };

    let Some(file_format) = BrowserSupportedImgFormat::infer(file_name) else {
        return Err(PostUploadUserAvatarResponse::BadRequest {
            detail: format!("Unsupported image format for the file: `{file_name}`"),
        });
    };

    let stream = field.map_err(|e| std::io::Error::new(std::io::ErrorKind::Other, e));

    Ok((stream, file_format))
}

pub(crate) async fn upload_user_avatar(
    ctx: &Context,
    claims: Option<JwtClaims>,
    mut multipart: axum::extract::Multipart,
) -> PostUploadUserAvatarResponse {
    let Some(claims) = claims else {
        tracing::warn!("post_upload_user_avatar: Missing JWT claims");
        return PostUploadUserAvatarResponse::Unauthorized {
            detail: "Missing or invalid JWT".to_string(),
        };
    };

    let user_id: mnln_core_items::id::UserId = claims.sub.into();

    let (stream, file_format) = match avatar_byte_stream_from_multipart(&mut multipart).await {
        Ok((stream, file_format)) => (stream, file_format),
        Err(err_resp) => return err_resp,
    };

    let s3_key = match object_storage::save_avatar(&ctx.env, user_id, stream, file_format).await {
        Ok(s3_key) => s3_key,
        Err(e) => {
            tracing::error!(
                "The function {mod_path}::{fn_name}(...) failed: {err}",
                mod_path = module_path!(),
                fn_name = stringify!(upload_user_avatar),
                err = e,
            );
            return PostUploadUserAvatarResponse::InternalServerError { detail: None };
        }
    };

    let user_id: db::id::UserId = user_id.into();

    if let Err(e) = db::user::set_avatar(&ctx.db, user_id, &s3_key).await {
        tracing::error!(
            "The function {mod_path}::{fn_name}(...) failed: {err}",
            mod_path = module_path!(),
            fn_name = stringify!(upload_user_avatar),
            err = e,
        );
        return PostUploadUserAvatarResponse::InternalServerError {
            detail: Some("Failed to set the uploaded avatar".to_string()),
        };
    };

    // TODO: find a way to do this via a drop guard
    match multipart.next_field().await {
        Ok(Some(_)) => {
            return PostUploadUserAvatarResponse::BadRequest {
                detail: "Unexpected extra form field".to_string(),
            };
        }
        Ok(None) => (),
        Err(e) => {
            tracing::error!(
                "The function {mod_path}::{fn_name}(...) failed: {err}",
                mod_path = module_path!(),
                fn_name = stringify!(upload_user_avatar),
                err = e,
            );
            return PostUploadUserAvatarResponse::InternalServerError { detail: None };
        }
    };

    let user_id: mnln_core_items::id::UserId = user_id.into();

    let url = links::avatar_url(&ctx.env, user_id);

    PostUploadUserAvatarResponse::Success(PostUploadUserAvatarSuccess { url })
}

pub(crate) async fn get_user_avatar(
    ctx: &Context,
    user_id: mnln_core_items::id::UserId,
) -> Response {
    let user_id: db::id::UserId = user_id.into();
    let avatar_s3_key = match db::user::get_avatar(&ctx.db, user_id).await {
        Ok(Some(avatar_s3_key)) => avatar_s3_key,
        Ok(None) => {
            return StatusCode::NOT_FOUND.into_response();
        }
        Err(e) => {
            tracing::error!(
                "The function {mod_path}::{fn_name}(...) failed: {err}",
                mod_path = module_path!(),
                fn_name = stringify!(get_user_avatar),
                err = e,
            );
            return StatusCode::INTERNAL_SERVER_ERROR.into_response();
        }
    };

    let avatar = match object_storage::get_avatar(&ctx.env, &avatar_s3_key).await {
        Ok(avatar) => avatar,
        Err(e) => {
            tracing::error!(
                "The function {mod_path}::{fn_name}(...) failed: {err}",
                mod_path = module_path!(),
                fn_name = stringify!(get_user_avatar),
                err = e,
            );
            return StatusCode::INTERNAL_SERVER_ERROR.into_response();
        }
    };

    let content_type = match BrowserSupportedImgFormat::infer(&avatar_s3_key) {
        Some(format) => format.content_type(),
        None => {
            tracing::error!(
                "The function {mod_path}::{fn_name}(...) failed: unsupported image format for the user avatar file: `{avatar_s3_key}`",
                mod_path = module_path!(),
                fn_name = stringify!(get_user_avatar),
            );
            "application/octet-stream"
        }
    };

    (
        StatusCode::OK,
        [(axum::http::header::CONTENT_TYPE, content_type)],
        avatar,
    )
        .into_response()
}
