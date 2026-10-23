# Experiment: provider-portability-v1

Date: 2026-10-22
Seed context: `20261022`
Environment: Windows, Python 3.15.0 local interpreter

## Methods

- SchemaRoute 0.1: exact verdict plus exact set of stable finding codes.
- Baseline: parse the JSON and treat every structurally valid schema object as portable.
- Corpus: 15 original synthetic cases.

## Result

| Method | Correct | Accuracy |
|---|---:|---:|
| SchemaRoute 0.1 | 15/15 | 100.00% |
| Parse-only baseline | 1/15 | 6.67% |

The absolute difference is 93.33 percentage points on this authored corpus. This result verifies implementation behavior against its stated contract. It does not estimate production sensitivity, false-positive rate, provider uptime, schema adherence, or semantic correctness.

Machine-readable output is in `provider-portability-v1-results.json` and the generated comparison is in `../assets/provider-portability-v1.svg`.
