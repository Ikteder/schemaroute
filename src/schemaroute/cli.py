"""SchemaRoute command line interface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .core import PROFILE_METADATA, audit_schema, benchmark_corpus
from .render import render_audit_html, render_benchmark_svg


def _json_file(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON from {path}: {exc}") from exc


def _write(path: Path | None, content: str) -> None:
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="schemaroute")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("profiles", help="list dated provider profiles")
    audit = subparsers.add_parser("audit", help="audit one JSON Schema")
    audit.add_argument("schema", type=Path)
    audit.add_argument("--targets", help="comma-separated profile names")
    audit.add_argument("--features", type=Path, help="optional route-feature JSON")
    audit.add_argument("--json", type=Path, dest="json_output")
    audit.add_argument("--html", type=Path, dest="html_output")
    benchmark = subparsers.add_parser("benchmark", help="run an authored evaluation corpus")
    benchmark.add_argument("corpus", type=Path)
    benchmark.add_argument("--json", type=Path, dest="json_output")
    benchmark.add_argument("--svg", type=Path, dest="svg_output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "profiles":
            print(json.dumps(PROFILE_METADATA, indent=2, sort_keys=True))
            return 0
        if args.command == "audit":
            targets = args.targets.split(",") if args.targets else None
            if targets is not None and any(not target for target in targets):
                raise ValueError("targets cannot contain empty profile names")
            features = _json_file(args.features) if args.features else None
            result = audit_schema(_json_file(args.schema), targets, features)
            output = json.dumps(result, indent=2, sort_keys=True) + "\n"
            _write(args.json_output, output)
            _write(args.html_output, render_audit_html(result))
            print(f"{result['verdict']}: {result['finding_count']} finding(s)")
            return 0 if result["verdict"] == "portable" else 1
        result = benchmark_corpus(_json_file(args.corpus))
        output = json.dumps(result, indent=2, sort_keys=True) + "\n"
        _write(args.json_output, output)
        _write(args.svg_output, render_benchmark_svg(result))
        print(
            f"SchemaRoute {result['schemaroute_correct']}/{result['case_count']}; "
            f"baseline {result['baseline_correct']}/{result['case_count']}"
        )
        return 0 if result["schemaroute_correct"] == result["case_count"] else 1
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
