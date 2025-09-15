from dataclasses import dataclass
import subprocess
from typing import TypedDict
from pathlib import Path

from scripts.common.docker import copy_from_container, create_container, remove_container

from .git import get_git_root

class PurposeSpecificDataVariant:
    # These images are used to store the artifacts or data generated during the build process.
    # They do not contain any executable code or runtime environment.
    # In this project, the `main-line-openapi_spec` and `main-line-api_client` images are examples of
    # data-only images, as they are used to generate and store the OpenAPI specification and API client
    # code, respectively.
    @dataclass
    class DataOnly:
        # the path inside the image where the artifact is stored
        artifact_path: str
        # the paths relative to the project root where the artifact should be copied to
        dest: list[str]
    # Setup images are used to set up the environment for building applications and images.
    # They typically contain the necessary tools, libraries, and dependencies required for building
    # and compiling code. In this project, the `main-line-rust_workspace` image is an example of a
    # setup image, providing the Rust toolchain and dependencies needed for building the Rust crates
    # in the project.
    @dataclass
    class Setup:
        pass
    # Application images are used to run the actual applications or services.
    # They contain the compiled code, runtime environment, and any additional dependencies required
    # for the application to function.
    # In this project, the `main-line-backend` image is an application image that runs the backend service.
    @dataclass
    class Application:
        pass

PurposeSpecificData = PurposeSpecificDataVariant.DataOnly | PurposeSpecificDataVariant.Setup | PurposeSpecificDataVariant.Application

class DockerImageDesc(TypedDict):
    # if the name is None,
    # the image is built and managed by Docker Compose
    name: str | None
    dockerfile: str
    is_intermediate: bool
    img_dependencies: list[str]
    purpose_specific_data: PurposeSpecificData

DOCKER_IMAGES: list[DockerImageDesc] = [
    # This is a *setup image* that contains the Rust toolchain and is used as a base
    # for building Rust crates in the project. It builds only the dependencies of the
    # Rust crates to speed up the build process. However, it does not build any crate
    # in the project.
    {
        "name": "main-line-rust_workspace",
        "dockerfile": "Dockerfile.rust_workspace",
        "is_intermediate": True,
        "img_dependencies": [],
        "purpose_specific_data": PurposeSpecificDataVariant.Setup()
    },
    # This is a *setup image* that is built on top of `main-line-rust_workspace`
    # (`Dockerfile.rust_workspace`) and is used to build the `backend_lib` crate,
    # which contains shared code for the backend service and for generating the OpenAPI
    # specification.
    {
        "name": "main-line-backend_lib",
        "dockerfile": "Dockerfile.backend_lib",
        "is_intermediate": True,
        "img_dependencies": ["main-line-rust_workspace"],
        "purpose_specific_data": PurposeSpecificDataVariant.Setup()
    },
    # This is a *data-only image* that is built using the `main-line-backend_lib` (`Dockerfile.backend_lib`)
    # and contains the generated OpenAPI specification from the Rust code in the `backend_lib` crate.
    {
        "name": "main-line-openapi_spec",
        "dockerfile": "Dockerfile.openapi_spec",
        "is_intermediate": True,
        "img_dependencies": ["main-line-backend_lib"],
        "purpose_specific_data": PurposeSpecificDataVariant.DataOnly(
            artifact_path="openapi_spec/openapi_spec.json",
            dest=["openapi_spec.json"]
        )
    },
    # This is an *application image* that is built using `main-line-backend_lib` (`Dockerfile.backend_lib`)
    # and is used to run the backend service.
    {
        "name": None,
        "dockerfile": "Dockerfile.backend",
        "is_intermediate": False,
        "img_dependencies": ["main-line-backend_lib"],
        "purpose_specific_data": PurposeSpecificDataVariant.Application()
    },
    # This is a *data-only image* that is built using the OpenAPI spec from
    # `main-line-openapi_spec` (`Dockerfile.openapi_spec`) and using the `gen-api-client`
    # tool to generate a TypeScript package with an API client and the `rust/export_shared_types`
    # tool to generate the TypeScript definitions for the types shared between the backend and
    # the API client that are defined in Rust and are not part of the OpenAPI specification.
    {
        "name": "main-line-api_client",
        "dockerfile": "Dockerfile.api_client",
        "is_intermediate": True,
        "img_dependencies": ["main-line-openapi_spec", "main-line-rust_workspace"],
        "purpose_specific_data": PurposeSpecificDataVariant.DataOnly(
            artifact_path="api_client",
            dest=["api-client"]
        )
    },
    # This is an *application image* that is built using the `main-line-api_client` (`Dockerfile.api_client`)
    # and is used to run the frontend application.
    {
        "name": None,
        "dockerfile": "Dockerfile.frontend",
        "is_intermediate": False,
        "img_dependencies": ["main-line-api_client"],
        "purpose_specific_data": PurposeSpecificDataVariant.Application()
    }
]

def get_actual_dockerfiles() -> list[str]:
    git_root = get_git_root()
    if git_root is None:
        raise RuntimeError("Not inside a Git repository or Git is not installed.")
    dockerfiles_dir = Path(git_root)
    return [str(p.relative_to(git_root)) for p in dockerfiles_dir.glob("Dockerfile*")]

def check_comprehensiveness():
    known_dockerfiles = [img["dockerfile"] for img in DOCKER_IMAGES]
    actual_dockerfiles = get_actual_dockerfiles()
    missing = set(actual_dockerfiles) - set(known_dockerfiles)
    extra = set(known_dockerfiles) - set(actual_dockerfiles)
    if not missing and not extra:
        return
    
    error_msgs = []
    
    if missing:
        error_msgs.append(f"\tMissing Dockerfiles in DOCKER_IMAGES: {', '.join(missing)}")
    if extra:
        error_msgs.append(f"\tExtra Dockerfiles in DOCKER_IMAGES: {', '.join(extra)}")
    
    raise RuntimeError("\n" + "\n".join(error_msgs))

def check_orderedness():
    # Check that dependencies are defined before they are used
    defined = set()
    for img in DOCKER_IMAGES:
        for dep in img["img_dependencies"]:
            if dep not in defined:
                raise RuntimeError(f"Image '{img['name']}' depends on '{dep}' which is not defined before it.")
        if img["name"] is not None:
            defined.add(img["name"])

def extract_artifact(image: DockerImageDesc, tabulation: str):
    git_root = get_git_root()
    if git_root is None:
        raise RuntimeError("Not inside a Git repository or Git is not installed.")
    psd = image["purpose_specific_data"]
    if not isinstance(psd, PurposeSpecificDataVariant.DataOnly):
        return
    if image["name"] is None:
        raise RuntimeError(f"Image with Dockerfile '{image['dockerfile']}' is a data-only image but has no name.")
    print(f"{tabulation}Extracting artifact from image '{image['name']}'...")
    create_container(image['name'])
    for dest in psd.dest:
        dest_path = Path(git_root) / dest
        copy_from_container(image['name'], psd.artifact_path, dest_path)
        print(f"{tabulation}\tExtracted to {dest_path}")
    remove_container(image['name'])

check_comprehensiveness()
check_orderedness()
# Now DOCKER_IMAGES is guaranteed to be comprehensive and correctly ordered

if __name__ == "__main__":
    print("All checks passed.")
