# Running the project

To run the project, you need to have Docker and Docker Compose installed on your machine. Follow these steps:

* Clone the repository to your local machine.
* Navigate to the project directory.
* Run the following command to remove the old intermediate images (if present):

```bash
# Windows
docker rmi main-line-rust_workspace 2>nul || echo "image main-line-rust_workspace doesn't exist yet"
docker rmi main-line-backend_lib 2>nul || echo "image main-line-backend_lib doesn't exist yet"

# Linux / MacOS
docker rmi main-line-rust_workspace || echo "image main-line-rust_workspace doesn't exist yet"
docker rmi main-line-backend_lib || echo "image main-line-backend_lib doesn't exist yet"
```

* Build the intermediate images:

```bash
docker build -t main-line-rust_workspace -f Dockerfile.rust_workspace .
docker build -t main-line-backend_lib -f Dockerfile.backend_lib .
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
