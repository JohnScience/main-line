use shared_items_lib::service_responses::PostRegisterResponse;

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
