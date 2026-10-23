# Contributing

SchemaRoute profiles are evidence claims. Changes to a profile must link primary provider documentation or a reproducible provider response, include an access date, add a regression case, and explain whether the rule blocks a route or only requires runtime validation.

Before opening a change:

```bash
python -m unittest discover -s tests -v
ruff check .
ruff format --check .
python -m build
```

Do not add provider credentials, captured prompts, customer schemas, or third-party benchmark data without explicit license and privacy review.
