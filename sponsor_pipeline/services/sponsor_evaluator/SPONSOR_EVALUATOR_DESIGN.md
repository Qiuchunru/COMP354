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

The final score is a weighted average of these six. **Weights are equal for now and will be adjusted later** in `criteria.py`

A company can score high on just one or two dimensions and still be a great lead, example a trading firm might score 0 on Developer Ecosystem but 10 on Talent Acquisition, and that's fine.

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

## Pipeline flow
```
Discovery stage
  (Company + Evidence)
        │
        ▼
  SponsorEvaluator
        │
        ├── Sends evidence to the LLM
        ├── Gets back scores for each dimension
        ├── Calculates the overall weighted score
        └── Assembles the full SponsorScore
        │
        ▼
  Saved to persistence -> exported to CSV / shown in CLI
```

---

## Ground rules
- **Every score needs evidence behind it.** The LLM can't just give a company a high score because it's a well-known name.
- **The six dimensions are independent.** Being weak in one shouldn't drag down a strong score in another
- **This module doesn't scrape or find contacts.** That's the discovery and contact stages, the evaluator only evaluates

