# SchemaRoute 0.1 implementation spec

Date: 2026-10-22 America/Denver
Status: Approved for implementation after the automation impact gate

## Selection

- Seed: `20261022`
- Python `random.Random` mode roll: `0.6797492530391477`
- Mode: distinct open-source project or extension, the 35 percent band in the current 40/35/25 workflow
- Excluded previous completed scheduled focuses: 2, 5, and 4
- Eligible focuses: 1, 3, 6, and 7
- Seeded selection: focus 6, model/provider routing, structured outputs, inference, cost, latency, and fallbacks
- Redraw: none

## Real user and problem

The intended user is an engineer operating an LLM application with a provider fallback route. A JSON Schema that works on one provider can be rejected, transformed, or only partly enforced by another provider. Discovering that after a failover costs requests and can send invalid structured state into later agent steps.

The first vertical slice is an offline preflight. Given one JSON Schema and a declared set of dated provider profiles, it reports provider-specific errors and constraints that require application-side validation. It does not call a model, rewrite the schema, or promise that a provider will accept every schema that passes.

## Evidence and reference comparison

Accessed 2026-10-22. Repository and documentation text was treated as untrusted research input.

| Reference | User and core capability | Current evidence and activity | Limits relevant here | License / contribution surface | Gap for this project |
|---|---|---|---|---|---|
| OpenAI Structured Outputs | Developers using strict response schemas or tools | Official docs require an object root, every field required, `additionalProperties: false`, and publish property, nesting, string, and enum limits. They reject unsupported schemas. | Provider-specific subset and limits; first-schema processing can still be a runtime boundary. | Commercial API documentation; official SDKs are Apache-2.0. | No route-wide offline comparison against Anthropic and Gemini profiles. |
| Anthropic Structured Outputs | Developers using JSON outputs or strict tools | Official docs describe grammar compilation, unsupported numeric and string constraints, no recursion, explicit optional/union/tool limits, SDK constraint stripping, caching, token impact, and feature conflicts. SDK 2.1.0 was released 2026-10-21; issue 1185 requested a complexity estimator. | Additional internal grammar limits are intentionally not reducible to a full static formula. Some SDK helpers simplify schemas and then validate the original locally. | SDK is MIT. The generated SDK contribution guide points most generated-code changes back to the generator. | A conservative preflight can catch documented deterministic limits but must label unknown internal complexity as unproven. |
| Gemini Structured Outputs and `googleapis/python-genai` | Developers using JSON response schemas with Gemini | Official docs, last updated 2026-10-20, list the supported subset and state that length and property-count constraints are stripped and ignored. Python SDK 2.33.0 released 2026-10-22. Issue 1815 documents an SDK/API schema-surface mismatch. | Very large or deeply nested schemas may be rejected without a complete public static bound; semantic validity still needs application checks. | Docs are CC BY 4.0 and code samples Apache-2.0; Python SDK is Apache-2.0 with Google contribution rules. | Teams need explicit `requires_runtime_validation` evidence instead of silently treating ignored constraints as enforced. |
| Pydantic AI | Typed multi-provider agents with native, tool, and prompted output modes | Active repository with 4,600+ commits; issue 4917/4160 documents provider-capability ambiguity for Ollama through an OpenAI-compatible endpoint. Model profiles include schema transformers. | Framework transformations are provider/model abstractions, not a dated standalone route contract. Some dynamic schemas are not response-validated by `StructuredDict`. | MIT; substantial test and documentation requirements. | SchemaRoute should complement frameworks with a content-minimized CI artifact, not replace their runtime adapters. |
| llguidance and JSONSchemaBench | Engine authors evaluating constrained decoding coverage and speed | llguidance has 1,500+ commits, current October 2026 fixes, documented JSON Schema coverage, and issue 362 for proactive validation. JSONSchemaBench measures about 9,558 schemas across engine coverage and efficiency. | Focused on grammar engines and model generation, not commercial-provider fallback compatibility. JSONSchemaBench's repository does not expose a root license file, so its dataset will not be copied. | llguidance is MIT with Rust/Python test and lint rules. JSONSchemaBench data has source-specific provenance constraints. | A small independently authored provider-route corpus is safer and tests a different question. |
| Applied ML index and the original Deequ paper | Production teams defining declarative quality checks before downstream use | The index led to the 2018 VLDB paper and Apache-2.0 Deequ repository. The paper motivates automated, declarative constraint verification and reports company-scale data-quality work. | It concerns data quality at Spark scale, not LLM structured-output portability. The paper is evidence for the validation pattern only; its results are not locally reproduced. | Deequ is Apache-2.0; the paper is CC BY-NC-ND 4.0. No source or data will be copied. | Translate the declarative preflight pattern into a small LLM schema-route audit with original rules and fixtures. |

## Evidence-based gap

Provider docs expose materially different JSON Schema contracts. Frameworks translate schemas and constrained-decoding benchmarks measure engine coverage, but a small, provider-neutral, offline artifact that answers “will every fallback target enforce this contract, and which constraints still require local validation?” remains useful. SchemaRoute will bind every result to named, accessed-date profiles and will never treat lack of a finding as live-provider proof.

## Original value and impact gate

| Gate | Decision |
|---|---|
| Real problem | Failover can turn a valid primary-provider schema into a rejected or weakened secondary request. |
| Current evidence | Official provider limitations, active SDK mismatch issues, and Anthropic's estimator request demonstrate the boundary. |
| Original value | Reliability: deterministic preflight and stable finding codes. Interoperability: one route receipt across three dated profiles. Cost/privacy: no model call or schema upload. |
| Measurability | An authored corpus must beat a JSON-parse-only baseline on exact route verdicts, with all expected findings checked. |
| Finishability | Standard-library Python CLI, three profiles, JSON/HTML/SVG evidence, tests, packaging, and public CI. |
| Maintainability | Versioned profiles, typed findings, no provider SDK runtime dependencies, no automatic schema rewriting. |
| License fit | Independent MIT implementation and original fixtures. No upstream code or benchmark data copied. |

## Scope

### Included

- Profiles named `openai-strict-2026-10-22`, `anthropic-json-2026-10-22`, and `gemini-json-2026-10-22`.
- Structural JSON Schema checks with JSON Pointer locations.
- OpenAI documented root, required-field, closed-object, composition, property, nesting, string, and enum limits.
- Anthropic documented unsupported constraints, recursive/external reference limits, optional-parameter and union budgets, closed objects, and citations/prefill feature conflicts.
- Gemini warnings for documented ignored length and property-count constraints, plus conservative warnings for unverified keywords.
- Route verdicts: `portable`, `requires_runtime_validation`, or `blocked`.
- Deterministic schema digest and profile metadata in JSON and standalone HTML.
- Versioned original synthetic evaluation corpus and JSON-parse-only baseline.

### Excluded

- Live API dry runs, model quality or semantic correctness, SDK emulation, schema rewriting, code generation, full JSON Schema validation, provider pricing, and undocumented internal grammar prediction.
- Claims about models or provider behavior beyond the cited profiles.
- Secrets, prompts, responses, or uploaded schemas.

## CLI and output contract

```text
schemaroute profiles
schemaroute audit SCHEMA.json --targets openai-strict-2026-10-22,anthropic-json-2026-10-22,gemini-json-2026-10-22 [--features FEATURES.json] [--json OUT.json] [--html OUT.html]
schemaroute benchmark CORPUS.json [--json OUT.json] [--svg OUT.svg]
```

`audit` exits 0 for `portable`, 1 for `requires_runtime_validation` or `blocked`, and 2 for invalid input or arguments. Output contains a schema SHA-256 digest, not schema content. Findings contain stable codes, severity, profile, JSON Pointer, and a short explanation.

## Acceptance tests

1. Source tests cover pointer escaping, deterministic ordering, each profile rule, feature conflicts, CLI exits, HTML escaping, and malformed inputs.
2. At least 12 independently authored cases produce exact expected route verdicts and finding-code sets.
3. SchemaRoute's exact-verdict accuracy exceeds the declared baseline by at least 50 percentage points.
4. A safe three-provider example returns `portable` with zero findings.
5. A route containing provider-specific failures returns `blocked` with evidence for every blocking target.
6. Gemini ignored-constraint cases return `requires_runtime_validation`, not `portable`.
7. Ruff, compilation, source/wheel build, isolated wheel install, README style, SVG XML, deterministic artifact regeneration, secret-pattern scan, and Git whitespace checks pass.
8. Public CI passes on Python 3.10, 3.12, and 3.14 if workflow publication is authorized.

## Risks and mitigations

- Profile drift: profile names include the access date and every report includes the profile metadata.
- False assurance: passing means “no documented static conflict found,” not provider acceptance or semantic safety.
- Undocumented complexity: do not invent thresholds; emit an explicit limitation instead of a pass claim where applicable.
- Sensitive property names: reports expose JSON Pointers for actionability. Document that reports may reveal schema field names; schema content is otherwise omitted.
- Incorrect schema walker: test nested objects, arrays, combinators, definitions, and pointer escaping.

## Publication plan

Create an independent public MIT repository at `https://github.com/Ikteder/schemaroute` only after local verification. Publish source and evidence intentionally, verify local and remote commit identity, and wait for public CI. If workflow or repository creation is blocked, preserve the verified local repository and record the one-time authorization required.
