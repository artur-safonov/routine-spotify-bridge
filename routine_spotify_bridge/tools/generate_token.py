"""Generate private, matching add-on/display settings without printing a secret."""
import argparse
import json
import os
import secrets
from pathlib import Path


def write_private(path: Path, content: str) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
        stream.write(content)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path(__file__).resolve().parents[1] / ".private",
    )
    directory = parser.parse_args().output_dir.resolve()
    names = ("bridge-token.txt", "addon-options.fragment.json", "display-secrets.fragment.yaml")
    if any((directory / name).exists() for name in names):
        parser.error("Private token files already exist; reuse them or choose a new output directory.")
    directory.mkdir(parents=True, exist_ok=True)
    # This directory must stay private even if generated outside the package.
    if not (directory / ".gitignore").exists():
        write_private(directory / ".gitignore", "*\n!.gitignore\n")
    token = secrets.token_urlsafe(32)
    write_private(directory / names[0], token + "\n")
    write_private(directory / names[1], json.dumps({"bridge_token": token}, indent=2) + "\n")
    write_private(directory / names[2], f'spotify_bridge_token: "{token}"\n')
    print(f"Private token and matching configuration fragments saved to: {directory}")
    print("Merge the fragments into your add-on options and display secrets; do not publish them.")


if __name__ == "__main__":
    main()
