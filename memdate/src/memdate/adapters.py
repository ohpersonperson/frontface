"""Storage adapters.

The core library talks only to ``StorageAdapter``. The local filesystem
is the default. Google Drive — the original skill's primary location —
is an *optional* seam: ``GoogleDriveAdapter`` documents the interface and
fails loudly with setup instructions instead of pretending to work.

To wire a real backend, subclass ``StorageAdapter`` and pass it to the
operations. All paths are relative to the memory root, using "/" as the
separator.
"""

from __future__ import annotations

import hashlib
import os
import shutil
from abc import ABC, abstractmethod


class StorageError(OSError):
    """Raised when the storage layer fails."""


class DriveNotConfigured(StorageError):
    """Raised by the Google Drive adapter seam (see below)."""


class StorageAdapter(ABC):
    """Minimal surface the memory operations need. Implement for a backend."""

    @abstractmethod
    def read(self, path: str) -> str | None:
        """Return file text, or None if the file does not exist."""

    @abstractmethod
    def write(self, path: str, text: str) -> None:
        """Create or overwrite a file."""

    @abstractmethod
    def append(self, path: str, text: str) -> None:
        """Append text to a file, creating it if needed."""

    @abstractmethod
    def exists(self, path: str) -> bool:
        """True if path exists (file or directory)."""

    @abstractmethod
    def makedirs(self, path: str) -> None:
        """Create a directory and any missing parents."""

    @abstractmethod
    def move(self, src: str, dst: str) -> None:
        """Move/rename a file, creating destination parents as needed."""

    @abstractmethod
    def list_files(self, path: str) -> list[str]:
        """Names of files directly inside a directory (no recursion)."""

    @abstractmethod
    def digest(self, path: str) -> str:
        """SHA-256 hex of a file's bytes. Used for the append-only check."""


class LocalFilesystemAdapter(StorageAdapter):
    """Default adapter. A plain directory on the local filesystem."""

    def __init__(self, root: str) -> None:
        self.root = os.path.abspath(os.path.expanduser(root))

    def _full(self, path: str) -> str:
        full = os.path.abspath(os.path.join(self.root, *path.split("/")))
        if full != self.root and not full.startswith(self.root + os.sep):
            raise StorageError(f"Path escapes the memory root: {path!r}.")
        return full

    def read(self, path: str) -> str | None:
        full = self._full(path)
        if not os.path.isfile(full):
            return None
        with open(full, encoding="utf-8") as f:
            return f.read()

    def write(self, path: str, text: str) -> None:
        full = self._full(path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(text)

    def append(self, path: str, text: str) -> None:
        full = self._full(path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "a", encoding="utf-8") as f:
            f.write(text)

    def exists(self, path: str) -> bool:
        return os.path.exists(self._full(path))

    def makedirs(self, path: str) -> None:
        os.makedirs(self._full(path), exist_ok=True)

    def move(self, src: str, dst: str) -> None:
        src_full, dst_full = self._full(src), self._full(dst)
        os.makedirs(os.path.dirname(dst_full), exist_ok=True)
        shutil.move(src_full, dst_full)

    def list_files(self, path: str) -> list[str]:
        full = self._full(path)
        if not os.path.isdir(full):
            return []
        return sorted(
            name for name in os.listdir(full)
            if os.path.isfile(os.path.join(full, name))
        )

    def digest(self, path: str) -> str:
        full = self._full(path)
        h = hashlib.sha256()
        with open(full, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()


class GoogleDriveAdapter(StorageAdapter):
    """Optional seam for a Google Drive backend. Not a real implementation.

    The original skill stored everything in a Drive folder; this package
    defaults to the local filesystem instead. If you want Drive, subclass
    ``StorageAdapter`` and implement the seven methods — for example by
    shelling out to the ``gws`` CLI or using the Drive API with your own
    credentials. Instantiating this class and calling any method raises
    ``DriveNotConfigured`` with a pointer, so a half-wired Drive setup
    fails loudly instead of silently writing nowhere.
    """

    _MSG = (
        "GoogleDriveAdapter is a seam, not an implementation: it has no "
        "credentials and performs no I/O. To use Google Drive as the "
        "memory root, subclass memdate.StorageAdapter and implement "
        "read/write/append/exists/makedirs/move/list_files/digest against "
        "the Drive API (or the gws CLI), then pass your adapter to the "
        "capture/distill/index functions. Until then, LocalFilesystemAdapter "
        "is the default and the only working backend."
    )

    def read(self, path: str) -> str | None:
        raise DriveNotConfigured(self._MSG)

    def write(self, path: str, text: str) -> None:
        raise DriveNotConfigured(self._MSG)

    def append(self, path: str, text: str) -> None:
        raise DriveNotConfigured(self._MSG)

    def exists(self, path: str) -> bool:
        raise DriveNotConfigured(self._MSG)

    def makedirs(self, path: str) -> None:
        raise DriveNotConfigured(self._MSG)

    def move(self, src: str, dst: str) -> None:
        raise DriveNotConfigured(self._MSG)

    def list_files(self, path: str) -> list[str]:
        raise DriveNotConfigured(self._MSG)

    def digest(self, path: str) -> str:
        raise DriveNotConfigured(self._MSG)


def default_adapter(root: str) -> LocalFilesystemAdapter:
    """The out-of-the-box backend: a local directory."""
    return LocalFilesystemAdapter(root)
