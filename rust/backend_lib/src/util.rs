use hmac::Mac as _;
use jwt::SignWithKey as _;

use hmac::Hmac;
use sha2::Sha256;

use shared_items_lib::{JwtClaims, JwtString, Timestamp};

use crate::Context;

pub(crate) fn now() -> Timestamp {
    let now = chrono::Utc::now();
    let timestamp = now.timestamp_millis();
    Timestamp(timestamp as u64)
}

pub(crate) fn time_from_now(duration: chrono::Duration) -> Timestamp {
    let later = chrono::Utc::now() + duration;
    let timestamp = later.timestamp_millis();
    Timestamp(timestamp as u64)
}

// See <https://docs.rs/jwt/latest/jwt/#signing>
pub(crate) fn sign_jwt(claims: &JwtClaims, ctx: &Context) -> anyhow::Result<JwtString> {
    let key: Hmac<Sha256> = Hmac::new_from_slice(ctx.env.jwt_signing_key.as_bytes())?;
    let token_str = claims.sign_with_key(&key)?;
    Ok(JwtString(token_str))
}
