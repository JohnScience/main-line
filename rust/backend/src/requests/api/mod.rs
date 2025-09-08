use axum::Router;

pub(crate) mod user;

fn api_routes<S>() -> Router<S>
where
    S: Clone + Send + Sync + 'static,
{
    let router = Router::new();
    user::add_nested_routes(router)
}

pub(in crate::requests) fn add_nested_routes<S>(router: Router<S>) -> Router<S>
where
    S: Clone + Send + Sync + 'static,
{
    router.nest("/api", api_routes())
}
