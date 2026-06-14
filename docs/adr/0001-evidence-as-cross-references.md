# ADR 0001: Evidence as cross-references, not copies

## Status

Accepted, v0.1.

## Context

When an agent run produces an audit log entry, ISO 42001 Annex A.6.2.7 ("AI system event logs") and EU AI Act Article 12 ("Record-keeping") both call that out as required evidence. We need a place to record that "yes, this audit log entry satisfies these two controls."

The options:

1. **Copy the audit log payload into the evidence record.** Self-contained, but bytes everywhere and integrity drifts.
2. **Cross-reference the audit log payload by id + hash.** Evidence is a small record that points at the audit entry; verification walks the chain.
3. **Pretend the audit log is the evidence record.** Loses the cross-reference to controls, makes the auditor reconstruct it manually.

## Decision

Evidence records carry a cross-reference (option 2). The schema:

```python
class Evidence(BaseModel):
    id: str
    timestamp: datetime
    control_ids: list[str]
    type: Literal[...]
    payload: dict[str, Any]
    source_system: str
```

For `audit_log_reference`-typed evidence, the `payload` carries `{run_id, sequence, audit_hash}`. The hash chain in `agentic-harness` is the trust anchor.

## Trade-offs

- **The evidence record is not self-contained.** An auditor reading only the `Evidence` table cannot reconstruct the agent run. They need access to the audit table too. We accept this because the alternative — duplicating audit-log payloads into the evidence record — burns storage and adds an integrity-drift risk.
- **Verification is two-step.** Walk the audit chain, then verify each `Evidence` record points at a real audit hash. Sites that need a one-step verification can layer a periodic batch job that recomputes a Merkle root over both tables.

## Consequences

- The evidence record is small and predictable; storage and indexing are cheap.
- Cross-system evidence (MLflow runs, Langfuse traces, vendor attestations) uses the same shape — the `source_system` field is the discriminator and the `payload` shape is per-source.
- Backups and DR strategy must keep audit table and evidence table consistent; one without the other is incoherent.
