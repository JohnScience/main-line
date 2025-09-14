import sys

from .common.docker_images import DOCKER_IMAGES
from .common.docker import BuildOptions, build_docker_image, docker_image_exists, remove_docker_image

def build_intermediate_images(options: BuildOptions):
    print(f"{options["tabulation"]}Building intermediate Docker images:")
    for img in DOCKER_IMAGES:
        if not img["is_intermediate"]:
            continue
        if not img["name"]:
            continue
        build_docker_image(img, {**options, "tabulation": options["tabulation"] + "\t" })

def print_intermediate_image_availability(tabulation: str = ""):
    print(f"{tabulation}Checking intermediate Docker image availability:")
    for img in DOCKER_IMAGES:
        if not img["name"]:
            continue
        if docker_image_exists(img["name"]):
            print(f"{tabulation}\tDocker image {img['name']} already exists.")
        else:
            print(f"{tabulation}\tDocker image {img['name']} does not exist.")

if __name__ == "__main__":
    force_rebuild = False
    if "-f" in sys.argv[1:]:
        force_rebuild = True

    print_intermediate_image_availability()
    options: BuildOptions = {
        "force_rebuild": force_rebuild,
        "tabulation": ""
    }
    build_intermediate_images(options)
