# Sponsor Evaluator — Design Doc

## What this does
This module takes what we know about a company and decides how good of a sponsor they'd actually be for Hack Canada.

The key idea: **a big, famous company is not automatically a good sponsor.** We want companies that have a real reason to care about our audience, students, Canadian talent, hackathons, developer tools.

The output is a scored report per company that our outreach team can act on directly.

---

## What goes in
We pass two things into the evaluator for each company:

**Company** — the basics: name, website, industry, and a short description.

**Evidence** — everything we've collected about them so far. This includes things like:
- Are they hiring interns or new grads in Canada?
- Do they have a public API or developer tool students can build with?
- Have they sponsored hackathons or student events before?
- Is there a real person we can contact (DevRel, recruiter, partnerships)?
- How big are they, and do they have the budget?
- Do they have Canadian offices, Waterloo co-ops, or Canadian recruiting?

Every score the evaluator gives has to come from this evidence, we don't reward companies just for being well-known.

---

## How we score them
We score each company across **six dimensions**, from 0 -10

| Dimension | What it's asking |

| **Talent Acquisition Fit** | Do they want to hire our students? |
| **Developer Ecosystem Fit** | Can students actually build with their product at a hackathon? |
| **Community Sponsorship Fit** | Have they sponsored similar events before? |
| **Outreach Accessibility** | Is there a real person we can reach out to? |
| **Sponsorship Capacity** | Do they have the budget to sponsor? |
| **Strategic Alignment** | Do their goals overlap with what Hack Canada offers? |

the final score is a weighted average of these six, configured in `criteria.py`:

| Dimension | Weight | comment |
| Community Sponsorship Fit | 2.0 | past sponsorship behavior is the strongest predictor of future sponsorship |
| Talent Acquisition Fit | 1.5 | reliable primary motivation for tech companies |
| Outreach Accessibility | 1.5 | no reachable contact means the pipeline stalls regardless of score |
| Sponsorship Capacity | 1.5 | no budget -> no deal |
| Strategic Alignment | 1.25 | Canada/Waterloo fit is secondary to the above |
| Developer Ecosystem Fit | 0.75 | relevant for APIs but not a prerequisite for a sponsorship|

A company can score high on just one or two dimensions and still be a great lead

---

## What comes out
For each company, the evaluator produces a `SponsorScore` with:

- The company info
- A score for each of the six dimensions
- An overall sponsorship score (0–10)
- Why they'd sponsor us (hiring, developer adoption, brand visibility — can be more than one)
- A confidence level (how much evidence we had)
- A plain-English explanation of the score
- Key strengths and weaknesses
- The best angle for our outreach pitch
- Who we should contact at the company

This output is structured so the CLI can display it, the export module can write it to CSV, and the persistence layer can save it.

---

## Pipeline Flow

```text
Discovery Stage
(Company + Evidence)
        │
        ▼
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
schemas.py
   Defines data structures:                                          I/O structuring stage
    - Company                                            Purpose: standardizes all data used across the system
    - Evidence
    - CriterionScore
    - SponsorScore
        │
        ▼
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
evaluator.py
   SponsorEvaluator (core orchestrator)                              Evaluation stage
    ├── Evaluates each sponsorship dimension               Purpose: controls the evaluation workflow, not the math
    ├── (Later) sends evidence to LLM for scoring                    it does not have an LLM prompt, prompt engineering lives in llm/
    ├── Collects the six criterion scores
        │
        │                                                How will it work:
        │
        │                                                evaluator.py
        │                                                 │
        │                                                 ├── calls ->
        │                                                 │     llm/sponsor_dimension_evaluator.py  (where the LLM prompt lives)
        │                                                 │
        │                                                 │         -> sends prompt to model
        │                                                 │         -> returns structured scores
        │                                                 │
        │                                                 ▼
        │                                                collects results
        │
        ▼
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
scoring.py
   ScoreCalculator                                                   Calculation stage
    ├── Validates criterion scores (0–10)                 Purpose: converts individual scores into a final weighted score
    ├── Applies configurable weights (from criteria.py)
    └── Computes overall sponsorship score
        │
        ▼
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
SponsorScore (schemas.py)
   Final structured output:                                          Output production stage
    ├── Company info                                       Purpose: clean, exportable result object for CLI / CSV / storage
    ├── 6 criterion scores
    ├── Overall score
    ├── Confidence level
    ├── Explanation
    ├── Sponsorship motivations
    ├── Strengths & weaknesses
    └── Outreach recommendation
        │
        ▼
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
Persistence / Export / CLI
```

---

## Ground rules
- **Every score needs evidence behind it.** The LLM can't just give a company a high score because it's a well-known name.
- **The six dimensions are independent.** Being weak in one shouldn't drag down a strong score in another
- **This module doesn't scrape or find contacts.** That's the discovery and contact stages, the evaluator only evaluates

