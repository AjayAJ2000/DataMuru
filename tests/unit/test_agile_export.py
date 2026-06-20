import json

from click.testing import CliRunner

from datamuru.agile.exporter import parse_backlog_table
from datamuru.cli.main import cli


ROADMAP_TABLE = """
# Roadmap

| Title | Area | Provider | Edition | Customer impact | Risk | Release target |
| --- | --- | --- | --- | --- | --- | --- |
| Resumable enterprise import jobs | Import | Provider-agnostic | Enterprise | Cost | High | 0.4.0a0 |
| GitHub Projects issue export command | Core | Provider-agnostic | Both | Developer experience | Low | 0.4.0a0 |
| Hosted control plane product architecture | Enterprise | Provider-agnostic | Enterprise | Production | High | 0.5.0a0 |
"""


def test_parse_backlog_table_extracts_issue_drafts():
    drafts = parse_backlog_table(ROADMAP_TABLE)

    assert [draft.title for draft in drafts] == [
        "Resumable enterprise import jobs",
        "GitHub Projects issue export command",
        "Hosted control plane product architecture",
    ]
    assert drafts[1].labels == [
        "area/core",
        "risk/low",
        "release/0.4.0a0",
        "edition/oss",
        "edition/enterprise",
    ]


def test_agile_export_writes_github_issue_drafts(tmp_path):
    source = tmp_path / "roadmap.md"
    source.write_text(ROADMAP_TABLE, encoding="utf-8")
    output_dir = tmp_path / "issue-drafts"

    result = CliRunner().invoke(
        cli,
        [
            "--no-banner",
            "agile",
            "export",
            "--source",
            str(source),
            "--out",
            str(output_dir),
            "--release-target",
            "0.4.0a0",
        ],
    )

    assert result.exit_code == 0
    assert "Exported 2 GitHub issue draft(s)" in result.output
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["draft_count"] == 2
    draft_text = (output_dir / "github-projects-issue-export-command.md").read_text(encoding="utf-8")
    assert "title: GitHub Projects issue export command" in draft_text
    assert "edition/oss" in draft_text
    assert "edition/enterprise" in draft_text


def test_agile_export_json_output(tmp_path):
    source = tmp_path / "roadmap.md"
    source.write_text(ROADMAP_TABLE, encoding="utf-8")

    result = CliRunner().invoke(
        cli,
        [
            "agile",
            "export",
            "--source",
            str(source),
            "--out",
            str(tmp_path / "issue-drafts"),
            "--release-target",
            "0.5.0a0",
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["draft_count"] == 1
    assert payload["drafts"][0]["title"] == "Hosted control plane product architecture"
