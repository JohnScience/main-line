# Running the project

## Dependencies

* Git
* Python
* Docker
* Docker Compose

## How to run

Once you have the dependencies installed, follow these steps:

* Clone the repository to your local machine.
* Navigate to the project directory.

* Build the intermediate Docker images using the Python script:

```bash
python -m scripts.build_intermediate_images
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

# Development

Working on the project heavily depends on code-generation. To extract the code-generated artifacts from the built Docker images, run:

```bash
python -m scripts.extract_artifacts
```

# Images

To learn more about the Docker images used in this project, read the comments in the `scripts/common/docker_images.py` file.
