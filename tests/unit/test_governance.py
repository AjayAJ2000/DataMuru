from datamuru.core.config import load_project
from datamuru.governance.masking import compile_masking_resources
from datamuru.governance.rbac import compile_rbac_resources
from datamuru.governance.taxonomy import compile_taxonomy_resources


def test_governance_compilation(sample_project):
    project = load_project(sample_project / "datamuru.yml")
    taxonomy = compile_taxonomy_resources(project.governance)
    rbac = compile_rbac_resources(project.governance)
    masks = compile_masking_resources(project.governance)
    assert taxonomy
    assert rbac
    assert masks
