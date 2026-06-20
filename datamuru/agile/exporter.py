from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re

from datamuru.errors import ValidationError


@dataclass(frozen=True)
class AgileIssueDraft:
    title: str
    area: str
    provider: str
    edition: str
    customer_impact: str
    risk: str
    release_target: str

    @property
    def slug(self) -> str:
        slug = re.sub(r"[^A-Za-z0-9]+", "-", self.title.strip().lower()).strip("-")
        return slug or "issue"

    @property
    def labels(self) -> list[str]:
        labels = [
            f"area/{self.area.lower()}",
            f"risk/{self.risk.lower()}",
            f"release/{self.release_target}",
        ]
        if self.provider.lower() != "provider-agnostic":
            labels.append(f"provider/{self.provider.lower()}")
        if self.edition.lower() == "both":
            labels.extend(["edition/oss", "edition/enterprise"])
        else:
            labels.append(f"edition/{self.edition.lower()}")
        return labels

    def to_markdown(self) -> str:
        labels = "\n".join(f"  - {label}" for label in self.labels)
        return "\n".join(
            [
                "---",
                f"title: {self.title}",
                "labels:",
                labels,
                f"milestone: {self.release_target}",
                "---",
                "",
                "## Outcome",
                "",
                f"Deliver `{self.title}` for DataMuru `{self.release_target}`.",
                "",
                "## Planning Fields",
                "",
                f"- Area: `{self.area}`",
                f"- Provider: `{self.provider}`",
                f"- Edition: `{self.edition}`",
                f"- Customer impact: `{self.customer_impact}`",
                f"- Risk: `{self.risk}`",
                f"- Release target: `{self.release_target}`",
                "",
                "## Acceptance Criteria",
                "",
                "- Scope is documented.",
                "- Implementation is covered by automated tests where applicable.",
                "- Documentation or runbook guidance is updated.",
                "- Evidence link is added to the GitHub Project item.",
                "",
            ]
        )

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "area": self.area,
            "provider": self.provider,
            "edition": self.edition,
            "customer_impact": self.customer_impact,
            "risk": self.risk,
            "release_target": self.release_target,
            "labels": self.labels,
            "filename": f"{self.slug}.md",
        }


@dataclass(frozen=True)
class AgileIssueExportResult:
    source: Path
    output_dir: Path
    drafts: list[AgileIssueDraft]
    manifest_path: Path

    def to_dict(self) -> dict:
        return {
            "source": str(self.source),
            "output_dir": str(self.output_dir),
            "manifest_path": str(self.manifest_path),
            "draft_count": len(self.drafts),
            "drafts": [draft.to_dict() for draft in self.drafts],
        }


def export_github_issue_drafts(
    *,
    source_path: str | Path,
    output_dir: str | Path,
    release_target: str | None = None,
) -> AgileIssueExportResult:
    source = Path(source_path).resolve()
    if not source.exists():
        raise ValidationError(
            description="Agile issue export source file was not found.",
            context={"source_path": str(source)},
            suggestion="Pass --source with a markdown file that contains the DataMuru backlog table.",
        )
    drafts = parse_backlog_table(source.read_text(encoding="utf-8"))
    if release_target:
        drafts = [draft for draft in drafts if draft.release_target == release_target]
    if not drafts:
        raise ValidationError(
            description="Agile issue export found no backlog rows to export.",
            context={"source_path": str(source), "release_target": release_target},
            suggestion="Verify the source table has Title, Area, Provider, Edition, Customer impact, Risk, and Release target columns.",
        )

    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    for draft in drafts:
        (output / f"{draft.slug}.md").write_text(draft.to_markdown(), encoding="utf-8")
    manifest_path = output / "manifest.json"
    result = AgileIssueExportResult(
        source=source,
        output_dir=output,
        drafts=drafts,
        manifest_path=manifest_path,
    )
    manifest_path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
    return result


def parse_backlog_table(markdown: str) -> list[AgileIssueDraft]:
    rows = _markdown_tables(markdown)
    for headers, table_rows in rows:
        normalized_headers = [_normalize_header(header) for header in headers]
        required = ["title", "area", "provider", "edition", "customer impact", "risk", "release target"]
        if normalized_headers[: len(required)] != required:
            continue
        drafts: list[AgileIssueDraft] = []
        for row in table_rows:
            cells = dict(zip(normalized_headers, row, strict=False))
            drafts.append(
                AgileIssueDraft(
                    title=cells["title"],
                    area=cells["area"],
                    provider=cells["provider"],
                    edition=cells["edition"],
                    customer_impact=cells["customer impact"],
                    risk=cells["risk"],
                    release_target=cells["release target"],
                )
            )
        return drafts
    return []


def _markdown_tables(markdown: str) -> list[tuple[list[str], list[list[str]]]]:
    lines = markdown.splitlines()
    tables: list[tuple[list[str], list[list[str]]]] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if not _is_table_row(line) or index + 1 >= len(lines) or not _is_separator(lines[index + 1]):
            index += 1
            continue
        headers = _split_row(line)
        index += 2
        rows: list[list[str]] = []
        while index < len(lines) and _is_table_row(lines[index]):
            row = _split_row(lines[index])
            if len(row) == len(headers):
                rows.append(row)
            index += 1
        tables.append((headers, rows))
    return tables


def _is_table_row(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|")


def _is_separator(line: str) -> bool:
    cells = _split_row(line)
    return bool(cells) and all(set(cell.replace(" ", "")) <= {"-", ":"} for cell in cells)


def _split_row(line: str) -> list[str]:
    return [cell.strip().replace("`", "") for cell in line.strip().strip("|").split("|")]


def _normalize_header(header: str) -> str:
    return re.sub(r"\s+", " ", header.strip().lower())
