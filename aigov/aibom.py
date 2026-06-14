"""SPDX 3.0 AI Profile emitter.

SPDX 3.0 introduced an AI Profile in late 2024 that gives us a vocabulary
for describing AI/ML systems in a Bill of Materials: models, datasets,
training-time hyperparameters, the chain from data to weights to deployed
artefact. This module emits a minimal-but-valid SPDX 3.0 document so a
site can drop it into its release artefact and ship.

We deliberately do NOT try to be a full SPDX implementation. We emit the
subset that an AI Act conformity assessment will ask for. Sites who need
broader SPDX coverage should write the rest of the document and merge.

The trade-off: minimal scope means smaller blast radius if SPDX 3.0 spec
shifts; broader scope would mean fewer downstream tools the site needs
to write themselves. We pick smaller blast radius.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class AIDataset(BaseModel):
    """A dataset that contributed to a model."""

    name: str
    version: Optional[str] = None  # type: ignore[name-defined]
    license: Optional[str] = None  # type: ignore[name-defined]
    source: Optional[str] = None  # type: ignore[name-defined]
    classification: Optional[str] = None  # type: ignore[name-defined]
    notes: Optional[str] = None  # type: ignore[name-defined]


# Local typing import — kept here so the module file can be read top-to-bottom.
from typing import Optional  # noqa: E402


class AIModel(BaseModel):
    name: str
    version: str
    base_model: Optional[str] = None
    license: Optional[str] = None
    parameters: Optional[int] = None
    training_method: Optional[str] = None
    datasets: list[AIDataset] = Field(default_factory=list)
    use_cases: list[str] = Field(default_factory=list)
    out_of_scope_use: list[str] = Field(default_factory=list)
    evaluation: list[str] = Field(default_factory=list)


class AISystem(BaseModel):
    name: str
    version: str
    purpose: str
    risk_classification: Optional[str] = None
    deployment_context: Optional[str] = None
    models: list[AIModel] = Field(default_factory=list)


def emit_spdx3(system: AISystem) -> dict[str, Any]:
    """Render an AISystem into an SPDX 3.0 JSON-LD document.

    Returns a dict that can be dumped to JSON. We keep the dict shape
    explicit (no auto-conversion magic) so the output is auditable line
    by line.
    """

    now = datetime.now(tz=timezone.utc).isoformat()

    graph: list[dict[str, Any]] = [
        {
            "spdxId": "SPDXRef-DOCUMENT",
            "type": "SpdxDocument",
            "name": f"{system.name} {system.version}",
            "creationInfo": {
                "created": now,
                "createdBy": ["Tool: aigov compliance-as-code"],
                "specVersion": "3.0.1",
            },
        },
        {
            "spdxId": f"SPDXRef-System-{_slug(system.name)}",
            "type": "AIPackage",
            "name": system.name,
            "packageVersion": system.version,
            "primaryPurpose": "ai-system",
            "description": system.purpose,
            "extension": [
                {"type": "AIExtension", "riskClassification": system.risk_classification}
            ] if system.risk_classification else [],
        },
    ]

    for model in system.models:
        graph.append(
            {
                "spdxId": f"SPDXRef-Model-{_slug(model.name)}-{_slug(model.version)}",
                "type": "AIPackage",
                "name": model.name,
                "packageVersion": model.version,
                "primaryPurpose": "model",
                "licenseDeclared": model.license,
                "baseModel": model.base_model,
                "modelParameters": model.parameters,
                "trainingMethod": model.training_method,
                "useCases": model.use_cases,
                "outOfScopeUse": model.out_of_scope_use,
                "evaluation": model.evaluation,
            }
        )
        for ds in model.datasets:
            graph.append(
                {
                    "spdxId": f"SPDXRef-Dataset-{_slug(ds.name)}",
                    "type": "DatasetPackage",
                    "name": ds.name,
                    "packageVersion": ds.version,
                    "licenseDeclared": ds.license,
                    "originator": ds.source,
                    "dataClassification": ds.classification,
                    "comment": ds.notes,
                }
            )

    return {
        "@context": "https://spdx.org/rdf/3.0.1/spdx-context.jsonld",
        "@graph": graph,
    }


def _slug(value: str) -> str:
    """Cheap, deterministic slug for SPDX identifiers."""
    return "".join(c if c.isalnum() else "-" for c in value).strip("-")
