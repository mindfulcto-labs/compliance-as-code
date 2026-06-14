# ISO/IEC 42001:2023 Annex A controls

This directory will hold one YAML file per control in ISO/IEC 42001 Annex A. v0.1 ships the schema (`aigov/schema.py`), the AIBOM emitter, and the CLI. The 38-control corpus lands in v0.2 once the source language has been authored against the standard rather than against public summaries.

## Shape

Each control is a single YAML file:

```yaml
id: iso42001:A.6.2.7
framework: iso_42001
name: AI system event logs
objective: >
  Maintain event logs over the AI system lifecycle so operation, incident
  investigation, and conformity assessment can be carried out.
enforcement: evidence_only
mappings:
  - framework: eu_ai_act
    reference: "Article 12"
    note: "Record-keeping for high-risk AI systems."
  - framework: nist_ai_rmf
    reference: "MEASURE 2.4"
evidence_required:
  - audit_log_reference
owner: "AI Operations Lead"
```

Load the corpus with `load_controls("controls")` or list them with `aigov controls list`.

## Status

- v0.1 (shipped): schema + CLI + AIBOM emitter, no controls authored yet.
- v0.2 (planned): 38 ISO 42001 Annex A controls written from the standard.
- v0.3 (planned): NIST AI RMF, OWASP Agentic Top 10 cross-maps.

## Contributing controls

PRs welcome. Cite the clause and quote the operative sentence in the PR body. We will not merge controls whose objective was paraphrased without checking against the standard.
