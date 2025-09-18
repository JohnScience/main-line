import sys

from scripts.common.docker_images import DOCKER_IMAGES, PurposeSpecificDataVariant, extract_artifact
from scripts.common.git import get_git_root

SAME_DEST_IMAGES: dict[str, list[str]] = {
    "api-client": ["main-line-api_client", "main-line-api_client_raw"]
}

DEFAULT_PREFERENCES: dict[str, str] = {
    "api-client": "main-line-api_client"
}

def collect_preferences(argv: list[str] = sys.argv[1:]) -> dict[str, str]:
    preferences = DEFAULT_PREFERENCES.copy()
    expecting_preference = False
    for arg in argv:
        if arg == "-p":
            expecting_preference = True
            continue
        if expecting_preference:
            for dest in SAME_DEST_IMAGES.keys():
                if arg in SAME_DEST_IMAGES[dest]:
                    preferences[dest] = arg
                    break
            expecting_preference = False
    return preferences

if __name__ == "__main__":
    preferences = collect_preferences()
    git_root = get_git_root()
    
    print("Extracting artifacts...")
    for img in DOCKER_IMAGES:
        if not isinstance(img["purpose_specific_data"], PurposeSpecificDataVariant.DataOnly):
            continue
        if bool(set(img["purpose_specific_data"].dest) & SAME_DEST_IMAGES.keys()):
            if not any(preferences[dest] == img["name"] for dest in img["purpose_specific_data"].dest):
                continue
        extract_artifact(img, "\t")
    print("Finished extracting artifacts.")
