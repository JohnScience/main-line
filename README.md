# Running the project

To run the project, you need to have Docker and Docker Compose installed on your machine. Follow these steps:

* Clone the repository to your local machine.
* Navigate to the project directory.
* Run the following command to remove the old intermediate images (if present):

```bash
# Windows
docker rmi main-line-rust_workspace 2>nul || echo "image main-line-rust_workspace doesn't exist yet"
docker rmi main-line-backend_lib 2>nul || echo "image main-line-backend_lib doesn't exist yet"
docker rmi main-line-openapi_spec 2>nul || echo "image main-line-openapi_spec doesn't exist yet"

# Linux / MacOS
docker rmi main-line-rust_workspace || echo "image main-line-rust_workspace doesn't exist yet"
docker rmi main-line-backend_lib || echo "image main-line-backend_lib doesn't exist yet"
docker rmi main-line-openapi_spec || echo "image main-line-openapi_spec doesn't exist yet"
```

* Build the intermediate images:

```bash
docker build -t main-line-rust_workspace -f Dockerfile.rust_workspace .
docker build -t main-line-backend_lib -f Dockerfile.backend_lib .
docker build -t main-line-openapi_spec -f Dockerfile.openapi_spec .
```

*Note: Ideally, this should be done using `additional_contexts` feature of Docker compose. However, my builder of version `v2.33.1-desktop.1` doesn't support it. Here's how I suppose it could be possible.*

```yml
backend-lib:
    build:
      context: ./
      dockerfile: Dockerfile.backend-lib
      # The docs (https://docs.docker.com/compose/how-tos/dependent-images/#use-another-services-image-as-the-base-image) state it should work
      # but it doesn't
      additional_contexts:
        # `FROM main-line-rust-workspace AS rust-workspace` would reference this image
        main-line-rust-workspace: "service:rust-workspace"
    profiles: ["build-only"]
```

* Run the multi-container application using Docker Compose:

```bash
docker compose up --build
```

# Testing the project

## Backend

### Health Check

To check if the `backend` service is running correctly, you can check whether the <localhost:3000/health-check> endpoint returns a `200 OK` status.

```bash
curl -i http://localhost:3000/health-check
```

### API Documentation

For the full list of available endpoints, navigate to <http://localhost:3000/swagger-ui/>.

### Postman Collection

For the Postman collection, please navigate to <https://www.postman.com/flight-saganist-17578370/workspace/mainline>.

# Docker images

* `main-line-rust_workspace` (`Dockerfile.rust_workspace`): This image contains the Rust toolchain and is used as a base for building Rust crates in the project. It builds only the dependencies of the Rust crates to speed up the build process. However, it does not build any crate in the project.
* `main-line-backend_lib` (`Dockerfile.backend_lib`): This image is built on top of `main-line-rust_workspace` (`Dockerfile.rust_workspace`) and is used to build the `backend_lib` crate, which contains shared code for the backend service and for generating the OpenAPI specification.
* `main-line-openapi_spec` (`Dockerfile.openapi_spec`): This image is built on top of `main-line-backend_lib` (`Dockerfile.backend_lib`) and is used to generate the OpenAPI specification from the Rust code in the `backend_lib` crate. To extract the generated OpenAPI specification from the image, you can use the following commands:

```bash
# Create a container from the image (without running it). The container is not meant to be run, so
# we pass `true` as the mandatory command argument.
docker container create --name main-line-openapi_spec main-line-openapi_spec true
# Copy the generated OpenAPI specification from the container to your local machine
docker cp main-line-openapi_spec:/openapi_spec/openapi_spec.json ./openapi_spec.json
# Remove the container
docker container rm main-line-openapi_spec
```

* `main-line-backend` (`Dockerfile.backend`): This image is built on top of `main-line-backend_lib` (`Dockerfile.backend_lib`) and is used to run the backend service.
