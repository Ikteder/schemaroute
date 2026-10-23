# Reference review, 2026-10-22

The full comparison table and source links are in the approved implementation spec. Key observations:

- OpenAI requires an object root, closed objects, and every property marked required. It publishes explicit property, nesting, string, and enum budgets.
- Anthropic supports JSON outputs and strict tools through compiled grammars. Its raw schema subset rejects several common numeric and string constraints, recursion, and open objects. SDK helpers may strip unsupported constraints and validate the original schema after generation.
- Gemini documents a different subset and explicitly strips `minLength`, `maxLength`, `minProperties`, and `maxProperties` rather than enforcing them.
- Pydantic AI and Google SDK issues show that framework, SDK, provider, and compatibility-endpoint capability claims can diverge.
- llguidance and JSONSchemaBench cover engine semantics and efficiency. SchemaRoute addresses provider-route contracts and does not reuse their datasets.
- Applied ML is an index only. The original Deequ paper supports declarative preflight as a production pattern, not any result claimed for this project.

No upstream source, fixture, prompt, or dataset was copied.
