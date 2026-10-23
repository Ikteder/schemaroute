# Decision: use dated conservative provider profiles

Date: 2026-10-22

## Decision

Profile names include their documentation access date. SchemaRoute reports only deterministic documented conflicts as errors. Documented ignored constraints and unverified keywords become warnings that require runtime validation. The tool does not automatically rewrite schemas.

## Why

Provider contracts and SDK transformations change. A timeless capability matrix would age silently. Conservative warnings preserve useful evidence without claiming that an unlisted keyword is rejected. Avoiding rewrites prevents the auditor from changing application semantics.

## Tradeoffs

Some schemas that work live will receive warnings. Users must periodically add new profiles instead of silently editing old evidence. The result is easier to audit and reproduce.
