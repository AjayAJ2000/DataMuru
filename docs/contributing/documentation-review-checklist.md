# Review documentation changes

Use this checklist for new pages and material edits.

## Reader and purpose

- [ ] The page names its reader, prerequisite knowledge, and intended outcome.
- [ ] The content uses the correct type: tutorial, how-to, concept, or reference.
- [ ] The most likely user question is answered before edge cases.

## Technical accuracy

- [ ] Commands match current `--help` output.
- [ ] Configuration fields match models and schemas.
- [ ] Examples use sanitized, non-production values.
- [ ] Expected results and failure recovery are documented.
- [ ] Capability and edition boundaries are explicit.

## Structure and language

- [ ] The page has one descriptive level-one heading.
- [ ] Headings are imperative or user-centered where appropriate.
- [ ] Paragraphs and list items lead with identifiable concepts.
- [ ] Links describe their destination without “click here.”
- [ ] Terms are consistent with the glossary and neighboring pages.
- [ ] Language is inclusive, direct, and free from unnecessary idiom.

## Accessibility

- [ ] Heading levels are sequential.
- [ ] Information does not depend on color, position, or an image alone.
- [ ] Images have meaningful alternative text or empty alt text when decorative.
- [ ] Tables include headers and contain genuinely tabular information.
- [ ] Keyboard focus and narrow-screen layout remain usable.

## Maintenance and publication

- [ ] The page is included in navigation or intentionally discoverable by links.
- [ ] Related README, changelog, examples, and reference pages are updated.
- [ ] `python -m mkdocs build --strict` passes.
- [ ] Documentation tests and external-link checks pass.
- [ ] The pull request identifies the responsible reviewer.
