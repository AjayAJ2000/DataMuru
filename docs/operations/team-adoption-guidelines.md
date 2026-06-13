# Team Adoption Guidelines

This page is for platform teams evaluating how to introduce DataMuru in a real organization.

## Suggested adoption path

1. Start with a single sandbox or personal workspace.
2. Validate the configuration and plan flow locally.
3. Review edition boundaries and choose the right product track.
4. Establish pull request review for DataMuru config changes.
5. Expand only after the provider behavior for your needed resource surface is production-ready.

## Roles to involve early

- platform engineering
- data governance or security leads
- developer experience owners
- release engineering if PyPI or internal package promotion is involved

## Internal standards to define early

- version pinning policy
- environment naming convention
- secrets handling convention
- ownership of governance taxonomy changes
- release note expectations for config-contract changes

## Documentation expectations

For enterprise credibility, every rollout should pair:

- package version
- documentation version
- config example set
- change summary

That discipline matters more than clever automation in the early stages of a platform product.
