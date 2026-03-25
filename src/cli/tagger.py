"""
tagger.py — CLI command to manually tag a sample in the library.

Usage examples:
  python main.py tag kick_120 --genre trap --mood dark --energy high
  python main.py tag hihat    --tags "hi-hat,percussion,loop"
  python main.py tag bass     --mood chill --energy low

The sample is found by partial filename match, so you don't need to type
the full filename — just enough to identify it uniquely.
"""

from data.database import get_sample_by_name, init_db, tag_sample

VALID_ENERGY = {"low", "mid", "high"}


def tag_samples(name: str, genre=None, mood=None, energy=None, tags=None):
    init_db()

    if energy and energy not in VALID_ENERGY:
        print(f"❌ Invalid energy '{energy}'. Choose from: low, mid, high")
        return

    sample = get_sample_by_name(name)
    if not sample:
        print(f"❌ No sample matching '{name}' found in library.")
        print("   Run `python main.py list` to see what's imported.")
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
