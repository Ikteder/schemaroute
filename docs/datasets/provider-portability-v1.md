# Dataset card: provider-portability-v1

Date created: 2026-10-22
License: MIT
Source: original synthetic cases in this repository

## Purpose and schema

The corpus evaluates exact route verdicts and finding-code sets for dated provider profiles. Each case has an ID, selected targets, an inline or generated JSON Schema, optional route features, an expected verdict, and expected finding codes.

## Composition

Fifteen cases cover one portable route and fourteen incompatibility or runtime-validation conditions. Generated cases create property, nesting, optional-parameter, and union-budget boundaries without committing multi-megabyte fixtures.

## Leakage and quality concerns

The same author designed the rules and cases, so the corpus is implementation-aligned and unsuitable for a generalization claim. It contains isolated failures and does not represent the frequency or co-occurrence of production schemas. No provider request or third-party schema is included.

## Exclusions

JSONSchemaBench data was not copied because the repository did not expose a root license file during review and because its engine-coverage task differs from route portability. Customer schemas, prompts, responses, and credentials are excluded.
