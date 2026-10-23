"""Provider-profile JSON Schema auditing and deterministic benchmark support."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from typing import Any

OPENAI = "openai-strict-2026-10-22"
ANTHROPIC = "anthropic-json-2026-10-22"
GEMINI = "gemini-json-2026-10-22"

PROFILE_METADATA: dict[str, dict[str, str]] = {
    OPENAI: {
        "provider": "OpenAI",
        "mode": "strict JSON Schema output",
        "accessed": "2026-10-22",
        "source": "https://developers.openai.com/api/docs/guides/structured-outputs",
    },
    ANTHROPIC: {
        "provider": "Anthropic",
        "mode": "output_config.format json_schema",
        "accessed": "2026-10-22",
        "source": "https://platform.claude.com/docs/en/build-with-claude/structured-outputs",
    },
    GEMINI: {
        "provider": "Google Gemini",
        "mode": "application/json response schema",
        "accessed": "2026-10-22",
        "source": "https://ai.google.dev/gemini-api/docs/structured-output",
    },
}

SCHEMA_CHILD_MAPS = ("properties", "$defs", "definitions", "dependentSchemas")
SCHEMA_CHILD_LISTS = ("anyOf", "oneOf", "allOf", "prefixItems")
SCHEMA_CHILD_SINGLE = (
    "items",
    "not",
    "if",
    "then",
    "else",
    "contains",
    "propertyNames",
)


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    profile: str
    pointer: str
    message: str


def _pointer_token(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _child_pointer(pointer: str, *tokens: str | int) -> str:
    suffix = "/".join(_pointer_token(str(token)) for token in tokens)
    return f"{pointer}/{suffix}" if pointer != "#" else f"#/{suffix}"


def _canonical_digest(schema: dict[str, Any]) -> str:
    raw = json.dumps(schema, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _walk(schema: dict[str, Any], pointer: str = "#") -> Iterable[tuple[str, dict[str, Any]]]:
    yield pointer, schema
    for key in SCHEMA_CHILD_MAPS:
        value = schema.get(key)
        if isinstance(value, dict):
            for name, child in value.items():
                if isinstance(child, dict):
                    yield from _walk(child, _child_pointer(pointer, key, name))
    for key in SCHEMA_CHILD_LISTS:
        value = schema.get(key)
        if isinstance(value, list):
            for index, child in enumerate(value):
                if isinstance(child, dict):
                    yield from _walk(child, _child_pointer(pointer, key, index))
    for key in SCHEMA_CHILD_SINGLE:
        value = schema.get(key)
        if isinstance(value, dict):
            yield from _walk(value, _child_pointer(pointer, key))
        elif key == "items" and isinstance(value, list):
            for index, child in enumerate(value):
                if isinstance(child, dict):
                    yield from _walk(child, _child_pointer(pointer, key, index))
    additional = schema.get("additionalProperties")
    if isinstance(additional, dict):
        yield from _walk(additional, _child_pointer(pointer, "additionalProperties"))


def _schema_depth(schema: dict[str, Any]) -> int:
    def children(node: dict[str, Any]) -> Iterable[dict[str, Any]]:
        for key in SCHEMA_CHILD_MAPS:
            value = node.get(key)
            if isinstance(value, dict):
                yield from (child for child in value.values() if isinstance(child, dict))
        for key in SCHEMA_CHILD_LISTS:
            value = node.get(key)
            if isinstance(value, list):
                yield from (child for child in value if isinstance(child, dict))
        for key in SCHEMA_CHILD_SINGLE:
            value = node.get(key)
            if isinstance(value, dict):
                yield value
            elif key == "items" and isinstance(value, list):
                yield from (child for child in value if isinstance(child, dict))
        additional = node.get("additionalProperties")
        if isinstance(additional, dict):
            yield additional

    def descend(node: dict[str, Any], current: int) -> int:
        is_object = node.get("type") == "object" or isinstance(node.get("properties"), dict)
        here = current + (1 if is_object else 0)
        return max([here, *(descend(child, here) for child in children(node))])

    return descend(schema, 0)


def _metrics(schema: dict[str, Any]) -> dict[str, int]:
    property_count = 0
    optional_count = 0
    union_count = 0
    enum_count = 0
    string_budget = 0
    max_enum_strings = 0
    for _, node in _walk(schema):
        properties = node.get("properties")
        if isinstance(properties, dict):
            property_count += len(properties)
            required = node.get("required")
            required_set = set(required) if isinstance(required, list) else set()
            optional_count += len(set(properties) - required_set)
            string_budget += sum(len(str(name)) for name in properties)
        for defs_key in ("$defs", "definitions"):
            defs = node.get(defs_key)
            if isinstance(defs, dict):
                string_budget += sum(len(str(name)) for name in defs)
        if isinstance(node.get("anyOf"), list) or isinstance(node.get("type"), list):
            union_count += 1
        enum = node.get("enum")
        if isinstance(enum, list):
            enum_count += len(enum)
            enum_strings = sum(len(item) for item in enum if isinstance(item, str))
            string_budget += enum_strings
            max_enum_strings = max(max_enum_strings, enum_strings)
        const = node.get("const")
        if isinstance(const, str):
            string_budget += len(const)
    return {
        "object_properties": property_count,
        "object_nesting_depth": _schema_depth(schema),
        "optional_parameters": optional_count,
        "union_parameters": union_count,
        "enum_values": enum_count,
        "string_budget": string_budget,
        "largest_enum_string_budget": max_enum_strings,
    }


def _validate_structure(schema: Any) -> dict[str, Any]:
    if not isinstance(schema, dict):
        raise ValueError("schema root must be a JSON object")
    valid_types = {"object", "array", "string", "integer", "number", "boolean", "null"}
    for pointer, node in _walk(schema):
        schema_type = node.get("type")
        if isinstance(schema_type, str) and schema_type not in valid_types:
            raise ValueError(f"{pointer}/type has unsupported type name {schema_type!r}")
        if isinstance(schema_type, list):
            if not schema_type or any(item not in valid_types for item in schema_type):
                raise ValueError(f"{pointer}/type must contain known type names")
        elif schema_type is not None and not isinstance(schema_type, str):
            raise ValueError(f"{pointer}/type must be a string or list")
        properties = node.get("properties")
        if properties is not None and not isinstance(properties, dict):
            raise ValueError(f"{pointer}/properties must be an object")
        required = node.get("required")
        if required is not None and (
            not isinstance(required, list) or any(not isinstance(item, str) for item in required)
        ):
            raise ValueError(f"{pointer}/required must be a list of strings")
    return schema


def _contains_key(value: Any, key: str) -> bool:
    if isinstance(value, dict):
        return key in value or any(_contains_key(item, key) for item in value.values())
    if isinstance(value, list):
        return any(_contains_key(item, key) for item in value)
    return False


def _is_recursive_ref(pointer: str, ref: str) -> bool:
    if ref == "#":
        return True
    if not ref.startswith("#/"):
        return False
    target = ref
    return pointer == target or pointer.startswith(f"{target}/")


def _finding(code: str, severity: str, profile: str, pointer: str, message: str) -> Finding:
    return Finding(code, severity, profile, pointer, message)


def _audit_openai(schema: dict[str, Any], metrics: dict[str, int]) -> list[Finding]:
    findings: list[Finding] = []
    if schema.get("type") != "object" or "anyOf" in schema:
        findings.append(
            _finding(
                "OPENAI_ROOT_OBJECT_REQUIRED",
                "error",
                OPENAI,
                "#",
                "The root must be an object and cannot be anyOf.",
            )
        )
    unsupported = {"allOf", "not", "dependentRequired", "dependentSchemas", "if", "then", "else"}
    for pointer, node in _walk(schema):
        properties = node.get("properties")
        is_object = node.get("type") == "object" or isinstance(properties, dict)
        if is_object:
            if node.get("additionalProperties") is not False:
                findings.append(
                    _finding(
                        "OPENAI_CLOSED_OBJECT_REQUIRED",
                        "error",
                        OPENAI,
                        pointer,
                        "Every object must set additionalProperties to false.",
                    )
                )
            if isinstance(properties, dict):
                required = set(node.get("required", []))
                missing = sorted(set(properties) - required)
                if missing:
                    findings.append(
                        _finding(
                            "OPENAI_ALL_FIELDS_REQUIRED",
                            "error",
                            OPENAI,
                            pointer,
                            f"All object fields must be required; {len(missing)} are optional.",
                        )
                    )
        for key in sorted(unsupported.intersection(node)):
            findings.append(
                _finding(
                    "OPENAI_UNSUPPORTED_KEYWORD",
                    "error",
                    OPENAI,
                    _child_pointer(pointer, key),
                    f"{key} is outside the documented strict-output subset.",
                )
            )
        ref = node.get("$ref")
        if isinstance(ref, str) and not ref.startswith("#"):
            findings.append(
                _finding(
                    "OPENAI_EXTERNAL_REF_UNVERIFIED",
                    "warning",
                    OPENAI,
                    _child_pointer(pointer, "$ref"),
                    "The profile does not claim portable external-reference support.",
                )
            )
    limits = (
        ("object_properties", 5000, "OPENAI_PROPERTY_LIMIT"),
        ("object_nesting_depth", 10, "OPENAI_NESTING_LIMIT"),
        ("string_budget", 120000, "OPENAI_STRING_LIMIT"),
        ("enum_values", 1000, "OPENAI_ENUM_LIMIT"),
    )
    for name, maximum, code in limits:
        if metrics[name] > maximum:
            findings.append(
                _finding(
                    code,
                    "error",
                    OPENAI,
                    "#",
                    f"{name} is {metrics[name]}, above the documented limit of {maximum}.",
                )
            )
    if metrics["enum_values"] > 250 and metrics["largest_enum_string_budget"] > 15000:
        findings.append(
            _finding(
                "OPENAI_LARGE_ENUM_STRING_LIMIT",
                "error",
                OPENAI,
                "#",
                "A large enum exceeds the documented 15,000-character string budget.",
            )
        )
    return findings


def _audit_anthropic(
    schema: dict[str, Any], metrics: dict[str, int], features: dict[str, Any]
) -> list[Finding]:
    findings: list[Finding] = []
    unsupported = {
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "multipleOf",
        "minLength",
        "maxLength",
        "maxItems",
        "minProperties",
        "maxProperties",
    }
    for pointer, node in _walk(schema):
        properties = node.get("properties")
        is_object = node.get("type") == "object" or isinstance(properties, dict)
        if is_object and node.get("additionalProperties") is not False:
            findings.append(
                _finding(
                    "ANTHROPIC_CLOSED_OBJECT_REQUIRED",
                    "error",
                    ANTHROPIC,
                    pointer,
                    "Every object must set additionalProperties to false.",
                )
            )
        additional = node.get("additionalProperties")
        if additional not in (None, False):
            findings.append(
                _finding(
                    "ANTHROPIC_ADDITIONAL_PROPERTIES_UNSUPPORTED",
                    "error",
                    ANTHROPIC,
                    _child_pointer(pointer, "additionalProperties"),
                    "additionalProperties supports only false in this profile.",
                )
            )
        for key in sorted(unsupported.intersection(node)):
            findings.append(
                _finding(
                    "ANTHROPIC_UNSUPPORTED_CONSTRAINT",
                    "error",
                    ANTHROPIC,
                    _child_pointer(pointer, key),
                    f"{key} is not enforced by the raw provider schema profile.",
                )
            )
        min_items = node.get("minItems")
        if min_items not in (None, 0, 1):
            findings.append(
                _finding(
                    "ANTHROPIC_MIN_ITEMS_LIMIT",
                    "error",
                    ANTHROPIC,
                    _child_pointer(pointer, "minItems"),
                    "Only minItems values 0 and 1 are supported.",
                )
            )
        if "allOf" in node and _contains_key(node["allOf"], "$ref"):
            findings.append(
                _finding(
                    "ANTHROPIC_ALLOF_REF_UNSUPPORTED",
                    "error",
                    ANTHROPIC,
                    _child_pointer(pointer, "allOf"),
                    "allOf combined with $ref is not supported.",
                )
            )
        ref = node.get("$ref")
        if isinstance(ref, str):
            if not ref.startswith("#"):
                findings.append(
                    _finding(
                        "ANTHROPIC_EXTERNAL_REF_UNSUPPORTED",
                        "error",
                        ANTHROPIC,
                        _child_pointer(pointer, "$ref"),
                        "External references are not supported.",
                    )
                )
            elif _is_recursive_ref(pointer, ref):
                findings.append(
                    _finding(
                        "ANTHROPIC_RECURSION_UNSUPPORTED",
                        "error",
                        ANTHROPIC,
                        _child_pointer(pointer, "$ref"),
                        "Recursive schemas are not supported.",
                    )
                )
    if metrics["optional_parameters"] > 24:
        findings.append(
            _finding(
                "ANTHROPIC_OPTIONAL_PARAMETER_LIMIT",
                "error",
                ANTHROPIC,
                "#",
                "The route exceeds the documented 24 optional-parameter limit.",
            )
        )
    if metrics["union_parameters"] > 16:
        findings.append(
            _finding(
                "ANTHROPIC_UNION_PARAMETER_LIMIT",
                "error",
                ANTHROPIC,
                "#",
                "The route exceeds the documented 16 union-parameter limit.",
            )
        )
    if features.get("citations") is True:
        findings.append(
            _finding(
                "ANTHROPIC_CITATIONS_CONFLICT",
                "error",
                ANTHROPIC,
                "#/features/citations",
                "Citations are incompatible with JSON outputs.",
            )
        )
    if features.get("message_prefill") is True:
        findings.append(
            _finding(
                "ANTHROPIC_PREFILL_CONFLICT",
                "error",
                ANTHROPIC,
                "#/features/message_prefill",
                "Message prefilling is incompatible with JSON outputs.",
            )
        )
    return findings


GEMINI_KNOWN_KEYWORDS = {
    "$defs",
    "$ref",
    "additionalProperties",
    "anyOf",
    "const",
    "default",
    "definitions",
    "description",
    "enum",
    "format",
    "items",
    "maxItems",
    "maxLength",
    "maxProperties",
    "maximum",
    "minItems",
    "minLength",
    "minProperties",
    "minimum",
    "prefixItems",
    "properties",
    "required",
    "title",
    "type",
}


def _audit_gemini(schema: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    root_type = schema.get("type")
    items = schema.get("items")
    array_of_objects = (
        root_type == "array" and isinstance(items, dict) and items.get("type") == "object"
    )
    if root_type != "object" and not array_of_objects:
        findings.append(
            _finding(
                "GEMINI_ROOT_SHAPE_REQUIRED",
                "error",
                GEMINI,
                "#",
                "The documented response root is an object or an array containing objects.",
            )
        )
    ignored = {"minLength", "maxLength", "minProperties", "maxProperties"}
    for pointer, node in _walk(schema):
        for key in sorted(ignored.intersection(node)):
            findings.append(
                _finding(
                    "GEMINI_CONSTRAINT_IGNORED",
                    "warning",
                    GEMINI,
                    _child_pointer(pointer, key),
                    f"{key} is stripped and must be validated by the application.",
                )
            )
        for key in sorted(set(node) - GEMINI_KNOWN_KEYWORDS):
            findings.append(
                _finding(
                    "GEMINI_KEYWORD_UNVERIFIED",
                    "warning",
                    GEMINI,
                    _child_pointer(pointer, key),
                    f"{key} is outside this profile's documented portable subset.",
                )
            )
    return findings


def audit_schema(
    schema: dict[str, Any], targets: list[str] | None = None, features: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Audit a schema against dated provider profiles."""
    schema = _validate_structure(schema)
    targets = targets or list(PROFILE_METADATA)
    features = features or {}
    unknown = [target for target in targets if target not in PROFILE_METADATA]
    if unknown:
        raise ValueError(f"unknown profiles: {', '.join(unknown)}")
    if not isinstance(features, dict):
        raise ValueError("features must be a JSON object")
    metrics = _metrics(schema)
    findings: list[Finding] = []
    for target in targets:
        if target == OPENAI:
            findings.extend(_audit_openai(schema, metrics))
        elif target == ANTHROPIC:
            findings.extend(_audit_anthropic(schema, metrics, features))
        elif target == GEMINI:
            findings.extend(_audit_gemini(schema))
    findings.sort(
        key=lambda item: (targets.index(item.profile), item.pointer, item.code, item.message)
    )
    if any(item.severity == "error" for item in findings):
        verdict = "blocked"
    elif findings:
        verdict = "requires_runtime_validation"
    else:
        verdict = "portable"
    return {
        "schema_version": 1,
        "tool": "schemaroute",
        "tool_version": "0.1.0",
        "verdict": verdict,
        "schema_sha256": _canonical_digest(schema),
        "targets": targets,
        "profiles": {target: PROFILE_METADATA[target] for target in targets},
        "metrics": metrics,
        "finding_count": len(findings),
        "findings": [asdict(item) for item in findings],
        "interpretation": (
            "Passing finds no documented static conflict in these dated profiles; it does not prove "
            "live provider acceptance, output meaning, or future compatibility."
        ),
    }


def _generated_schema(generator: dict[str, Any]) -> dict[str, Any]:
    kind = generator.get("kind")
    count = generator.get("count")
    if not isinstance(count, int) or count < 1 or count > 6000:
        raise ValueError("generator count must be an integer from 1 through 6000")
    if kind == "properties":
        properties = {f"field_{index:04d}": {"type": "string"} for index in range(count)}
        return {
            "type": "object",
            "properties": properties,
            "required": list(properties),
            "additionalProperties": False,
        }
    if kind == "nested_objects":
        node: dict[str, Any] = {
            "type": "object",
            "properties": {"value": {"type": "string"}},
            "required": ["value"],
            "additionalProperties": False,
        }
        for index in range(count - 1):
            name = f"level_{count - index:02d}"
            node = {
                "type": "object",
                "properties": {name: node},
                "required": [name],
                "additionalProperties": False,
            }
        return node
    if kind == "optional_properties":
        return {
            "type": "object",
            "properties": {f"field_{index:02d}": {"type": "string"} for index in range(count)},
            "required": [],
            "additionalProperties": False,
        }
    if kind == "union_properties":
        properties = {
            f"field_{index:02d}": {"anyOf": [{"type": "string"}, {"type": "null"}]}
            for index in range(count)
        }
        return {
            "type": "object",
            "properties": properties,
            "required": list(properties),
            "additionalProperties": False,
        }
    raise ValueError(f"unknown generator kind: {kind!r}")


def benchmark_corpus(corpus: dict[str, Any]) -> dict[str, Any]:
    """Evaluate SchemaRoute and a JSON-parse-only baseline on an authored corpus."""
    if corpus.get("schema_version") != 1 or not isinstance(corpus.get("cases"), list):
        raise ValueError("corpus must contain schema_version 1 and a cases list")
    rows: list[dict[str, Any]] = []
    tool_correct = 0
    baseline_correct = 0
    seen: set[str] = set()
    for case in corpus["cases"]:
        if not isinstance(case, dict) or not isinstance(case.get("id"), str):
            raise ValueError("each case must be an object with a string id")
        case_id = case["id"]
        if case_id in seen:
            raise ValueError(f"duplicate case id: {case_id}")
        seen.add(case_id)
        schema = case.get("schema")
        if schema is None and isinstance(case.get("generator"), dict):
            schema = _generated_schema(case["generator"])
        result = audit_schema(schema, case.get("targets"), case.get("features"))
        expected_verdict = case.get("expected_verdict")
        expected_codes = sorted(case.get("expected_codes", []))
        actual_codes = sorted({finding["code"] for finding in result["findings"]})
        tool_match = result["verdict"] == expected_verdict and actual_codes == expected_codes
        baseline_verdict = "portable"
        baseline_match = baseline_verdict == expected_verdict
        tool_correct += int(tool_match)
        baseline_correct += int(baseline_match)
        rows.append(
            {
                "id": case_id,
                "expected_verdict": expected_verdict,
                "actual_verdict": result["verdict"],
                "expected_codes": expected_codes,
                "actual_codes": actual_codes,
                "schemaroute_correct": tool_match,
                "baseline_verdict": baseline_verdict,
                "baseline_correct": baseline_match,
            }
        )
    total = len(rows)
    return {
        "schema_version": 1,
        "tool": "schemaroute",
        "tool_version": "0.1.0",
        "case_count": total,
        "schemaroute_correct": tool_correct,
        "baseline_correct": baseline_correct,
        "schemaroute_accuracy": tool_correct / total if total else 0.0,
        "baseline_accuracy": baseline_correct / total if total else 0.0,
        "baseline": "JSON parse plus object-root check; every structurally valid schema is portable",
        "cases": rows,
    }
