use crate::db::id::UserId;

// pub fn register(
//     pg_pool: &sqlx::PgPool,
//     username: &str,
//     password_hash: &str,
// ) -> anyhow::Result<UserId> {
//     let user_id = sqlx::query_scalar!(
//         r#"
//         INSERT INTO users (username, password_hash)
//         VALUES ($1, $2)
//         RETURNING id
//         "#,
//         username,
//         password_hash
//     )
//     .fetch_one(pg_pool)
//     .await?;
//     Ok(UserId(user_id))
// }
