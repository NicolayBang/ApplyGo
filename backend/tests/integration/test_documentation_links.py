from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[3]
MARKDOWN_PATH_PATTERN = re.compile(r"`([^`]+\.md)`")


def _read_repo_file(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _section(text: str, heading: str) -> str:
    marker = f"## {heading}"
    start = text.index(marker)
    next_heading = text.find("\n## ", start + len(marker))
    if next_heading == -1:
        return text[start:]
    return text[start:next_heading]


def _markdown_paths(text: str) -> list[str]:
    return MARKDOWN_PATH_PATTERN.findall(text)


def test_root_readme_reviewer_entry_points_exist() -> None:
    readme = _read_repo_file("README.md")
    reviewer_entry_points = _section(readme, "M1 demo path")
    paths = _markdown_paths(reviewer_entry_points)

    assert paths
    for relative_path in paths:
        assert (REPO_ROOT / relative_path).is_file()


def test_capstone_index_entries_exist() -> None:
    capstone_index = _read_repo_file("docs/capstone/README.md")
    start_here = _section(capstone_index, "Start Here")
    paths = _markdown_paths(start_here)

    assert paths
    for relative_path in paths:
        assert (REPO_ROOT / "docs" / "capstone" / relative_path).is_file()
