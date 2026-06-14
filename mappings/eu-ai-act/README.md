# EU AI Act mappings

This directory will hold the EU AI Act Article-to-implementation map. v0.1 keeps Article references inline on each ISO 42001 control (see `controls/iso42001/`). The standalone Article-centred view ships in v0.2.

## Shape

The eventual layout is one YAML file per Article that ships runtime obligations the library can act on:

- `article-09.yaml` — Risk management system
- `article-10.yaml` — Data and data governance
- `article-12.yaml` — Record-keeping
- `article-13.yaml` — Transparency and provision of information to deployers
- `article-14.yaml` — Human oversight
- `article-15.yaml` — Accuracy, robustness, cybersecurity

Each file lists the obligations the Article creates, the evidence types that satisfy them, and the ISO 42001 controls that reference back.

## Status

- v0.1 (shipped): inline Article references on ISO 42001 controls (see schema).
- v0.2 (planned): Articles 9-15 authored as standalone files.
- v0.3 (planned): post-market-monitoring Articles, deployer-facing obligations.

## Disclaimer

Not legal advice. Refer to the consolidated text of [Regulation (EU) 2024/1689](https://eur-lex.europa.eu/eli/reg/2024/1689/oj) for the operative text. We track the consolidated version and note our snapshot date in each file's frontmatter.
