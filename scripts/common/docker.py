from pathlib import Path
import subprocess
from typing import TypedDict

class BuildOptions(TypedDict):
    tabulation: str
    force_rebuild: bool

class DockerImageBuildArgs(TypedDict):
    name: str
    dockerfile: str

def build_docker_image(img: DockerImageBuildArgs, options: BuildOptions):
    print(f"{options['tabulation']}Preparing to build Docker image: {img['name']} from {img['dockerfile']}...")
    image_exists = docker_image_exists(img["name"])
    if image_exists and not options.get("force_rebuild"):
        print(f"{options['tabulation']}\tDocker image {img['name']} already exists. Skipping build.")
        return

    if image_exists:
        if not options.get("force_rebuild"):
            print(f"{options['tabulation']}\tDocker image {img['name']} already exists. Skipping build.")
            return
        print(f"{options['tabulation']}\tRemoving existing Docker image: {img['name']}...")
        remove_docker_image(img["name"])

    print(f"{options['tabulation']}\tBuilding Docker image: {img['name']} from {img['dockerfile']}...")
    subprocess.run(
        ["docker", "build", "-f", img["dockerfile"], "-t", img["name"], "."],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
        encoding="utf-8"
    )

def docker_image_exists(img_name: str) -> bool:
    # silence stdout
    result = subprocess.run(
        ["docker", "images", "-q", img_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return result.stdout.strip() != ""

def remove_docker_image(img_name: str):
    subprocess.run(
        ["docker", "rmi", img_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

def create_container(img_name: str, container_name: str | None = None, on_start: str = "true"):
    if container_name is None:
        container_name = img_name
    subprocess.run(
        ["docker", "container", "create", "--name", container_name, img_name, on_start],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True
    )

def remove_container(container_name: str):
    subprocess.run(
        ["docker", "container", "rm", "-f", container_name],
        stdout=subprocess.PIPE,
    )

def copy_from_container(container_name: str, src_path: str, dest_path: Path):
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["docker", "cp", f"{container_name}:{src_path}", dest_path],
        stdout=subprocess.PIPE,
        check=True
    )
