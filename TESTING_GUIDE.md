# Testing Guide — Hack Canada Sponsor Research Pipeline
> For anyone who wants to run and test the pipeline locally.

---

## Prerequisites

Before starting, make sure you have the following installed:
- **Python 3.11 or higher** — check with `python --version` in the terminal
- **Git** — to clone the repo

---

## Step 1 — Clone the repo (terminal)

```bash
git clone https://github.com/e-lizabethwong/COMP354.git
cd COMP354
```

---

## Step 2 — Create a virtual environment (terminal)

This keeps all dependencies isolated from your system Python.

```bash
# Prompt to create the virtual environment
python -m venv venv

# Prompt to activate the virtual environment
# On Windows (Git Bash):
source venv\Scripts\activate

# On Windows (PowerShell or Command Prompt):
venv\Scripts\Activate.ps1

# On Mac/Linux:
source venv/bin/activate
```

You should see `(venv)` appear at the start of your terminal prompt.

---

## Step 3 — Install dependencies (terminal)

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

> Note: `playwright install chromium` downloads a browser (~300MB) used for web scraping.
> This only needs to be done once.

---

## Step 4 — Create your environment variables `.env` file (terminal)

Copy the example file and fill in your details:

```bash
cp env.example .env
```

Open `.env` in any text editor and fill in the following:

### If using OpenAI/ChatGPT API (credits required):
```
LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-key-here
LLM_MODEL=gpt-4o-mini
```

### If using Anthropic/Claude API (credits required):
```
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-anthropic-key-here
LLM_MODEL=claude-sonnet-4-5
```

### If using Google/Gemini API (credits required):
```
LLM_PROVIDER=google
GOOGLE_API_KEY=your-google-key-here
LLM_MODEL=gemini-1.5-flash
```

### If using Playwright (no API key required):
Leave the `LLM_PROVIDER`, `API_KEY`, and `LLM_MODEL` sections as they are, no need to change them.

### Email generator details (optional but recommended):
```
SENDER_NAME=Your Full Name
SENDER_TITLE=Your Title
EVENT_NAME=Your Hackathon Event
EVENT_DATE=Your Hackathon Event Date
EVENT_VENUE=Your Hackathon Event Venue
```

> **Important:** Never commit your `.env` file to git. It is already in `.gitignore`.

---

## Step 5 — Verify the setup (terminal)

Run these quick checks before testing the full pipeline:

```bash
# Check all imports work
python -c "from sponsor_pipeline.config import Settings; from sponsor_pipeline.models import Company, RawLead; from sponsor_pipeline.orchestrator import PipelineOrchestrator; print('All imports OK')"

# Check settings load correctly
python -c "
from sponsor_pipeline.config import Settings
s = Settings.from_env(require_llm=False)
print(f'Provider: {s.llm_provider}')
print(f'Model: {s.llm_model}')
print(f'Sender: {s.sender_name}')
print('Settings OK')
"

# Check CLI application is working
python main.py --help
```

All three should run without errors.

---

## Step 6 — Test the scraper (no API key needed)

In terminal, test that Playwright can crawl a website and extract emails:

```bash
python main.py scrape --url https://conuhacks.io --output test_emails.txt
cat test_emails.txt
```
> **Note:** This prompt makes Playwright crawl `conuhacks` website. 
> To test it with other website, simply replace the https://conuhacks.io url for another one.

Expected output (should show emails found on the ConUHacks website):
```
Website: https://conuhacks.io
sponsor.hackconcordia@ecaconcordia.ca
team.hackconcordia@ecaconcordia.ca
```

You can also scrape multiple URLs from the seed list of sponsors file:
```bash
python main.py scrape data/hackathon_urls.txt --output test_emails.txt
```

---

## Step 7 — Test the email generators (no API key needed)

In terminal, test the initial outreach email generator:
```bash
python generate_initial_outreach.py
```

When prompted:
- **Company name:** `Any company name` (press Enter)
- **Recipient name:** optional (press Enter)
- **Local recipient:** `y` or `n` (press Enter)

You should see a fully formatted sponsorship email with your name and event details.

Test the follow-up email generator:
```bash
python generate_followup_email.py
```

Same prompts as above.

---

## Step 8 — Run the full pipeline (API key required)

> **Note:** This makes real API calls and uses credits. Run it once to verify it works.

### Option A — Run each stage separately (recommended for testing)

```bash
# Stage 1: Discover companies from hackathon websites
python main.py discover

# Stage 2: Score discovered companies (uses LLM credits)
python main.py score

# Stage 3: Research high-scoring companies (uses LLM credits)
python main.py research

# Stage 4: Find contacts for researched companies (uses LLM credits)
python main.py contacts

# Export results to CSV and Markdown
python main.py export --output-dir results/
```

### Option B — Run the full pipeline in one command (terminal)

```bash
python main.py run
```

---

## Step 9 — Check the results (terminal)

After running the pipeline, check what was produced:

```bash
# Check the sponsor CSV
cat data/sponsors.csv

# Check exported results (if you ran export)
ls results/
```

---

## Troubleshooting

**"No module named X"**
Make sure your virtual environment is activated (`venv\Scripts\activate` on Windows) and you ran `pip install -r requirements.txt`.

**"playwright: command not found"**
Use `python -m playwright install chromium` instead of `playwright install chromium`.

**"API key not set"**
Make sure your `.env` file exists and has the correct API key for your chosen provider.

**"LLM_PROVIDER not supported"**
Check that `LLM_PROVIDER` in your `.env` is exactly one of: `anthropic`, `openai`, or `google`.

**Pipeline produces no results**
Check `data/hackathon_urls.txt` exists and has valid URLs. Run the scrape test first to confirm Playwright is working.

---

*Last updated: July 2026 | COMP354 — Introduction to Software Engineering | Concordia University*
