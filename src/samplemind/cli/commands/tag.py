"""Tag samples with genre, mood, energy, and custom tags."""

from samplemind.data.database import init_db, get_sample_by_name, tag_sample

VALID_ENERGY = {"low", "mid", "high"}


def tag_samples(name: str, genre=None, mood=None, energy=None, tags=None):
    """Manually tag a sample in the library."""
    init_db()

    if energy and energy not in VALID_ENERGY:
        print(f"❌ Invalid energy '{energy}'. Choose from: low, mid, high")
        return

    sample = get_sample_by_name(name)
    if not sample:
        print(f"❌ No sample matching '{name}' found in library.")
        print("   Run `samplemind list` to see what's imported.")
        return

    updated = tag_sample(
        path=sample["path"],
        genre=genre,
        mood=mood,
        energy=energy,
        tags=tags,
    )

    if updated:
        print(f"🏷️  Tagged: {sample['filename']}")
        if genre:  print(f"   Genre:  {genre}")
        if mood:   print(f"   Mood:   {mood}")
        if energy: print(f"   Energy: {energy}")
        if tags:   print(f"   Tags:   {tags}")
    else:
        print("⚠️  Nothing was updated (no fields provided).")
