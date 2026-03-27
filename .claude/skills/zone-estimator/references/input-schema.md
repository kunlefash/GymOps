# Input Schema

Full structured input for zone-estimator. Missing fields must be inferred conservatively.

## Schema

```json
{
  "title": "string",
  "description": "string",
  "acceptance_criteria": ["string"],
  "repos_affected": ["string"],
  "services_affected": ["string"],
  "components_affected": ["string"],
  "data_model_changes": "none | minor | moderate | major",
  "external_integrations": ["string"],
  "unknowns": ["string"],
  "non_functional_requirements": {
    "performance_sensitive": true,
    "security_sensitive": true,
    "compliance_sensitive": false,
    "availability_sensitive": true
  },
  "testing_requirements": "none | basic | moderate | extensive",
  "deployment_requirements": "none | simple | moderate | complex"
}
```

## Field Reference

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| title | string | Yes | Task title |
| description | string | Yes | Task description; infer from context if missing |
| acceptance_criteria | string[] | Yes | List of AC; missing = UNESTIMABLE if no other context |
| repos_affected | string[] | No | Repos touched; infer from services if missing |
| services_affected | string[] | No | Services/modules; infer from description |
| components_affected | string[] | No | UI/API/components; infer conservatively |
| data_model_changes | enum | No | none, minor, moderate, major; default minor if schema work implied |
| external_integrations | string[] | No | External systems; empty = 0 integration complexity |
| unknowns | string[] | No | List uncertainties; drives confidence (0.1 per unknown) |
| non_functional_requirements | object | No | performance_sensitive, security_sensitive, compliance_sensitive, availability_sensitive; affects operational_complexity |
| testing_requirements | enum | No | none, basic, moderate, extensive |
| deployment_requirements | enum | No | none, simple, moderate, complex |

## Inference Rules

When fields are missing:

- **repos_affected / services_affected**: If only description given, assume single service unless keywords suggest multi-service (e.g. "cross-service", "settlement and auth").
- **data_model_changes**: "minor" if any DB/schema mentioned; "none" only if explicitly no data changes.
- **external_integrations**: Empty unless explicitly stated (API calls, third-party, core banking, etc.).
- **unknowns**: Add one per major uncertainty (undocumented API, unclear requirements, unknown system behavior).
- **testing_requirements**: "moderate" if security/compliance; "basic" for simple features.
- **deployment_requirements**: "moderate" if multi-service or feature flags; "simple" for single deploy.

## Minimal Valid Input

For estimation to proceed, at minimum:
- `title` or `description` (enough to infer scope)
- `acceptance_criteria` or equivalent clarity (otherwise UNESTIMABLE)

All other fields can be inferred; conservative inference increases scores and reduces confidence.
