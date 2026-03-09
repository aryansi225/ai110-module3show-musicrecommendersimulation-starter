"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

import os
import sys

# Ensure `src/` is on the path whether invoked as `python -m src.main`
# (cwd = /workspace) or `python main.py` (cwd = /workspace/src)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from recommender import load_songs, recommend_songs

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_WIDTH = 60


def _bar(score: float, max_score: float = 5.75, width: int = 20) -> str:
    """Render a simple ASCII score bar, e.g. [████████░░░░░░░░░░░░]."""
    filled = round((score / max_score) * width)
    return "[" + "█" * filled + "░" * (width - filled) + "]"


def _print_header(user_prefs: dict) -> None:
    print("=" * _WIDTH)
    print("  🎵  Music Recommender — Top Picks")
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
    songs = load_songs(os.path.join(_ROOT, "data", "songs.csv"))
    print(f"Loaded songs: {len(songs)}")

    # Full taste profile — all features used by the scoring function
    user_prefs = {
        "favorite_genre": "rock",
        "favorite_mood":  "intense",
        "target_energy":  0.85,
        "target_valence": 0.50,
        "likes_acoustic": False,
    }

    recommendations = recommend_songs(user_prefs, songs, k=5)

    _print_header(user_prefs)
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        _print_recommendation(rank, song, score, explanation)

    print("\n" + "=" * _WIDTH + "\n")


if __name__ == "__main__":
    main()
