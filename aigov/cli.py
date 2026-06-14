"""aigov — CLI for compliance-as-code.

Three subcommands:

  aigov controls list                # list every control, grouped by framework
  aigov controls show <id>           # show one control + its mappings + evidence types
  aigov map <from> <to>              # cross-reference: e.g. 'eu_ai_act:Article 12' -> iso 42001
  aigov aibom emit <input.yaml>      # emit SPDX 3.0 AI Profile JSON from an AISystem YAML
  aigov init <name>                  # generate a starter-pack repo for an AI system

We intentionally keep the surface area small. The library is the product;
the CLI is the easiest way in.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
import yaml

from aigov.aibom import AISystem, emit_spdx3
from aigov.schema import Framework, load_controls

CONTROLS_DIR = Path(__file__).parent.parent / "controls"


@click.group()
@click.version_option()
def cli() -> None:
    """compliance-as-code: ISO 42001 + EU AI Act, codified."""


@cli.group()
def controls() -> None:
    """List and inspect controls."""


@controls.command("list")
@click.option(
    "--framework",
    type=click.Choice([f.value for f in Framework]),
    default=None,
    help="filter to one framework",
)
def controls_list(framework: str | None) -> None:
    """List every control."""
    corpus = load_controls(CONTROLS_DIR)
    rows = [c for c in corpus.values() if (framework is None or c.framework.value == framework)]
    rows.sort(key=lambda c: c.id)
    for control in rows:
        click.echo(f"{control.id:40} {control.enforcement.value:14} {control.name}")


@controls.command("show")
@click.argument("control_id")
def controls_show(control_id: str) -> None:
    """Show one control by id (e.g. iso42001:A.7.4)."""
    corpus = load_controls(CONTROLS_DIR)
    if control_id not in corpus:
        click.echo(f"unknown control id: {control_id}", err=True)
        sys.exit(1)
    click.echo(yaml.safe_dump(corpus[control_id].model_dump(mode="json"), sort_keys=False))


@cli.command("map")
@click.argument("source")
def map_cmd(source: str) -> None:
    """Cross-reference: print every control that maps to SOURCE.

    SOURCE is 'framework:reference', e.g. 'eu_ai_act:Article 12'.
    """
    try:
        framework_str, reference = source.split(":", 1)
        framework = Framework(framework_str)
    except (ValueError, KeyError):
        click.echo(f"source must be 'framework:reference', got {source!r}", err=True)
        sys.exit(1)
    corpus = load_controls(CONTROLS_DIR)
    hits = []
    for control in corpus.values():
        for mapping in control.mappings:
            if mapping.framework == framework and mapping.reference == reference:
                hits.append(control)
                break
    hits.sort(key=lambda c: c.id)
    if not hits:
        click.echo(f"no controls map to {source}")
        return
    click.echo(f"controls mapping to {source}:")
    for control in hits:
        click.echo(f"  {control.id}  {control.name}")


@cli.group()
def aibom() -> None:
    """Emit AI Bill of Materials documents."""


@aibom.command("emit")
@click.argument("input_path", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", type=click.Path(path_type=Path), default=None)
def aibom_emit(input_path: Path, output: Path | None) -> None:
    """Emit SPDX 3.0 AI Profile JSON from an AISystem YAML."""
    data = yaml.safe_load(input_path.read_text())
    system = AISystem.model_validate(data)
    doc = emit_spdx3(system)
    rendered = json.dumps(doc, indent=2, ensure_ascii=False)
    if output:
        output.write_text(rendered + "\n")
        click.echo(f"wrote {output}")
    else:
        click.echo(rendered)


@cli.command("init")
@click.argument("name")
@click.option(
    "--directory",
    "-d",
    type=click.Path(path_type=Path),
    default=None,
    help="destination directory (default: ./<name>)",
)
def init_cmd(name: str, directory: Path | None) -> None:
    """Generate a starter-pack repo for a new AI system."""
    target = directory or Path(name)
    target.mkdir(parents=True, exist_ok=False)
    (target / "system.yaml").write_text(_starter_system_yaml(name))
    (target / "evidence").mkdir(exist_ok=True)
    (target / "README.md").write_text(_starter_readme(name))
    click.echo(f"created starter pack in {target}/")
    click.echo("next steps:")
    click.echo(f"  1. edit {target}/system.yaml")
    click.echo(f"  2. aigov aibom emit {target}/system.yaml -o {target}/spdx.json")
    click.echo(f"  3. set up an evidence collector pointing at {target}/evidence/")


def _starter_system_yaml(name: str) -> str:
    return f"""name: {name}
version: 0.1.0
purpose: >
  One short paragraph describing what this system does and why it exists.
risk_classification: limited  # one of: minimal, limited, high, unacceptable (EU AI Act)
deployment_context: production
models:
  - name: example-model
    version: "1.0"
    base_model: ""
    license: ""
    parameters: 0
    training_method: ""
    datasets:
      - name: example-dataset
        version: ""
        license: ""
        source: ""
        classification: ""
    use_cases:
      - ""
    out_of_scope_use:
      - ""
    evaluation:
      - ""
"""


def _starter_readme(name: str) -> str:
    return f"""# {name} — AI system compliance pack

Generated by `aigov init {name}`.

## Files

- `system.yaml` — the AI system definition; edit me first.
- `evidence/` — drop attestation records, test runs, impact assessments here.
- `spdx.json` — generated AIBOM (run `aigov aibom emit system.yaml -o spdx.json`).

## Suggested next steps

1. Fill in `system.yaml`.
2. Map your runtime evidence into `evidence/` using the schemas in `aigov.schema.Evidence`.
3. Configure CI to run `aigov aibom emit` on every release and attach `spdx.json` as a release artefact.
"""


if __name__ == "__main__":
    cli()
