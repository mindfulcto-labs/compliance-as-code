# Templates

Starter pack generators land here. v0.1 ships the basic `aigov init <name>` scaffolder inline in `aigov/cli.py`. v0.2 will move that scaffolder to a templates pack so sites can pick the shape that matches their AI system (regulated/internal/customer-facing) rather than getting a one-size-fits-all output.

Planned templates:
- `regulated/` — high-risk AI Act profile, full evidence emitter list, two-person approval defaults
- `internal/` — minimal evidence, limited-risk AI Act profile
- `customer-facing/` — transparency-obligation defaults, model-card scaffolding
