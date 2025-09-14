from scripts.common.docker_images import DOCKER_IMAGES, PurposeSpecificDataVariant, extract_artifact
from scripts.common.git import get_git_root

if __name__ == "__main__":
    git_root = get_git_root()
    print("Extracting artifacts...")
    for img in DOCKER_IMAGES:
        if isinstance(img["purpose_specific_data"], PurposeSpecificDataVariant.DataOnly):
            extract_artifact(img, "\t")
    print("Finished extracting artifacts.")
