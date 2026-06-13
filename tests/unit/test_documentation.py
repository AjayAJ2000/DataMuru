import re
from pathlib import Path

import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = REPOSITORY_ROOT / "docs"
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def _nav_paths(value):
    if isinstance(value, str):
        yield value
        return
    if isinstance(value, list):
        for item in value:
            yield from _nav_paths(item)
        return
    if isinstance(value, dict):
        for item in value.values():
            yield from _nav_paths(item)


def test_mkdocs_navigation_targets_exist():
    config = yaml.safe_load((REPOSITORY_ROOT / "mkdocs.yml").read_text(encoding="utf-8"))
    missing = [
        path
        for path in _nav_paths(config["nav"])
        if not (DOCS_ROOT / path).is_file()
    ]

    assert missing == []


def test_relative_markdown_links_resolve():
    broken: list[str] = []
    for page in DOCS_ROOT.rglob("*.md"):
        text = page.read_text(encoding="utf-8")
        for target in MARKDOWN_LINK.findall(text):
            target = target.split("#", 1)[0].strip()
            if not target or "://" in target or target.startswith(("mailto:", "#")):
                continue
            resolved = (page.parent / target).resolve()
            if not resolved.exists():
                broken.append(f"{page.relative_to(REPOSITORY_ROOT)} -> {target}")

    assert broken == []
