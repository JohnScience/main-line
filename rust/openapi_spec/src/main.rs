use utoipa::OpenApi as _;

use backend_lib::ApiDoc;

fn main() {
    let openapi = ApiDoc::openapi();
    println!("{}", openapi.to_pretty_json().unwrap());
}
