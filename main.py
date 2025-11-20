# -*- coding: utf-8 -*-

import os
import yaml
from typing import Any, List


def generate_readme() -> list[str]:
    contents: list[str] = []
    for root, _, files in os.walk("./blog"):
        if root == "./blog/images":
            continue
        keys = root.replace("./blog/", "").replace("./blog", "").split("/")
        contents.append(f"{'#' * len(keys)}  {keys[-1] or '  '}")
        for file in files:
            if not file.endswith(".md") or file == "index.md":
                continue
            contents.append(f"- [{os.path.basename(file)}]({os.path.join(root, file).replace('./', '')})")
        contents.append("")
    return contents

def update_mkdocs():
    """Update mkdocs.yml file with the latest blog post entries."""
    with open("./mkdocs.yml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    def generate_yaml_nav(dir: str) -> List[Any]:
        """Recursively generate YAML navigation structure."""
        nav: List[Any] = []
        sub_dirs: List[str] = []
        for item in os.listdir(dir):
            if item == "images":
                continue
            if os.path.isdir(os.path.join(dir, item)):
                sub_dirs.append(os.path.join(dir, item))
            elif item.endswith(".md") and item != "index.md":
                nav.append({item.replace(".md", ""): f"{dir}/{item}".replace("./blog/", "")})
        for dir in sub_dirs:
            nav.append({os.path.basename(dir): generate_yaml_nav(dir)})
        return nav

    config["nav"][0]["Home"] = generate_yaml_nav("./blog")
    with open("./mkdocs.yml", "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False, default_flow_style=False)


if __name__ == '__main__':
    body = generate_readme()
    with open("./README.md", "w", encoding="utf-8") as f:
        f.write("\n".join(body))
