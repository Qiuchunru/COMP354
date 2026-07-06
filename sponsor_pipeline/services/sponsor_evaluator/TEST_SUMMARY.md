# Sponsor Evaluator Test Summary

---

## Tested layers

### 1. Data Structures `schemas.py` (14 tests)

This file defines the building blocks every other module uses: Company, Evidence, CriterionScore, SponsorScore, and the Confidence , SponsorMotivation enums

**summary:**
- create a `Company` with just a name, the other fields (website, industry, description) safely default to empty strings, so nothing crashes when data is missing

- Every field on `Evidence` defaults to an empty list, not `None`,  the prompt builders iterate over these lists, a `None` default would cause a crash

- Each `Evidence` instance gets its own independent list

- The `Confidence` and `SponsorMotivation` enums reject invalid values with a clear error 
  ex: if the LLM returns `"High"` instead of `"high"`, the parser fails loudly rather than silently
---

### 2. Evaluation Criteria Configuration `criteria.py` (7 test)

the file defines the six sponsorship dimensions and their weights
(Talent Acquisition, Developer Ecosystem, Community Sponsorship,
Outreach Accessibility, Sponsorship Capacity, Strategic Alignment)

**summary:**
- There are exactly 6 criteria (no accidental additions or removals)

- All criterion keys are unique. a duplicate key would cause one dimension to silently overwrite another in the results dictionary

- All weights are positive, a zero weight would mean a dimension gets scored by the LLM
  (spending tokens & money) but contributes nothing to the final score

- The `CRITERIA_BY_KEY` lookup dictionary is in sync with the `CRITERIA` list

