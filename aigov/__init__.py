"""aigov — ISO/IEC 42001 Annex A and EU AI Act Articles 12-15 as code.

Public API. Sites import from ``aigov`` (not the submodules) so the
internal layout can change without breaking callers.
"""

from aigov.aibom import AIDataset, AIModel, AISystem, emit_spdx3
from aigov.schema import (
    Control,
    EnforcementMode,
    Evidence,
    Framework,
    Mapping,
    load_controls,
)

__all__ = [
    "AIDataset",
    "AIModel",
    "AISystem",
    "Control",
    "EnforcementMode",
    "Evidence",
    "Framework",
    "Mapping",
    "emit_spdx3",
    "load_controls",
]
