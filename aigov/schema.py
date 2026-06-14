"""Schemas for controls, evidence, and the runtime gate.

A control is a YAML file. The schema below lets us validate the corpus
at load time, before any of it is used to gate a request or generate
an AIBOM. The trade-off: heavier load-time cost, but unparseable YAML
is caught in CI instead of at 3am.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Literal, Optional

import yaml
from pydantic import BaseModel, Field, field_validator


class Framework(str, Enum):
    """The standards we map controls to."""

    ISO_42001 = "iso_42001"
    EU_AI_ACT = "eu_ai_act"
    NIST_AI_RMF = "nist_ai_rmf"
    UK_AI_CYBER = "uk_ai_cyber"
    OWASP_LLM = "owasp_llm"


class EnforcementMode(str, Enum):
    """How a control is enforced at runtime.

    `evidence_only`     The control does not gate anything. It only
                        records evidence (the most common shape — most
                        management-system controls are about having
                        a process, not blocking a request).
    `gate`              The control evaluates at request time and can
                        block. Used for high-risk operational controls
                        like data-classification gates.
    `attestation`       The control requires a periodic human attestation
                        (quarterly, annually). The evidence is the
                        attestation record itself.
    """

    EVIDENCE_ONLY = "evidence_only"
    GATE = "gate"
    ATTESTATION = "attestation"


class Mapping(BaseModel):
    """One control's cross-reference into another framework.

    A single ISO 42001 control can map to multiple EU AI Act articles
    and vice versa, so this is a many-to-many relation expressed at
    the control level.
    """

    framework: Framework
    reference: str = Field(description="e.g. 'Article 12', 'A.7.4', 'GV-1.1'")
    note: Optional[str] = None


class Control(BaseModel):
    """One control in the corpus."""

    id: str = Field(description="primary key, e.g. 'iso42001:A.7.4'")
    framework: Framework
    name: str
    objective: str = Field(description="what the control achieves, in plain English")
    enforcement: EnforcementMode
    mappings: list[Mapping] = Field(default_factory=list)
    evidence_required: list[str] = Field(
        default_factory=list,
        description="list of evidence types this control produces or requires",
    )
    owner: Optional[str] = Field(
        default=None,
        description="suggested owner role (e.g. 'Chief AI Officer', 'Data Steward')",
    )
    cadence: Optional[str] = Field(
        default=None,
        description="for ATTESTATION controls: 'quarterly', 'annually', 'on_change'",
    )
    notes: Optional[str] = None

    @field_validator("id")
    @classmethod
    def _id_shape(cls, v: str) -> str:
        if ":" not in v:
            raise ValueError(f"control id must be 'framework:reference', got {v!r}")
        return v


class Evidence(BaseModel):
    """One evidence record emitted by a control.

    Evidence is a structured fact about the system or its operation. The
    same record may satisfy multiple controls; the harness records the
    cross-references at emit time so audit queries don't have to recompute.
    """

    id: str
    timestamp: datetime
    control_ids: list[str] = Field(min_length=1)
    type: Literal[
        "audit_log_reference",
        "attestation_record",
        "policy_decision",
        "data_classification",
        "model_release",
        "incident_postmortem",
        "training_record",
        "vendor_assessment",
        "impact_assessment",
        "test_run",
    ]
    payload: dict[str, Any]
    source_system: str = Field(description="e.g. 'agentic-harness', 'mlflow', 'langfuse'")

    @classmethod
    def now(cls, **kwargs) -> "Evidence":
        kwargs.setdefault("timestamp", datetime.now(tz=timezone.utc))
        return cls(**kwargs)


def load_controls(directory: Path) -> dict[str, Control]:
    """Load every YAML file under ``directory`` as a Control.

    Returns a dict keyed by control id so callers can look controls up
    by their cross-reference. Duplicate ids raise; controls do not have
    a merge semantic on purpose.
    """

    out: dict[str, Control] = {}
    for path in sorted(directory.rglob("*.yaml")):
        data = yaml.safe_load(path.read_text())
        control = Control.model_validate(data)
        if control.id in out:
            raise ValueError(f"duplicate control id {control.id} at {path}")
        out[control.id] = control
    return out
