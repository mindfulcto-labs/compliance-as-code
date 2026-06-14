"""Schema and control-loading tests."""

from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

from aigov import Control, EnforcementMode, Evidence, Framework, Mapping, load_controls


def test_control_id_must_have_colon():
    with pytest.raises(ValueError):
        Control(
            id="A.7.4",  # missing 'iso42001:' prefix
            framework=Framework.ISO_42001,
            name="Data provenance",
            objective="track data origin",
            enforcement=EnforcementMode.EVIDENCE_ONLY,
        )


def test_control_with_mappings():
    c = Control(
        id="iso42001:A.6.2.7",
        framework=Framework.ISO_42001,
        name="AI system event logs",
        objective="Maintain event logs for operational AI systems.",
        enforcement=EnforcementMode.EVIDENCE_ONLY,
        mappings=[
            Mapping(framework=Framework.EU_AI_ACT, reference="Article 12"),
        ],
    )
    assert len(c.mappings) == 1
    assert c.mappings[0].framework == Framework.EU_AI_ACT


def test_evidence_now_sets_utc_timestamp():
    ev = Evidence.now(
        id="ev-1",
        control_ids=["iso42001:A.7.4"],
        type="audit_log_reference",
        payload={"run_id": "r1"},
        source_system="agentic-harness",
    )
    assert ev.timestamp.tzinfo is not None
    assert ev.timestamp <= datetime.now(tz=timezone.utc)


def test_evidence_requires_at_least_one_control():
    with pytest.raises(ValueError):
        Evidence(
            id="ev-bad",
            timestamp=datetime.now(tz=timezone.utc),
            control_ids=[],  # empty
            type="audit_log_reference",
            payload={},
            source_system="x",
        )


def test_load_controls_round_trip(tmp_path: Path):
    (tmp_path / "c1.yaml").write_text(
        yaml.safe_dump(
            {
                "id": "iso42001:A.7.4",
                "framework": "iso_42001",
                "name": "Data provenance",
                "objective": "Track origin and transformations of data used by AI systems.",
                "enforcement": "evidence_only",
                "mappings": [{"framework": "eu_ai_act", "reference": "Article 10"}],
                "evidence_required": ["data_classification"],
            }
        )
    )
    corpus = load_controls(tmp_path)
    assert "iso42001:A.7.4" in corpus
    assert corpus["iso42001:A.7.4"].name == "Data provenance"


def test_load_controls_rejects_duplicate_ids(tmp_path: Path):
    body = {
        "id": "iso42001:A.1",
        "framework": "iso_42001",
        "name": "X",
        "objective": "y",
        "enforcement": "evidence_only",
    }
    (tmp_path / "a.yaml").write_text(yaml.safe_dump(body))
    (tmp_path / "b.yaml").write_text(yaml.safe_dump(body))
    with pytest.raises(ValueError, match="duplicate control id"):
        load_controls(tmp_path)
