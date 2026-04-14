from scripts.common.docker import (
    BuildOptions,
    docker_image_exists,
    get_registry_tagged_name,
    push_image,
    remove_docker_image,
    tag_image,
)
from scripts.common.docker_images import (
    DOCKER_IMAGES,
    build_all_images,
    extract_artifact,
    PurposeSpecificDataVariant,
)
from scripts.bootstrap_kind_cluster.steps_base import Step, StepKind, CliArg
from scripts.common.check_result import CheckPassed, CheckFailed, CheckResult

def check_images_pushed(registry_host: str = 'localhost', registry_port: int = 5000, **kwargs) -> CheckResult:
    """Check that all non-intermediate images exist in the registry."""
    registry = f"{registry_host}:{registry_port}"
    images_to_check = [img for img in DOCKER_IMAGES if img["name"] is not None and not img["is_intermediate"]]
    missing = [
        img["name"] for img in images_to_check
        if not docker_image_exists(get_registry_tagged_name(img["name"], registry))
    ]
    if missing:
        return CheckFailed(errors=[f"Image not found in registry {registry}: {name}" for name in missing])
    return CheckPassed()

def build_and_push_all_images(registry_host: str, registry_port: int, force_rebuild: bool = False) -> bool:
    """
    Build all Docker images, tag them for the registry, and push them.
    
    Workflow:
    1. Build all images in dependency order using docker_images.build_all_images()
    2. Push each built image to the private registry
    3. Extract artifacts from data-only images
    
    Args:
        registry_host: Registry hostname (e.g., "localhost")
        registry_port: Registry port number
        force_rebuild: Whether to force rebuild existing images
    
    Returns:
        bool: True if all operations successful, False otherwise
    """
    print("\n=== Building and Pushing All Images ===")
    
    registry = f"{registry_host}:{registry_port}"
    
    # Build all images with registry tagging
    build_options: BuildOptions = {
        "tabulation": "",
        "force_rebuild": force_rebuild,
        "private_registry": registry,
    }
    
    try:
        print(f"\nBuilding images (tagged for {registry})...")
        built_images = build_all_images(build_options)
        
        if not built_images:
            print("✗ No images were built")
            return False
        
        # Tag and push all images to the registry
        print(f"\nTagging and pushing {len(built_images)} images to registry...")
        for image_name in built_images:
            registry_image = get_registry_tagged_name(image_name, registry)
            
            try:
                # Tag the image for the registry if not already tagged during build
                if not docker_image_exists(registry_image):
                    print(f"  Tagging {image_name} as {registry_image}...")
                    tag_image(image_name, registry_image)
                
                # Push to registry
                print(f"  Pushing {registry_image}...")
                push_image(registry_image)
                print(f"  ✓ Successfully pushed {registry_image}")
            except Exception as e:
                print(f"  ✗ Failed to push {registry_image}: {e}")
                return False
        
        # Extract artifacts from data-only images
        print("\nExtracting artifacts from data-only images...")
        data_only_images = [
            img for img in DOCKER_IMAGES 
            if img["name"] is not None 
            and isinstance(img["purpose_specific_data"], PurposeSpecificDataVariant.DataOnly)
        ]
        
        if data_only_images:
            for img in data_only_images:
                try:
                    extract_artifact(img, "  ")
                except Exception as e:
                    print(f"  ⚠ Warning: Failed to extract artifact from {img['name']}: {e}")
                    # Don't fail the entire process for artifact extraction failures
        else:
            print("  No data-only images to extract artifacts from.")
        
        print(f"\n✓ Successfully built and pushed all {len(built_images)} images to {registry}")
        return True
        
    except Exception as e:
        print(f"\n✗ Failed to build and push images: {e}")
        return False

def cleanup_images(registry_host: str = "localhost", registry_port: int = 5000) -> bool:
    """
    Remove locally built images (both local and registry-tagged versions).
    
    Args:
        registry_host: Registry hostname
        registry_port: Registry port number
    
    Returns:
        bool: True if successful, False otherwise
    """
    print("\nCleaning up Docker images...")
    
    registry = f"{registry_host}:{registry_port}"
    removed_count = 0
    failed_count = 0
    
    for img in DOCKER_IMAGES:
        if img["name"] is None:
            continue
        
        local_name = img["name"]
        registry_name = get_registry_tagged_name(local_name, registry)
        
        # Remove registry-tagged image
        if docker_image_exists(registry_name):
            try:
                remove_docker_image(registry_name)
                print(f"  ✓ Removed {registry_name}")
                removed_count += 1
            except Exception as e:
                print(f"  ✗ Failed to remove {registry_name}: {e}")
                failed_count += 1
        
        # Remove local image
        if docker_image_exists(local_name):
            try:
                remove_docker_image(local_name)
                print(f"  ✓ Removed {local_name}")
                removed_count += 1
            except Exception as e:
                print(f"  ✗ Failed to remove {local_name}: {e}")
                failed_count += 1
    
    if removed_count > 0:
        print(f"\n✓ Removed {removed_count} images")
    else:
        print("\nℹ No images found to remove")
    
    if failed_count > 0:
        print(f"⚠ Failed to remove {failed_count} images")
        return False
    
    return True

BUILD_AND_PUSH_IMAGES = Step(
    name="build_and_push_images",
    description="Builds and pushes all Docker images to the private registry so that later they can be accessed by the 'kind'-powered cluster",
    perform=lambda **kwargs: build_and_push_all_images(**kwargs),
    check=lambda **kwargs: check_images_pushed(**kwargs),
    rollback=lambda registry_host='localhost', registry_port=5000, **kwargs: cleanup_images(registry_host, registry_port),
    args={
        'registry_host': 'localhost',
        'registry_port': 5000,
        'force_rebuild': False
    },
    rollback_flag='cleanup_images',
    step_kind=StepKind.Optional(skip_flag='skip_build'),
    cli_arg_mappings={'registry_port': 'port', 'force_rebuild': 'force_rebuild'},
    cli_args=[
        CliArg(
            name='port',
            arg_type=int,
            default=5000,
            help='Registry port',
            step_description='Registry port for pushing built images'
        ),
        CliArg(
            name='force_rebuild',
            arg_type=bool,
            default=False,
            help='Force rebuild Docker images',
            step_description='Rebuild all images even if they already exist'
        )
    ],
    depends_on=['start_registry']
)
