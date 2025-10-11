use serde::Deserialize;
use utoipa::IntoParams;

use shared_items_lib::id::UserId;

#[derive(Deserialize, IntoParams)]
#[into_params(parameter_in = Path)]
pub(crate) struct UserIdPathParams {
    pub(crate) user_id: UserId,
}
