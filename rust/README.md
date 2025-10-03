# Rust Workspace

## Useful Commands

```bash
cargo tree --depth workspace
```

Based on the output of the above command, you can request your favorite LLM to generate a graphviz `.dot` file representing the dependency graph of your Rust workspace. This can help visualize the relationships between different crates and their dependencies, e.g. like [this](https://dreampuf.github.io/GraphvizOnline/?engine=dot#digraph%20workspace_deps%20%7B%0D%0A%20%20%20%20rankdir%3DLR%3B%0D%0A%20%20%20%20node%20%5Bshape%3Dbox%2C%20style%3Drounded%5D%3B%0D%0A%0D%0A%20%20%20%20backend%20-%3E%20backend_lib%3B%0D%0A%20%20%20%20backend_lib%20-%3E%20mnln_core_items%3B%0D%0A%20%20%20%20backend_lib%20-%3E%20mnln_env%3B%0D%0A%20%20%20%20backend_lib%20-%3E%20shared_items_lib%3B%0D%0A%0D%0A%20%20%20%20mnln_env%20-%3E%20git_repo_root%3B%0D%0A%20%20%20%20shared_items_lib%20-%3E%20mnln_core_items%3B%0D%0A%0D%0A%20%20%20%20export_shared_types%20-%3E%20shared_items_lib%3B%0D%0A%0D%0A%20%20%20%20mnln_time%20-%3E%20mnln_core_items%3B%0D%0A%0D%0A%20%20%20%20object_storage%20-%3E%20browser_supported_img_format%3B%0D%0A%20%20%20%20object_storage%20-%3E%20mnln_core_items%3B%0D%0A%20%20%20%20object_storage%20-%3E%20mnln_env%3B%0D%0A%20%20%20%20object_storage%20-%3E%20mnln_time%3B%0D%0A%0D%0A%20%20%20%20openapi_spec%20-%3E%20backend_lib%3B%0D%0A%7D%0D%0A).

