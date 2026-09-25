# Runbook: weekly changelog publish

## Ground Rules & Prerequisites

### Required Baseline

The changelog draft exists.

### Routing Architecture

#### Input spec

Markdown text, under 5000 characters.

#### Service 1: ChangelogGen

- **When to use:** always for the rewrite step
- **Prompt (verbatim):**
  ```
  Rewrite this changelog clearly.
  ```
- **Expected output format:** markdown with H2 sections

#### Service 2: LinkCheck

- **When to use:** after the rewrite
- **Free-tier limits:** 100 URLs per day
- **Prompt (verbatim):**
  ```
  Check these links.
  ```
- **Expected output format:** JSON list of broken URLs

### Needed Tools/Items

- Hardware: a laptop
- Software: a browser
- Accounts: free-tier accounts on both services
- Files: ~/changelog/draft.md

### Expected Outcome

The changelog is published.

### Glossary

- Webhook: a callback URL
- Slug (the URL-friendly version of a title)

## Step-by-Step Directives

### Step 1: Open the editor

**Do:** Open the editor and load the draft file.

**Look for:** The draft text. Formatting is done automatically.

**Verify:** The draft text is visible.

**If wrong:** Wrong file opened.

**Fix:** Reopen the right file.

### Step 2: Rewrite

**Do:** Paste the draft into ChangelogGen.

**Look for:** The output appears.

**Verify:** it works.

### Step 3: Publish

**Do:** Press Continue.

**Look for:** The button.

**If wrong:** Nothing happens.

**Fix:** Click again.

## Validation & Closure

### Step 4: Done

**Do:** Close the browser.

**Look for:** The window closes.
