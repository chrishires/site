import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # site repo root
MANIFEST = ROOT / "posts.json"
DEST_ROOT = ROOT / "posts"


def run(cmd, cwd=None):
    subprocess.check_call(cmd, cwd=cwd)


def copy_tree(src: Path, dst: Path):
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.name.startswith("."):
            continue
        if item.is_dir():
            shutil.copytree(item, dst / item.name, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dst / item.name)


def main():
    if not MANIFEST.exists():
        raise FileNotFoundError(f"Missing {MANIFEST}")

    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    posts = data.get("posts", [])
    if not posts:
        print("No posts found in posts.json")
        return

    DEST_ROOT.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)

        for p in posts:
            slug = p["slug"]
            repo = p["repo"]
            notebook = p.get("notebook", "post.ipynb")

            print(f"Syncing {slug} from {repo} ...")

            clone_dir = tmpdir / slug
            run(["git", "clone", "--depth", "1", f"https://github.com/{repo}.git", str(clone_dir)])

            nb_path = clone_dir / notebook
            if not nb_path.exists():
                raise FileNotFoundError(f"Notebook not found: {repo}/{notebook}")

            out_dir = DEST_ROOT / slug
            if out_dir.exists():
                shutil.rmtree(out_dir)
            out_dir.mkdir(parents=True, exist_ok=True)

            # Rename to index.ipynb so URL is /posts/<slug>/
            shutil.copy2(nb_path, out_dir / "index.ipynb")

            # Copy commonly-used asset folders if present
            for folder in ["images", "figures", "data", f"{Path(notebook).stem}_files"]:
                src = clone_dir / folder
                if src.exists() and src.is_dir():
                    copy_tree(src, out_dir / folder)

    print("Done syncing posts.")


if __name__ == "__main__":
    main()