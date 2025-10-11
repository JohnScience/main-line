use mnln_env::Env;

pub(crate) fn avatar_url(env: &Env, user_id: mnln_core_items::id::UserId) -> String {
    let base_api_url = &env.base_api_url;
    format!("{base_api_url}/api/user/{user_id}/avatar")
}

pub(crate) fn chess_dot_com_profile(username: &str) -> String {
    format!("https://www.chess.com/member/{username}")
}

pub(crate) fn lichess_profile(username: &str) -> String {
    format!("https://lichess.org/@/{username}")
}
