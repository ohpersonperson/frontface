"""memdate — file-based memory with a hard CAPTURE/DISTILL split.

CAPTURE preserves raw records (append-only, timestamped, never
interpreted). DISTILL consolidates raw into derived distilled.md files
(never touching raw). INDEX regenerates the cross-domain connective
tissue after multi-domain distills.

Front-facing conversion of the ``memdate-v2`` skill (Ryan's
skill-suite, MIT). The original skill's Ryan-specific domains and Google
Drive root are configuration here, not defaults: domains come from
``MemoryConfig`` (neutral defaults shipped), storage is a
``StorageAdapter`` (local filesystem default, Drive an optional seam).
"""

from .adapters import (
    DriveNotConfigured,
    GoogleDriveAdapter,
    LocalFilesystemAdapter,
    StorageAdapter,
    StorageError,
    default_adapter,
)
from .capture import (
    CaptureError,
    CaptureResult,
    InterpretationError,
    capture,
    read_raw,
    route,
    scan_interpretation,
)
from .config import (
    DEFAULT_DOMAINS,
    ConfigError,
    MemoryConfig,
)
from .distill import (
    DistillError,
    DistillResult,
    distill,
    read_distilled,
)
from .drop import SweepItem, ensure_layout, sweep_new
from .frontmatter import FrontmatterError
from .index import IndexError, IndexResult, read_index, regenerate_index

__all__ = [
    "MemoryConfig",
    "ConfigError",
    "DEFAULT_DOMAINS",
    "StorageAdapter",
    "StorageError",
    "LocalFilesystemAdapter",
    "GoogleDriveAdapter",
    "DriveNotConfigured",
    "default_adapter",
    "CaptureError",
    "CaptureResult",
    "InterpretationError",
    "capture",
    "read_raw",
    "route",
    "scan_interpretation",
    "DistillError",
    "DistillResult",
    "distill",
    "read_distilled",
    "SweepItem",
    "ensure_layout",
    "sweep_new",
    "FrontmatterError",
    "IndexError",
    "IndexResult",
    "read_index",
    "regenerate_index",
]

__version__ = "1.0.0"
