mod api;
mod general;

pub(crate) fn make_router<S>() -> axum::Router<S>
where
    S: Clone + Send + Sync + 'static,
{
    let router = axum::Router::new();
    let router = general::add_routes(router);
    router
}
