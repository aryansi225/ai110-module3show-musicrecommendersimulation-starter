"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

import argparse
import os
import sys

# Ensure `src/` is on the path whether invoked as `python -m src.main`
# (cwd = /workspace) or `python main.py` (cwd = /workspace/src)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from recommender import load_songs, recommend_songs

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_WIDTH = 60

# ---------------------------------------------------------------------------
# User profiles — standard + adversarial edge cases
# ---------------------------------------------------------------------------

PROFILES = {
    # --- Standard profiles ---
    "High-Energy Pop": {
        "favorite_genre": "pop",
        "favorite_mood":  "happy",
        "target_energy":  0.90,
        "target_valence": 0.80,
        "likes_acoustic": False,
    },
    "Chill Lofi": {
        "favorite_genre": "lofi",
        "favorite_mood":  "chill",
        "target_energy":  0.38,
        "target_valence": 0.58,
        "likes_acoustic": True,
    },
    "Deep Intense Rock": {
        "favorite_genre": "rock",
        "favorite_mood":  "intense",
        "target_energy":  0.85,
        "target_valence": 0.50,
        "likes_acoustic": False,
    },
    # --- Adversarial / edge-case profiles ---
    # Conflicting: high energy + sad mood (arousal vs. valence mismatch)
    "High-Energy Sad": {
        "favorite_genre": "blues",
        "favorite_mood":  "sad",
        "target_energy":  0.90,
        "target_valence": 0.25,
        "likes_acoustic": False,
    },
    # Genre with no catalog match — should surface only on numeric proximity
    "Unknown Genre": {
        "favorite_genre": "bossa nova",
        "favorite_mood":  "relaxed",
        "target_energy":  0.40,
        "target_valence": 0.70,
        "likes_acoustic": True,
    },
    # Extremes: max energy + max acoustic (physically contradictory preferences)
    "Max Energy + Max Acoustic": {
        "favorite_genre": "folk",
        "favorite_mood":  "intense",
        "target_energy":  1.00,
        "target_valence": 0.50,
        "likes_acoustic": True,
    },
}


def _bar(score: float, max_score: float = 5.75, width: int = 20) -> str:
    """Render a simple ASCII score bar, e.g. [████████░░░░░░░░░░░░]."""
    filled = round((score / max_score) * width)
    return "[" + "█" * filled + "░" * (width - filled) + "]"


def _print_header(label: str, user_prefs: dict) -> None:
    print("\n" + "=" * _WIDTH)
    print(f"  Profile : {label}")
    print("=" * _WIDTH)
    print(f"  Genre   : {user_prefs['favorite_genre']}")
    print(f"  Mood    : {user_prefs['favorite_mood']}")
    print(f"  Energy  : {user_prefs['target_energy']}")
    print(f"  Acoustic: {'yes' if user_prefs['likes_acoustic'] else 'no'}")
    print("=" * _WIDTH)


def _print_recommendation(rank: int, song: dict, score: float, explanation: str) -> None:
    max_score = 5.75
    bar = _bar(score, max_score)
    pct = (score / max_score) * 100

    print(f"\n  #{rank}  {song['title']}  —  {song['artist']}")
    print(f"       {bar}  {score:.2f} / {max_score:.2f}  ({pct:.0f}%)")
    print(f"       Genre: {song['genre']}  |  Mood: {song['mood']}  "
          f"|  Energy: {song['energy']}")
    print("       Why recommended:")
    for reason in explanation.split("; "):
        print(f"         • {reason}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Music Recommender Simulation")
    parser.add_argument(
        "profiles",
        nargs="*",
        metavar="PROFILE",
        help=f"Profile name(s) to run. Available: {list(PROFILES)}. Runs all if omitted.",
    )
    args = parser.parse_args()

    selected = args.profiles if args.profiles else list(PROFILES)
    unknown = [p for p in selected if p not in PROFILES]
    if unknown:
        parser.error(f"Unknown profile(s): {unknown}. Available: {list(PROFILES)}")

    songs = load_songs(os.path.join(_ROOT, "data", "songs.csv"))
    print(f"Loaded songs: {len(songs)}")

    for label in selected:
        prefs = PROFILES[label]
        recommendations = recommend_songs(prefs, songs, k=5)
        _print_header(label, prefs)
        for rank, (song, score, explanation) in enumerate(recommendations, start=1):
            _print_recommendation(rank, song, score, explanation)
        print("\n" + "-" * _WIDTH)


if __name__ == "__main__":
    main()
