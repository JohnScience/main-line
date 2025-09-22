import secrets

from .common.git import get_git_root

if __name__ == "__main__":
    git_root = get_git_root()
    # create $(git_root)/secrets/jwt_signing_key.env if it doesn't exist
    with open(f"{git_root}/secrets/jwt_signing_key.env", "a+") as f:
        f.seek(0)
        content = f.read().strip()
        if not content:
            secret = secrets.token_urlsafe(256)
            f.write(f"JWT_SIGNING_KEY={secret}\n")
            print(f"Generated new JWT signing key and saved to {git_root}/secrets/jwt_signing_key.env")
        else:
            print(f"JWT signing key already exists in {git_root}/secrets/jwt_signing_key.env")
