from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path

from schemaroute.cli import main
from schemaroute.core import ANTHROPIC, GEMINI, OPENAI, audit_schema, benchmark_corpus
from schemaroute.render import render_audit_html, render_benchmark_svg

ROOT = Path(__file__).resolve().parents[1]


class AuditTests(unittest.TestCase):
    def test_portable_example(self) -> None:
        schema = json.loads((ROOT / "examples/portable.schema.json").read_text(encoding="utf-8"))
        result = audit_schema(schema)
        self.assertEqual("portable", result["verdict"])
        self.assertEqual(0, result["finding_count"])
        self.assertEqual(64, len(result["schema_sha256"]))

    def test_openai_required_and_closed_object(self) -> None:
        schema = {"type": "object", "properties": {"x": {"type": "string"}}}
        result = audit_schema(schema, [OPENAI])
        self.assertEqual("blocked", result["verdict"])
        self.assertEqual(
            {"OPENAI_ALL_FIELDS_REQUIRED", "OPENAI_CLOSED_OBJECT_REQUIRED"},
            {item["code"] for item in result["findings"]},
        )

    def test_anthropic_feature_conflicts(self) -> None:
        schema = {
            "type": "object",
            "properties": {"x": {"type": "string"}},
            "required": ["x"],
            "additionalProperties": False,
        }
        result = audit_schema(schema, [ANTHROPIC], {"citations": True, "message_prefill": True})
        self.assertEqual(
            {"ANTHROPIC_CITATIONS_CONFLICT", "ANTHROPIC_PREFILL_CONFLICT"},
            {item["code"] for item in result["findings"]},
        )

    def test_gemini_ignored_constraint_is_not_portable(self) -> None:
        schema = {
            "type": "object",
            "properties": {"x": {"type": "string", "maxLength": 4}},
            "required": ["x"],
        }
        result = audit_schema(schema, [GEMINI])
        self.assertEqual("requires_runtime_validation", result["verdict"])
        self.assertEqual("#/properties/x/maxLength", result["findings"][0]["pointer"])

    def test_json_pointer_escaping_and_html_escaping(self) -> None:
        schema = {
            "type": "object",
            "properties": {"x/y~<script>": {"type": "string", "maxLength": 3}},
            "required": ["x/y~<script>"],
        }
        result = audit_schema(schema, [GEMINI])
        pointer = result["findings"][0]["pointer"]
        self.assertIn("x~1y~0<script>", pointer)
        report = render_audit_html(result)
        self.assertNotIn("<script>/maxLength", report)
        self.assertIn("&lt;script&gt;", report)
        match = re.search(r'<script type="application/json" id="receipt">(.*?)</script>', report)
        self.assertIsNotNone(match)
        embedded = json.loads(match.group(1))  # type: ignore[union-attr]
        self.assertEqual(result["schema_sha256"], embedded["schema_sha256"])

    def test_bad_profile_and_bad_schema_are_controlled(self) -> None:
        with self.assertRaises(ValueError):
            audit_schema([], [OPENAI])  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            audit_schema({"type": "object"}, ["made-up"])

    def test_digest_is_key_order_independent(self) -> None:
        left = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}
        right = {"required": [], "properties": {}, "additionalProperties": False, "type": "object"}
        self.assertEqual(
            audit_schema(left, [OPENAI])["schema_sha256"],
            audit_schema(right, [OPENAI])["schema_sha256"],
        )


class BenchmarkTests(unittest.TestCase):
    def test_full_authored_corpus(self) -> None:
        corpus = json.loads(
            (ROOT / "benchmarks/provider-portability-v1.json").read_text(encoding="utf-8")
        )
        result = benchmark_corpus(corpus)
        self.assertEqual(15, result["case_count"])
        self.assertEqual(15, result["schemaroute_correct"])
        self.assertEqual(1, result["baseline_correct"])

    def test_duplicate_case_id_rejected(self) -> None:
        case = {
            "id": "same",
            "targets": [GEMINI],
            "schema": {"type": "object", "properties": {}, "required": []},
            "expected_verdict": "portable",
            "expected_codes": [],
        }
        with self.assertRaises(ValueError):
            benchmark_corpus({"schema_version": 1, "cases": [case, case]})

    def test_svg_contains_evidence(self) -> None:
        result = {
            "case_count": 10,
            "schemaroute_correct": 9,
            "baseline_correct": 2,
        }
        svg = render_benchmark_svg(result)
        self.assertIn("9/10", svg)
        self.assertIn("2/10", svg)


class CliTests(unittest.TestCase):
    def test_cli_exit_contract_and_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            portable = ROOT / "examples/portable.schema.json"
            risky = ROOT / "examples/risky.schema.json"
            self.assertEqual(0, main(["audit", str(portable), "--json", str(root / "ok.json")]))
            self.assertEqual(1, main(["audit", str(risky)]))
            self.assertEqual(2, main(["audit", str(root / "missing.json")]))
            self.assertTrue((root / "ok.json").is_file())

    def test_benchmark_cli(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(
                0,
                main(
                    [
                        "benchmark",
                        str(ROOT / "benchmarks/provider-portability-v1.json"),
                        "--json",
                        str(root / "evidence.json"),
                        "--svg",
                        str(root / "evidence.svg"),
                    ]
                ),
            )
            self.assertTrue((root / "evidence.svg").read_text(encoding="utf-8").startswith("<svg"))


if __name__ == "__main__":
    unittest.main()
