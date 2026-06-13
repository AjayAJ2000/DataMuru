# Documentation style guide

This guide adapts the principles taught in Google's
[Technical Writing courses](https://developers.google.com/tech-writing) to
DataMuru documentation.

## Write for a defined reader

State prerequisites and assumed knowledge. Prefer one primary audience per page.
Do not make a new user read contributor architecture to complete a task.

## Choose the correct document type

- **Tutorial:** teaches by guiding a complete learning experience.
- **How-to guide:** helps a reader complete a specific task.
- **Concept:** explains how or why the system works.
- **Reference:** provides exact, scannable facts.

Do not combine all four types into one long page.

## Put the action first

Use active voice and imperative task headings:

- “Configure the provider,” not “Provider configuration.”
- “Run doctor,” not “Doctor can be run.”

Lead with the key action or conclusion. Keep subjects and verbs close together.

## Use clear words

- Prefer familiar, specific words.
- Define DataMuru terms on first use.
- Avoid filler, marketing claims, and unexplained abbreviations.
- Use one term for one concept. Say “workspace URL,” not alternating “host,”
  “endpoint,” and “instance link” in prose.
- Use short paragraphs and meaningful lists.

## Structure for scanning

- Start with purpose and outcome.
- List prerequisites before steps.
- Use numbered lists for ordered procedures.
- Use headings that describe the reader's task or question.
- Put warnings immediately before the risky step.
- End tasks with verification and recovery or cleanup.

## Write useful examples

Examples must be minimal, realistic, sanitized, and consistent with maintained
configuration. Show expected output when it helps readers decide whether a step
succeeded.

Never use real:

- tokens or secrets;
- workspace and account identifiers;
- personal email addresses;
- customer or production resource names.

## Document errors as recovery paths

State:

1. what failed;
2. the likely cause;
3. what the reader should inspect;
4. the safest next action.

Preserve stable error codes and quote only the relevant provider response.

## Write accessibly

- Use descriptive link text.
- Do not communicate meaning through color alone.
- Add alternative text to informative images.
- Use tables only for genuinely tabular comparisons.
- Keep heading levels sequential.
- Prefer text and Mermaid diagrams that remain useful with screen readers.

## Verify before merging

```powershell
python -m mkdocs build --strict
```

Also verify:

- internal links resolve;
- commands match `--help`;
- field names match models and schemas;
- examples pass validation where practical;
- implementation status is accurate;
- the page has an owner or clear maintenance location.
