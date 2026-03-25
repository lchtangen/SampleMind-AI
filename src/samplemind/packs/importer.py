"""Import and verify .smpack ZIP archives into the SampleMind library.

Import flow:
  1. Validate the file is a ZIP and contains manifest.json.
  2. Parse manifest.json into a PackManifest (Pydantic validation included).
  3. Extract archive to a temporary directory.
  4. Verify every entry's SHA-256 checksum -- raise PackIntegrityError on any
     mismatch or missing file.
  5. Copy verified files to dest_dir (auto-resolved from DB path if not given).
  6. Upsert each sample into the library via SampleRepository.

dry_run=True stops before steps 5-6 so callers can use 'pack verify' without
modifying the library.
"""

from __future__ import annotations

import re
import shutil
import tempfile
import zipfile
from pathlib import Path

from samplemind.core.config import get_settings
from samplemind.core.models.sample import SampleCreate
from samplemind.data.orm import init_orm
from samplemind.data.repositories.sample_repository import SampleRepository
from samplemind.packs.checksums import verify_manifest_checksums
from samplemind.packs.models import PackManifest

# Re-export for callers who only import from this module
from samplemind.core.models.sample import Sample  # noqa: F401 -- public re-export


class PackIntegrityError(Exception):
    """Raised when one or more files in a .smpack archive fail checksum verification."""


def import_pack(
    smpack_path: Path,
    *,
    dest_dir: Path | None = None,
    dry_run: bool = False,
) -> list[Sample]:
    """Verify and import a .smpack archive into the SampleMind library.

    Args:
        smpack_path: Path to the .smpack file.
        dest_dir:    Directory where audio files are copied.  Defaults to
                     ``<db_dir>/packs/<pack_name>/``.
        dry_run:     If True, verify checksums but do NOT copy files or update
                     the library.  Returns an empty list.

    Returns:
        List of Sample ORM objects upserted into the library.
        Empty when dry_run=True.

    Raises:
        FileNotFoundError:  smpack_path does not exist.
        ValueError:         Not a valid ZIP, or manifest.json is missing.
        PackIntegrityError: One or more checksum mismatches.
    """
    if not smpack_path.exists():
        raise FileNotFoundError(f"Pack not found: {smpack_path}")
    if not zipfile.is_zipfile(smpack_path):
        raise ValueError(f"Not a valid .smpack (ZIP) file: {smpack_path}")

    with zipfile.ZipFile(smpack_path, "r") as zf:
        if "manifest.json" not in zf.namelist():
            raise ValueError(f"Pack missing manifest.json: {smpack_path.name}")

        manifest = PackManifest.model_validate_json(zf.read("manifest.json"))

        with tempfile.TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            zf.extractall(tmp)

            failures = verify_manifest_checksums(manifest, tmp)
            if failures:
                raise PackIntegrityError(
                    f"Integrity check failed ({len(failures)} file(s)):\n"
                    + "\n".join(f"  - {f}" for f in failures)
                )

            if dry_run:
                return []

            # Resolve destination directory
            if dest_dir is None:
                db_url = get_settings().database_url
                db_parent = Path(db_url.removeprefix("sqlite:///")).parent
                safe_name = re.sub(r"[^\w.-]", "_", manifest.name.lower()).strip("_")
                dest_dir = db_parent / "packs" / safe_name
            dest_dir.mkdir(parents=True, exist_ok=True)

            init_orm()
            samples: list[Sample] = []
            for entry in manifest.entries:
                src = tmp / entry.filename
                dst = dest_dir / Path(entry.filename).name
                shutil.copy2(src, dst)

                sample = SampleRepository.upsert(
                    SampleCreate(
                        filename=Path(entry.filename).name,
                        path=str(dst.resolve()),
                        bpm=entry.bpm,
                        key=entry.key,
                        energy=entry.energy,
                        mood=entry.mood,
                        instrument=entry.instrument,
                        genre=entry.genre,
                        tags=entry.tags,
                    )
                )
                samples.append(sample)

            return samples
