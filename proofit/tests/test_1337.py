"""The 1337 module as proofit rules R11-R14.

Test fixture: the actual poisoned brief from the 2026-10-09 morning
standup (run fedb881c32da) — exactly 1,337 characters, header dated
2023-10-05, builder and verifier making the identical false
"MEMORY.md is missing" claim. Reconstructed verbatim from
staff/langchain/test_leet.py (AST-extracted, repr round-trip); the
length assertion below pins it.
"""
import os
from datetime import date

import pytest

from proofit import leet, lint_text
from proofit.parser import parse


# The actual poisoned brief — DO NOT EDIT (length must stay 1337).
POISONED_BRIEF = '**Morning Brief for Ryan**  \n**2023-10-05: Missing Files & Task Failures**  \n**Critical Issue: Multiple teams report missing files (MEMORY.md, scout.md) and recurring task failures in Kentucky claims.**  \n\n**Scout**  \nNOTICED: File "staff/briefings/scout.md" is missing.  \nPROPOSE: Investigate cause and propose prevention measures.  \nNEEDS RYAN: Approval to proceed with investigation.  \n\n**Builder**  \nNOTICED: MEMORY.md file is missing.  \nPROPOSE: Retrieve from backups or version control.  \nNEEDS RYAN: Access to backup/version control systems.  \n\n**Verifier**  \nNOTICED: MEMORY.md is missing, risking data integrity.  \nPROPOSE: Restore from backups, check version history.  \nNEEDS RYAN: Access to version control logs/backups.  \n\n**Clerk**  \nNOTICED: Staff devlog (DEVLOG.md) lacks updates for the past week.  \nPROPOSE: Backfill entries with full details.  \nNEEDS RYAN: Nothing.  \n\n**Runner**  \nNOTICED: Builder failing Kentucky unclaimed-property tasks.  \nPROPOSE: Investigate root cause via task logs.  \nNEEDS RYAN: Access to task logs and error messages.  \n\n**OPEN LOOPS**  \n- Scout: Approval for missing file investigation.  \n- Builder/Verifier: Access to backup/version control systems.  \n- Runner: Permission to access Kentucky task logs.  \n\n**Closing Line:** Turns out the real missing file was the clarity to fix the chaos.\n'


def rules_of(text):
    return sorted({v.rule for v in lint_text(text).violations})


def violations_of_rule(text, rule):
    return [v for v in lint_text(text).violations if v.rule == rule]


@pytest.fixture()
def memfile(tmp_path, monkeypatch):
    """A tmp root where MEMORY.md exists — deterministic R14 resolution."""
    (tmp_path / "MEMORY.md").write_text("x")
    monkeypatch.setattr(leet, "_FILE_ROOTS", [str(tmp_path)])
    return tmp_path


# ---------------------------------------------------------------------------
# The fixture: fires all four 1337 rules, exactly once each
# ---------------------------------------------------------------------------

def test_fixture_is_exactly_1337_chars():
    assert len(POISONED_BRIEF) == 1337


def test_poisoned_brief_fires_all_four_1337_rules(memfile):
    v11 = violations_of_rule(POISONED_BRIEF, 11)
    v12 = violations_of_rule(POISONED_BRIEF, 12)
    v13 = violations_of_rule(POISONED_BRIEF, 13)
    v14 = violations_of_rule(POISONED_BRIEF, 14)
    assert len(v11) == 1, v11
    assert len(v12) == 1, v12
    assert len(v13) == 1, v13
    assert len(v14) == 1, v14


def test_poisoned_brief_severities(memfile):
    by_rule = {v.rule: v for v in lint_text(POISONED_BRIEF).violations
               if v.rule in (11, 12, 13, 14)}
    assert by_rule[11].severity == "ERROR"
    assert by_rule[12].severity == "ERROR"
    assert by_rule[13].severity == "WARNING"   # namesake: half joke, half real
    assert by_rule[14].severity == "ERROR"


def test_poisoned_brief_fails_lint(memfile):
    # R11/R12/R14 are ERROR: the poisoned brief cannot pass.
    assert not lint_text(POISONED_BRIEF).passed


def test_r11_names_builder_and_verifier(memfile):
    v11 = violations_of_rule(POISONED_BRIEF, 11)
    assert "builder" in v11[0].message and "verifier" in v11[0].message
    assert "memory.md" in v11[0].message


def test_r12_names_the_stale_date(memfile):
    v12 = violations_of_rule(POISONED_BRIEF, 12)
    assert "2023-10-05" in v12[0].message


def test_r13_names_the_reading(memfile):
    v13 = violations_of_rule(POISONED_BRIEF, 13)
    assert "1337" in v13[0].message and "leet" in v13[0].message


def test_r14_names_the_hallucinated_file(memfile):
    v14 = violations_of_rule(POISONED_BRIEF, 14)
    assert "MEMORY.md" in v14[0].message
    assert "false file claim" in v14[0].message


# ---------------------------------------------------------------------------
# R11 — cross-role duplication
# ---------------------------------------------------------------------------

def test_r11_quiet_when_claims_differ():
    doc = ("### scout\nnotes-tmp.md is missing, skipped that read.\n\n"
           "### clerk\narchive-old.md is missing, filed without it.\n")
    assert not violations_of_rule(doc, 11)


def test_r11_quiet_when_both_roles_date_today():
    # Both roles dating their sections today is normal, not poison.
    # (today computed at runtime — never hardcode a date here.)
    today = date.today().isoformat()
    doc = (f"### scout\n{today}: all quiet.\n\n"
           f"### clerk\n{today}: filed everything.\n")
    assert not violations_of_rule(doc, 11)


def test_r11_fires_on_shared_off_date():
    doc = ("### scout\n2023-10-05: nothing to report.\n\n"
           "### runner\n2023-10-05: sweep clear.\n")
    v11 = violations_of_rule(doc, 11)
    assert len(v11) == 1
    assert "2023-10-05" in v11[0].message


def test_r11_quiet_without_role_sections():
    doc = "Morning brief - no roles here.\nnotes-tmp.md is missing.\n"
    assert not violations_of_rule(doc, 11)


# ---------------------------------------------------------------------------
# R12 — header date check
# ---------------------------------------------------------------------------

def test_r12_quiet_on_today_header():
    doc = f"Morning brief — {date.today().isoformat()}\n\nNothing to report.\n"
    assert not violations_of_rule(doc, 12)


def test_r12_quiet_without_header_date():
    assert not violations_of_rule("No date anywhere in this document.\n", 12)


def test_r12_fires_on_stale_header():
    doc = "**2023-10-05: status**\n\nAll quiet.\n"
    v12 = violations_of_rule(doc, 12)
    assert len(v12) == 1
    assert "2023-10-05" in v12[0].message


# ---------------------------------------------------------------------------
# R13 — suspicious character count (namesake)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("n,reading", [
    (93, "dragonflies"),
    (222, "sometimes lucky"),
    (555, "hahaha"),
    (840, "twice as high"),
    (1001, "10:01"),
    (1111, "make a wish"),
    (1217, "Chestnut"),
    (1337, "leet"),
])
def test_r13_fires_on_canon_lengths(n, reading):
    v13 = violations_of_rule("x" * n, 13)
    assert len(v13) == 1
    assert str(n) in v13[0].message and reading in v13[0].message


def test_r13_quiet_on_ordinary_length():
    assert not violations_of_rule("x" * 100, 13)


def test_r13_is_warning_so_it_never_fails_the_draft():
    # WARNING is listed but never fails the draft — unless --strict
    # (PARAM-PROOFIT-001 doctrine). Asserted on the result's own
    # error/warning split, not on a synthetic all-clean draft.
    result = lint_text("x" * 222)
    v13 = [v for v in result.violations if v.rule == 13]
    assert len(v13) == 1
    assert v13[0] in result.warnings
    assert v13[0] not in result.errors


def test_canon_hygiene():
    assert len(leet.CUTE_LENGTHS) == 8
    for n, reading in leet.CUTE_LENGTHS.items():
        assert isinstance(n, int) and n > 0, n
        assert isinstance(reading, str) and reading.strip(), n


# ---------------------------------------------------------------------------
# R14 — missing-file verification
# ---------------------------------------------------------------------------

def test_r14_quiet_on_truly_missing_file(memfile):
    doc = "### scout\ndefinitely-not-a-real-file-xyz123.md is missing.\n"
    assert not violations_of_rule(doc, 14)


def test_r14_fires_when_claimed_file_exists(memfile):
    doc = "### builder\nNOTICED: MEMORY.md is missing.\n"
    v14 = violations_of_rule(doc, 14)
    assert len(v14) == 1
    assert "MEMORY.md" in v14[0].message


def test_r14_quiet_without_missing_claim(memfile):
    assert not violations_of_rule("### scout\nMEMORY.md is current.\n", 14)


# ---------------------------------------------------------------------------
# Waivers and wiring
# ---------------------------------------------------------------------------

def test_1337_checks_are_in_the_lint_run():
    from proofit.checks import ALL_CHECKS
    names = [c.__name__ for c in ALL_CHECKS]
    assert "check_r11_cross_role_dup" in names
    assert "check_r12_header_date" in names
    assert "check_r13_cute_length" in names
    assert "check_r14_false_file_claims" in names


def test_waiver_excuses_r11(memfile):
    doc = ("# waiver(11): roles legitimately restated the shared finding\n"
           "### builder\nMEMORY.md is missing.\n\n"
           "### verifier\nMEMORY.md is missing.\n")
    result = lint_text(doc)
    v11 = [v for v in result.violations if v.rule == 11]
    assert len(v11) == 1
    assert all(v.waived for v in v11)
    assert not [v for v in result.violations if v.rule == 11 and not v.waived]
