use crate::db;

#[derive(sqlx::FromRow, Debug)]
pub(crate) struct UserPageData {
    pub(crate) avatar_s3_key: Option<String>,
    pub(crate) username: String,
    pub(crate) email: Option<String>,
    pub(crate) chess_dot_com_username: Option<String>,
    pub(crate) lichess_username: Option<String>,
}

pub(crate) async fn get_user_page_data(
    pg_pool: &sqlx::PgPool,
    user_id: db::id::UserId,
) -> sqlx::Result<Option<UserPageData>> {
    let user_page_data: Option<UserPageData> = sqlx::query_as!(
        UserPageData,
        r#"
        SELECT
            avatar_s3_key,
            username,
            email,
            chess_dot_com_username,
            lichess_username
        FROM users
        WHERE id = $1
        "#,
        user_id.0,
    )
    .fetch_optional(pg_pool)
    .await?;

    if user_page_data.is_none() {
        tracing::warn!(
            "Couldn't find user with id {} when calling {m}::{fn_name}",
            user_id.0,
            m = module_path!(),
            fn_name = "get_user_page_data",
        );
    } else {
        tracing::info!(
            "Fetched user page data for user id {} when calling {m}::{fn_name}: {user_page_data:?}",
            user_id.0,
            m = module_path!(),
            fn_name = "get_user_page_data",
        );
    }

    Ok(user_page_data)
}
