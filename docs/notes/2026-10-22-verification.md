# Verification, 2026-10-22

Environment: Windows, Python 3.15.0. The package declares Python 3.10 or newer.

## Results

| Check | Result |
|---|---|
| Unit and CLI tests from source | 12/12 passed |
| Ruff lint | Passed |
| Ruff format check | 15 files passed |
| Python byte compilation | Passed for `src` and `tests` |
| Isolated source and wheel build | Passed |
| Clean wheel install with no dependencies | Passed |
| `pip check` in clean wheel environment | No broken requirements |
| Tests against installed wheel | 12/12 passed |
| Authored portability corpus | SchemaRoute 15/15; parse-only baseline 1/15 |
| Portable and risky CLI exit contract | Exit 0 and exit 1, respectively |
| Generated evidence reproducibility | Six JSON, HTML, and SVG artifacts matched byte for byte |
| SVG XML parse | Passed |
| Browser visual review | Portable and blocked receipts rendered cleanly in Chromium |
| README em dash check | None found |
| Credential-pattern scan | No common provider or GitHub token pattern found |

The missing-file error shown during one CLI test is intentional evidence for the controlled exit-2 path. It does not indicate a failed test.

## Artifact hashes

| Artifact | SHA-256 |
|---|---|
| `docs/experiments/portable-receipt.json` | `BB4DC49F558F14D1FDCCDD1D6A72DF6C0E426705B7E9C3F8FECD00950517C96D` |
| `docs/assets/portable-audit.html` | `31DEB1DB1B90F7D6BB2C05011885B5BA7D5E93F7917F583431B115206B529EC2` |
| `docs/experiments/risky-receipt.json` | `A89225941A48D307822AE20D9E61279DED01290BA167A3AC641515D1B0B4A659` |
| `docs/assets/risky-audit.html` | `CD631A3B7D7EBEF9318356744360C13B9CEEFED7B19B3E1C00B4C30028842989` |
| `docs/experiments/provider-portability-v1-results.json` | `BA417E4E1736EFD84A772AEE5C6DAD33C985B505A04BCAB3F4CF461BD4B90D2D` |
| `docs/assets/provider-portability-v1.svg` | `747D326C7418D181126E8E320B84639B36EFFCAC870A78AE76A3DA8650FD0AF7` |

## Interpretation boundary

This verifies local deterministic behavior and packaging. It does not verify live provider acceptance, model output quality, future provider contracts, or performance on independently collected schemas.
