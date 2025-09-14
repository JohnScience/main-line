import subprocess

def get_git_root(path=".") -> str | None:
    """
    Return the absolute path to the root of the Git repository containing `path`,
    or None if `path` is not inside a Git repo.
    """
    try:
        result = subprocess.run(
            ["git", "-C", path, "rev-parse", "--show-toplevel"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

if __name__ == "__main__":
    git_root = get_git_root()
    if git_root:
        print(git_root)
    else:
        print("Not inside a Git repository or Git is not installed.")
        exit(1)
