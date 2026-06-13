from datamuru.core.config import validate_project


def test_open_source_disallows_enterprise_only_features(sample_project):
    config_path = sample_project / "datamuru.yml"
    text = config_path.read_text(encoding="utf-8")
    text = text.replace("compliance_reporting: false", "compliance_reporting: true")
    config_path.write_text(text, encoding="utf-8")

    issues = validate_project(config_path)
    errors = [issue for issue in issues if issue.level == "error"]
    assert any(issue.path == "features.compliance_reporting" for issue in errors)


def test_open_source_disallows_identity_management(sample_project):
    config_path = sample_project / "datamuru.yml"
    text = config_path.read_text(encoding="utf-8")
    text = text.replace("identity_management: false", "identity_management: true")
    config_path.write_text(text, encoding="utf-8")

    issues = validate_project(config_path)
    errors = [issue for issue in issues if issue.level == "error"]
    assert any(issue.path == "features.identity_management" for issue in errors)


def test_enterprise_allows_enterprise_features(sample_project):
    config_path = sample_project / "datamuru.yml"
    text = config_path.read_text(encoding="utf-8")
    text = text.replace("edition: open-source", "edition: enterprise")
    text = text.replace("compliance_reporting: false", "compliance_reporting: true")
    text = text.replace("multi_workspace: false", "multi_workspace: true")
    text = text.replace("hosted_control_plane: false", "hosted_control_plane: true")
    text = text.replace("identity_management: false", "identity_management: true")
    config_path.write_text(text, encoding="utf-8")

    issues = validate_project(config_path)
    errors = [issue for issue in issues if issue.level == "error"]
    assert not errors
