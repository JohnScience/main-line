//! Backend-for-Frontend (BFF) service layer.

use shared_items_lib::service_responses::{GetUserPageDataResponse, UserPageData};

use crate::{Context, db, links};

pub(crate) async fn get_user_page_data(
    ctx: &Context,
    user_id: shared_items_lib::id::UserId,
) -> GetUserPageDataResponse {
    let user_id: mnln_core_items::id::UserId = user_id.into();
    let user_id: db::id::UserId = user_id.into();
    // TODO: cache avatar_s3_key

    let user_page_data = match db::bff::get_user_page_data(&ctx.db, user_id).await {
        Ok(data) => data,
        Err(err) => {
            tracing::error!("Failed to get user page data from the database: {err}");
            return GetUserPageDataResponse::InternalServerError;
        }
    };
    let Some(db::bff::UserPageData {
        avatar_s3_key,
        username,
        email,
        chess_dot_com_username,
        lichess_username,
    }) = user_page_data
    else {
        return GetUserPageDataResponse::NotFound;
    };

    let chess_dot_com_profile =
        chess_dot_com_username.map(|username| links::chess_dot_com_profile(&username));
    let lichess_profile = lichess_username.map(|username| links::lichess_profile(&username));

    let avatar_url = if avatar_s3_key.is_some() {
        let user_id: mnln_core_items::id::UserId = user_id.into();
        let avatar_url = links::avatar_url(&ctx.env, user_id);
        Some(avatar_url)
    } else {
        None
    };

    let data = UserPageData {
        avatar_url,
        username,
        email,
        chess_dot_com_profile,
        lichess_profile,
    };

    GetUserPageDataResponse::Success(data)
}
