# Get support and provide feedback

DataMuru OSS is community-supported alpha software. The public project does not
provide an uptime or response-time SLA.

## Choose the correct channel

| Need | Channel |
| --- | --- |
| Documentation is unclear, missing, or incorrect | [Documentation issue](https://github.com/AjayAJ2000/DataMuru/issues/new?template=documentation.yml) |
| Reproducible software defect | [Bug report](https://github.com/AjayAJ2000/DataMuru/issues/new?template=bug.yml) |
| Product or documentation proposal | [Feature request](https://github.com/AjayAJ2000/DataMuru/issues/new?template=feature.yml) |
| Security vulnerability or exposed credential | [Private vulnerability report](https://github.com/AjayAJ2000/DataMuru/security/advisories/new) |

Use the **Edit this page** action on any documentation page for a direct
documentation pull request.

## Search before reporting

1. Search the documentation and existing GitHub issues.
2. Run `validate`, `doctor --output json`, and the failing command again.
3. Compare the behavior with the
   [current capability reference](../reference/capabilities-limits.md).

## Include useful diagnostic information

Provide:

- DataMuru version from `python -m pip show datamuru`;
- operating system and Python version;
- command and redacted configuration shape;
- structured error code;
- expected and actual behavior;
- smallest reproducible example.

Do not provide tokens, customer data, personal email addresses, private
workspace URLs, or account identifiers.

## Documentation feedback standard

Explain:

- what goal you were trying to complete;
- which page or heading you used;
- where you became blocked or uncertain;
- what information would have resolved the problem.

This context is more actionable than saying that a page is confusing.
