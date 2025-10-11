//! Backend-for-Frontend (BFF) API request handlers.

use std::sync::Arc;

use axum::{
    Json, Router,
    extract::{Path, State},
    http::StatusCode,
    response::{IntoResponse, Response},
    routing::get,
};
use shared_items_lib::service_responses::{GetUserPageDataResponse, UserPageData};

use crate::params::UserIdPathParams;
use crate::{Context, service};

#[utoipa::path(
    get,
    path = "/api/bff/user-page-data/{user_id}",
    tag = "bff",
    responses(
        (status = 200, description = "User page data returned successfully", body = UserPageData),
        (status = 404, description = "User not found", body = ()),
        (status = 500, description = "Internal server error", body = ()),
    ),
    params(UserIdPathParams)
)]
async fn get_user_page_data(
    State(ctx): State<Arc<Context>>,
    Path(path_params): Path<UserIdPathParams>,
) -> Response {
    let UserIdPathParams { user_id } = path_params;
    match service::bff::get_user_page_data(&ctx, user_id).await {
        GetUserPageDataResponse::Success(data) => (StatusCode::OK, Json(data)).into_response(),
        GetUserPageDataResponse::NotFound => StatusCode::NOT_FOUND.into_response(),
        GetUserPageDataResponse::InternalServerError => {
            StatusCode::INTERNAL_SERVER_ERROR.into_response()
        }
    }
}

fn bff_routes() -> Router<Arc<Context>> {
    Router::new().route("/user-page-data/{user_id}", get(get_user_page_data))
}

pub(in crate::requests::api) fn add_nested_routes(
    router: axum::Router<Arc<Context>>,
) -> axum::Router<Arc<Context>> {
    router.nest("/bff", bff_routes())
}
