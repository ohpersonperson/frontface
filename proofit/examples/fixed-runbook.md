# Runbook: weekly changelog publish

## Ground Rules & Prerequisites

### Required Baseline

Starting state: the changelog draft exists at ~/changelog/draft.md and the laptop is connected to the internet.

### Routing Architecture

#### Input spec

Markdown text, under 5000 characters.

#### Service 1: ChangelogGen

- **When to use:** for the rewrite step, every Friday
- **Free-tier limits:** 50 rewrites per day, 4000-character context window
- **Prompt (verbatim):**
  ```
  Rewrite this changelog clearly. Keep all version numbers exact.
  ```
- **Expected output format:** markdown with H2 sections, one per version

#### Service 2: LinkCheck

- **When to use:** after the rewrite, before publishing
- **Free-tier limits:** 100 URLs per day
- **Prompt (verbatim):**
  ```
  Check these links and list the broken ones.
  ```
- **Expected output format:** JSON list of broken URLs, fields: url, status

#### Rate limit handling

When a free-tier limit is hit, wait 60 minutes and retry once; if it still fails, run the remaining work in the other service's slot tomorrow and note the delay in the changelog.

#### Error paths

If a service returns unexpected data, re-run the step once with the same verbatim prompt. If it fails twice, stop and record the raw output in ~/changelog/errors.md.

### Needed Tools/Items

- Hardware: a laptop with 8 GB RAM
- Software: Chrome 120 or newer
- Accounts: free-tier accounts on ChangelogGen and LinkCheck (no API keys)
- Permissions: write access to ~/changelog/
- Files: ~/changelog/draft.md
- Internet access: required throughout (both services are web-only)

### Expected Outcome

~/changelog/published/ contains this week's changelog as index.md, with all links verified.

### Glossary

- Webhook (a URL the service calls when publishing finishes)
- Slug (the URL-friendly version of a title)

## Step-by-Step Directives

### Step 1: Open the draft

**Do:** Open **VS Code**.

**Look for:** The VS Code window opens with the file tree visible.

**Verify:** The editor window displays ~/changelog/draft.md.

**If wrong:** A different file is open.

**Fix:** Press **Ctrl+O**, select **draft.md**, and press **Open**.

### Step 2: Rewrite the draft

**Do:** Paste the draft text into the **ChangelogGen** input box.

**Look for:** The **Rewrite** button becomes clickable.

**Verify:** The output area displays rewritten markdown with H2 sections.

**If wrong:** The output is empty.

**Fix:** Press **Rewrite** once more; if still empty, check the free-tier quota.

### Step 3: Check the links

**Do:** Paste the rewritten text into the **LinkCheck** input box.

**Look for:** A progress bar appears and completes.

**Verify:** The results area contains a JSON list, possibly empty, with url and status fields.

**If wrong:** The page shows an error banner.

**Fix:** Wait 60 seconds and press the **Check again** button.

### Step 4: Publish

**Do:** Click the blue **Publish** button in the bottom-right corner.

**Look for:** A confirmation dialog appears showing the slug.

**Verify:** The dialog displays "Published" and ~/changelog/published/index.md exists.

**If wrong:** The dialog shows an error.

**Fix:** Copy the rewritten text, close the dialog with the **Close** button, and retry from Step 4.

## Validation & Closure

### Success Condition

The week's changelog exists at ~/changelog/published/index.md, every link in it returned a working status from LinkCheck, and the file matches the H2-per-version format.

### Consistency Checkpoints

- [ ] The input met the spec (markdown, under 5000 characters).
- [ ] ChangelogGen received the verbatim prompt and the draft text.
- [ ] ChangelogGen's output matched the expected H2 format.
- [ ] LinkCheck received the rewritten text and returned the JSON schema.
- [ ] Error recovery was never triggered, OR was triggered and resolved correctly.
- [ ] The published changelog contains the intended content.
