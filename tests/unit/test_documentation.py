import re
from pathlib import Path

import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = REPOSITORY_ROOT / "docs"
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
MARKDOWN_LINK_WITH_TEXT = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")
MARKDOWN_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
VAGUE_LINK_TEXT = {"click here", "here", "this", "this link", "read more"}


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


def test_markdown_pages_have_one_top_level_heading():
    invalid: list[str] = []
    for page in DOCS_ROOT.rglob("*.md"):
        headings = [
            line for line in page.read_text(encoding="utf-8").splitlines()
            if line.startswith("# ")
        ]
        if len(headings) != 1:
            invalid.append(f"{page.relative_to(REPOSITORY_ROOT)}: {len(headings)} H1 headings")

    assert invalid == []


def test_markdown_links_use_descriptive_text():
    vague: list[str] = []
    for page in DOCS_ROOT.rglob("*.md"):
        text = page.read_text(encoding="utf-8")
        for label, target in MARKDOWN_LINK_WITH_TEXT.findall(text):
            if label.strip().lower() in VAGUE_LINK_TEXT:
                vague.append(
                    f"{page.relative_to(REPOSITORY_ROOT)}: {label!r} -> {target}"
                )

    assert vague == []


def test_markdown_images_have_alt_text():
    missing: list[str] = []
    for page in DOCS_ROOT.rglob("*.md"):
        text = page.read_text(encoding="utf-8")
        for alt_text, target in MARKDOWN_IMAGE.findall(text):
            if not alt_text.strip():
                missing.append(f"{page.relative_to(REPOSITORY_ROOT)} -> {target}")

    assert missing == []


def test_public_documentation_has_no_local_windows_paths():
    invalid: list[str] = []
    local_path = re.compile(r"\b[A-Za-z]:\\")
    for page in [REPOSITORY_ROOT / "README.md", *DOCS_ROOT.rglob("*.md")]:
        if local_path.search(page.read_text(encoding="utf-8")):
            invalid.append(str(page.relative_to(REPOSITORY_ROOT)))

    assert invalid == []
