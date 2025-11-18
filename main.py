# -*- coding: utf-8 -*-

import os


def generate_readme(dir: str) -> list[str]:
    contents: list[str] = []
    for root, _, files in os.walk(dir):
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


if __name__ == '__main__':
    body = generate_readme("./blog")
    with open("./README.md", "w", encoding="utf-8") as f:
        f.write("\n".join(body))
