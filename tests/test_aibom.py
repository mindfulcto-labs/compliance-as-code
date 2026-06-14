"""SPDX 3.0 AIBOM emitter tests."""

from aigov import AIDataset, AIModel, AISystem, emit_spdx3


def _sample_system() -> AISystem:
    return AISystem(
        name="triage-bot",
        version="1.2.0",
        purpose="Route purchase requests under autonomy budgets and blast-radius policy.",
        risk_classification="limited",
        deployment_context="production",
        models=[
            AIModel(
                name="claude-3-5-sonnet",
                version="20240620",
                base_model="anthropic/claude-3-5-sonnet",
                license="proprietary",
                use_cases=["Procurement request classification"],
                out_of_scope_use=[
                    "Final approval of purchase orders without human review."
                ],
                evaluation=["End-to-end test in tests/test_procurement_triage.py"],
                datasets=[
                    AIDataset(
                        name="procurement-sop-corpus",
                        version="2026-Q1",
                        license="internal-confidential",
                        source="Procurement policy v3.4",
                        classification="internal",
                    )
                ],
            )
        ],
    )


def test_emit_returns_jsonld_with_context():
    doc = emit_spdx3(_sample_system())
    assert doc["@context"].startswith("https://spdx.org/")
    assert "@graph" in doc


def test_document_node_present():
    doc = emit_spdx3(_sample_system())
    doc_node = [n for n in doc["@graph"] if n.get("type") == "SpdxDocument"]
    assert len(doc_node) == 1
    assert doc_node[0]["name"] == "triage-bot 1.2.0"


def test_system_node_carries_risk_classification():
    doc = emit_spdx3(_sample_system())
    sys_nodes = [
        n
        for n in doc["@graph"]
        if n.get("type") == "AIPackage" and n.get("primaryPurpose") == "ai-system"
    ]
    assert len(sys_nodes) == 1
    assert sys_nodes[0]["extension"][0]["riskClassification"] == "limited"


def test_model_and_dataset_nodes_emitted():
    doc = emit_spdx3(_sample_system())
    model_nodes = [
        n
        for n in doc["@graph"]
        if n.get("type") == "AIPackage" and n.get("primaryPurpose") == "model"
    ]
    dataset_nodes = [n for n in doc["@graph"] if n.get("type") == "DatasetPackage"]
    assert len(model_nodes) == 1
    assert len(dataset_nodes) == 1
    assert dataset_nodes[0]["name"] == "procurement-sop-corpus"


def test_system_without_risk_classification_omits_extension():
    system = _sample_system()
    system.risk_classification = None
    doc = emit_spdx3(system)
    sys_nodes = [
        n
        for n in doc["@graph"]
        if n.get("type") == "AIPackage" and n.get("primaryPurpose") == "ai-system"
    ]
    assert sys_nodes[0]["extension"] == []
