"""Tag samples with genre, mood, energy, and custom tags."""

import sys

from samplemind.core.models.sample import SampleUpdate
from samplemind.data.orm import init_orm
from samplemind.data.repositories.sample_repository import SampleRepository

VALID_ENERGY = {"low", "mid", "high"}


def tag_samples(name: str, genre=None, mood=None, energy=None, tags=None):
    """Manually tag a sample in the library."""
    init_orm()

    if energy and energy not in VALID_ENERGY:
        print(f"❌ Invalid energy '{energy}'. Choose from: low, mid, high", file=sys.stderr)
        return

    sample = SampleRepository.get_by_name(name)
    if not sample:
        print(f"❌ No sample matching '{name}' found in library.", file=sys.stderr)
        print("   Run `samplemind list` to see what's imported.", file=sys.stderr)
        return

    update = SampleUpdate(genre=genre, mood=mood, energy=energy, tags=tags)
    updated = SampleRepository.tag(sample.path, update)

    if updated:
        print(f"🏷️  Tagged: {sample.filename}", file=sys.stderr)
        if genre:  print(f"   Genre:  {genre}", file=sys.stderr)
        if mood:   print(f"   Mood:   {mood}", file=sys.stderr)
        if energy: print(f"   Energy: {energy}", file=sys.stderr)
        if tags:   print(f"   Tags:   {tags}", file=sys.stderr)
    else:
        print("⚠️  Nothing was updated (no fields provided).", file=sys.stderr)
