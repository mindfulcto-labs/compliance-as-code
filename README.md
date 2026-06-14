# compliance-as-code

[![CI](https://github.com/mindfulcto-labs/compliance-as-code/actions/workflows/ci.yml/badge.svg)](https://github.com/mindfulcto-labs/compliance-as-code/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

> ISO/IEC 42001 Annex A and EU AI Act Articles 12-15, codified. Runtime-enforced policies, evidence-generating logs, SPDX 3.0 AIBOMs. Plugs into [`agentic-harness`](https://github.com/mindfulcto-labs/agentic-harness) and any LLM gateway.

A small Python package + CLI that gives you four things:

1. **A YAML control library.** Every ISO/IEC 42001:2023 Annex A control, expressed as a structured YAML file with cross-references into EU AI Act Articles, NIST AI RMF, UK AI Cyber Code, and OWASP LLM Top 10. Look one up by id, list them by framework, walk the cross-map both directions.
2. **An evidence schema.** Pydantic-typed records that link runtime events (audit log entries, attestation records, model releases, policy decisions) back to the controls they satisfy. Drop your `agentic-harness` audit-log entries through it and you have machine-readable conformity evidence.
3. **An SPDX 3.0 AI Profile emitter.** Render an AI system definition (`system.yaml`) into a valid SPDX 3.0 AIBOM you can attach to a release. Models, datasets, training method, intended use, out-of-scope use, evaluation references — all in one file your auditor will recognise.
4. **A CLI scaffolder.** `aigov init my-system` lays out a starter pack so you can stop staring at the ISO 42001 PDF and start filling in fields.

## Why this exists

The AI governance tooling market in 2026 is dominated by SaaS. Credo AI, IBM watsonx.governance, Microsoft Purview AI Hub, Holistic AI, Modulos — pick your vendor, sign your contract, get a dashboard. That's fine if you have the budget and the buying cycle. It's not fine if you are a CTO who wants to be able to inspect, fork, and version-control your governance.

This repo is for the second case. It is opinionated about three things:

- **Controls are code, not slideware.** A control that only lives in a Word document is invisible to your CI and your audit log. A control that lives in a YAML file under version control changes the conversation with your auditor from "show me the policy" to "show me the policy and the runtime evidence it generated last quarter."
- **Evidence is hash-chained, not screenshots.** Your evidence corpus is only as trustworthy as the chain that links runtime to record. The schema deliberately points at the [`agentic-harness`](https://github.com/mindfulcto-labs/agentic-harness) audit log shape, which is SHA-256 hash-chained for tamper-evidence.
- **An AIBOM is a single file, not a portal.** SPDX 3.0 added the AI Profile in late 2024. We emit a minimal, valid SPDX 3.0 JSON-LD document so you can attach it to a GitHub Release and move on.

## Mapping table — the page reviewers linger on

| ISO/IEC 42001:2023 control | EU AI Act | NIST AI RMF | What it produces |
|---|---|---|---|
| A.6.2.7 — AI system event logs | Article 12 (record-keeping) | MEASURE 2.4 | Hash-chained audit log entries (`agentic-harness` audit table) |
| A.6.2.5 — Operation and monitoring | Article 15 (accuracy, robustness) | MEASURE 2.3, 2.7 | Eval run records (Langfuse / Ragas / DeepEval references) |
| A.7.4 — Data provenance | Article 10 (data governance) | MAP 4.1 | Dataset metadata in SPDX 3.0 AIBOM |
| A.7.6 — Data privacy | Article 10 + GDPR | GOVERN 1.6 | DPIA reference + DLP / PII redaction policy decision records |
| A.8.1 — System documentation and information for users | Article 13 (transparency) | GOVERN 1.4 | Model card + intended use + out-of-scope use in AIBOM |
| A.9.3 — Intended use | Article 13 + Article 9 (risk management) | MAP 1.1 | Intended use field in AIBOM + risk classification |
| A.5 — AI system impact assessment | Article 9 (risk management) + Article 27 (FRIA) | MAP 5.1 | Impact assessment record + risk classification |
| A.6.2.4 — AI system deployment | Article 14 (human oversight) | GOVERN 3.2 | Two-person approval records from `agentic-harness` blast-radius gate |

Full library lives under [`controls/iso42001/`](controls/iso42001/) and [`mappings/eu-ai-act/`](mappings/eu-ai-act/). One YAML file per control. `aigov controls list` prints the lot.

## Quickstart

```bash
pip install aigov
```

```bash
# Browse the corpus
aigov controls list
aigov controls show iso42001:A.6.2.7
aigov map eu_ai_act:Article 12   # → every control that satisfies AI Act Article 12

# Scaffold a new AI system
aigov init triage-bot
cd triage-bot
$EDITOR system.yaml

# Emit a SPDX 3.0 AIBOM for the release
aigov aibom emit system.yaml -o spdx.json
```

```python
from aigov import Evidence, load_controls

# Load the corpus once at startup.
controls = load_controls("controls")

# Emit evidence as your agent runs. Cross-reference the controls
# whose objective this event helps satisfy.
ev = Evidence.now(
    id="audit-2026-06-14-000123",
    control_ids=["iso42001:A.6.2.7"],
    type="audit_log_reference",
    payload={"run_id": "demo-001", "audit_hash": "9f1a..."},
    source_system="agentic-harness",
)
# ev goes to your durable evidence store; the audit-log payload itself
# stays in the harness's hash-chained table.
```

## Integration recipes

### With `agentic-harness`

The [`agentic-harness`](https://github.com/mindfulcto-labs/agentic-harness) hash-chained audit log is the natural evidence source for `iso42001:A.6.2.7` (event logs) and EU AI Act Article 12. Wire it up like this:

```python
from harness import AuditLogger, InMemoryAuditWriter
from aigov import Evidence

writer = InMemoryAuditWriter()  # or PostgresAuditWriter in production
log = AuditLogger(run_id="run-001", writer=writer)

# Normal agent work; the harness emits events into the audit log.
event = log.emit("tool.invoke", {"tool": "erp.read_supplier"})

# At evidence-collection time (CI job, nightly batch, on-demand):
ev = Evidence.now(
    id=f"evidence-{event.hash[:12]}",
    control_ids=["iso42001:A.6.2.7", "iso42001:A.6.2.5"],
    type="audit_log_reference",
    payload={"audit_hash": event.hash, "run_id": event.run_id, "sequence": event.sequence},
    source_system="agentic-harness",
)
```

### With LangGraph / LangChain

The pattern is the same: emit `Evidence` records at the points where your application takes a decision a regulator will want to inspect. The granularity is yours — typical sites emit one record per checkpointable state transition, plus one per release.

### With your CI/CD

Run `aigov aibom emit` on every release and attach the result as a release artefact. The SPDX 3.0 file is small, stable, and unambiguous.

## What this proves

Sites this is written for: UK and EU teams who need to demonstrate ISO 42001 readiness or EU AI Act conformity without buying a SaaS dashboard. The CLI + YAML library + AIBOM emitter is enough to ship.

For my CV, this repo backs:

- **"AI Governance, Responsible AI, AI Ethics swimlane"** — the YAML control corpus and the cross-map are the artefact.
- **"ISO/IEC 42001 (AI Management Systems) Lead Auditor (in progress)"** — the controls and the evidence schema are the lens I'm reading 42001 through.
- **"ISACA CGEIT, CRISC, CISM (exams passed July 2025)"** — the governance/risk/security control vocabulary used in the schema.

## Limitations

- **v0.1 ships the schema, the AIBOM emitter, and the CLI. The 38-control YAML library lands incrementally** as I source the language from the standard. Pull requests welcome; please cite the clause.
- **No legal advice.** This is a code library, not counsel. Use a real auditor for real audits.
- **SPDX 3.0 AI Profile is still settling.** We emit a deliberate subset; the spec may add fields we don't yet emit. Sites who need more should extend the emitter and contribute back.
- **No OPA Rego policies in v0.1.** The reference policies live in [`agentic-harness`](https://github.com/mindfulcto-labs/agentic-harness). v0.2 will ship a small Rego library that maps controls to policy decisions.

## Roadmap

- **v0.2** — 38 ISO 42001 Annex A controls authored from primary sources. CycloneDX ML-BOM emitter alongside SPDX 3.0. OPA Rego policy library plug-in.
- **v0.3** — NIST AI RMF cross-map. OWASP Agentic Top 10 cross-map. ISO 23894 (AI risk management) bridge.
- **v0.4** — GitHub Actions templates that auto-collect evidence from MLflow and Langfuse on every CI run.

## IP statement

This is a public reference implementation of patterns inspired by production AI governance practice. It does not reference, replicate, or derive from any employer's internal architecture, source code, or proprietary designs. All data is synthetic or drawn from public sources. The control language draws on publicly available standards (ISO/IEC 42001:2023, EU AI Act Regulation (EU) 2024/1689).

## Companion reading

Long-form essays at [themindfulcto.com](https://themindfulcto.com):

- _What ISO 42001 Annex A actually asks for, and how to wire it into your repo._
- _EU AI Act Article 12 in practice: what regulators will look at, and what they will not._
- _The AIBOM. Why SPDX 3.0 won the format war and what that means for your release pipeline._

## License

[Apache License 2.0](LICENSE).
