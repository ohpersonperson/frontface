"""proofit — fail-closed linter for locked-down runbooks."""
from .linter import lint_file, lint_text
from .model import LintResult, Runbook, Step, Violation
from .parser import parse

__version__ = "1.0.0"
__all__ = [
    "lint_file",
    "lint_text",
    "parse",
    "LintResult",
    "Runbook",
    "Step",
    "Violation",
    "__version__",
]
