# Error codes

DataMuru errors contain a code, title, description, context, suggestion, and
exit code.

| Code | Error | Typical cause |
| --- | --- | --- |
| `DMR-CFG-1001` | Configuration Load Failed | missing file, invalid YAML, or unresolved value |
| `DMR-CFG-1002` | Configuration Validation Failed | invalid field or unsafe combination |
| `DMR-PROV-1001` | Provider Operation Failed | credentials, connectivity, permission, or API failure |
| `DMR-PLAN-1001` | Saved Plan Error | missing, stale, or malformed saved plan |
| `DMR-APPLY-1001` | Apply Dependency Skipped | child resource skipped because its parent failed earlier in the apply |
| `DMR-IMPORT-1001` | Import Adoption Blocked | missing live resources or fingerprint conflicts prevent state adoption |
| `DMR-STATE-1001` | State Backend Error | unsupported backend or inaccessible state |
| `DMR-STATE-REMOTE` | Remote State Boundary | `s3`, `azure_blob`, or `gcs` is configured for OSS plan/apply/adoption before a hosted state extension is available |
| `DMR-CORE-1001` | Unsupported Operation | capability is not implemented for the selected mode |

## Read an error

```text
DMR-PROV-1001 Provider Operation Failed
Databricks API create request failed.
status_code: 400
response: ...
Suggestion: Verify Unity Catalog permissions and the target object name.
```

Use the description to identify the failed action, context to locate the
provider response, and suggestion as the first recovery step.

## Report an error safely

Include:

- DataMuru version;
- command and resource target;
- error code and redacted context;
- execution mode;
- whether validation and doctor succeed.

Exclude tokens, full account identifiers, private URLs, emails, and customer
data.
