use mnln_env::Env;

use crate::util;

pub(crate) fn avatar_url(env: &Env, user_id: mnln_core_items::id::UserId) -> String {
    let base_api_url = &env.base_api_url;
    let timestamp: shared_items_lib::Timestamp = util::now();
    let timestamp: mnln_core_items::Timestamp = timestamp.into();
    // https://stackoverflow.com/questions/1077041/refresh-image-with-a-new-one-at-the-same-url
    format!("{base_api_url}/api/user/{user_id}/avatar?ts={timestamp}")
}

pub(crate) fn chess_dot_com_profile(username: &str) -> String {
    format!("https://www.chess.com/member/{username}")
}

pub(crate) fn lichess_profile(username: &str) -> String {
    format!("https://lichess.org/@/{username}")
}
