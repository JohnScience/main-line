import subprocess
import platform

from scripts.common.cloud_provider_kind import expose_kind_cluster_network
from scripts.kind_cluster.index import KIND_CLUSTER_NAME

def main():
    print(f"Exposing the network for {KIND_CLUSTER_NAME}...")
    # if Linux, skip
    if platform.system() == "Linux":
        print("Linux detected, MetalLB is meant to handle exposure.")
        return
    
    # If not MacOS or Windows, warn about lack of support
    if platform.system() not in ["Darwin", "Windows"]:
        print("Warning: Network exposure is only supported on MacOS and Windows.")
        return
    
    ip_address = expose_kind_cluster_network(KIND_CLUSTER_NAME)
    print(f"✓ Exposed network IP address: {ip_address}")

if __name__ == "__main__":
    main()