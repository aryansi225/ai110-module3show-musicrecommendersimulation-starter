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
from tabulate import tabulate

# Ensure `src/` is on the path whether invoked as `python -m src.main`
# (cwd = /workspace) or `python main.py` (cwd = /workspace/src)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from recommender import load_songs, recommend_songs, SCORING_MODES, DiversityConfig

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


def _bar(score: float, max_score: float, width: int = 14) -> str:
    """Render a compact ASCII score bar, e.g. [████████░░░░░░]."""
    filled = round((score / max_score) * width)
    return "[" + "█" * filled + "░" * (width - filled) + "]"


def _print_header(label: str, user_prefs: dict, mode_name: str = "balanced") -> None:
    print("\n" + "=" * _WIDTH)
    print(f"  Profile : {label}")
    print(f"  Mode    : {mode_name}")
    print("=" * _WIDTH)
    print(f"  Genre   : {user_prefs['favorite_genre']}")
    print(f"  Mood    : {user_prefs['favorite_mood']}")
    print(f"  Energy  : {user_prefs['target_energy']}")
    print(f"  Acoustic: {'yes' if user_prefs['likes_acoustic'] else 'no'}")
    print("=" * _WIDTH)


def _print_results_table(
    recommendations: list,
    max_score: float,
) -> None:
    """Render all recommendations as a single tabulate grid table.

    Columns
    -------
    #   — rank
    Song / Artist  — title on line 1, artist on line 2
    Genre · Mood · Nrg  — three song attributes
    Score  — ASCII bar, then "score / max  (pct%)"
    Why Recommended  — each scoring reason on its own bullet line
    """
    rows = []
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        pct = (score / max_score) * 100
        bar = _bar(score, max_score)

        song_cell   = f"{song['title']}\n{song['artist']}"
        attrs_cell  = f"Genre : {song['genre']}\nMood  : {song['mood']}\nEnergy: {song['energy']:.2f}"
        score_cell  = f"{bar}\n{score:.2f} / {max_score:.2f}  ({pct:.0f}%)"
        reasons_cell = "\n".join(f"• {r}" for r in explanation.split("; "))

        rows.append([rank, song_cell, attrs_cell, score_cell, reasons_cell])

    headers = ["#", "Song\nArtist", "Attributes", "Score", "Why Recommended"]
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Music Recommender Simulation")
    parser.add_argument(
        "profiles",
        nargs="*",
        metavar="PROFILE",
        help=f"Profile name(s) to run. Available: {list(PROFILES)}. Runs all if omitted.",
    )
    parser.add_argument(
        "--mode",
        choices=list(SCORING_MODES),
        default="balanced",
        help="Scoring strategy. Choices: %(choices)s. Default: %(default)s.",
    )
    parser.add_argument(
        "--diversity",
        action="store_true",
        help="Enable diversity re-ranking to avoid repeat artists/genres in top results.",
    )
    parser.add_argument(
        "--artist-penalty",
        type=float,
        default=1.5,
        metavar="N",
        help="Score deducted per repeat artist already in top results (default: 1.5).",
    )
    parser.add_argument(
        "--genre-penalty",
        type=float,
        default=0.8,
        metavar="N",
        help="Score deducted per repeat genre already in top results (default: 0.8).",
    )
    args = parser.parse_args()

    selected = args.profiles if args.profiles else list(PROFILES)
    unknown = [p for p in selected if p not in PROFILES]
    if unknown:
        parser.error(f"Unknown profile(s): {unknown}. Available: {list(PROFILES)}")

    weights   = SCORING_MODES[args.mode]
    diversity = DiversityConfig(
        artist_penalty=args.artist_penalty,
        genre_penalty=args.genre_penalty,
    ) if args.diversity else None

    songs = load_songs(os.path.join(_ROOT, "data", "songs.csv"))
    diversity_label = (
        f"ON  (artist -{args.artist_penalty}, genre -{args.genre_penalty})"
        if diversity else "off"
    )
    print(
        f"Loaded songs: {len(songs)}  |  Mode: {weights.name}"
        f"  |  Max score: {weights.max_score}  |  Diversity: {diversity_label}"
    )

    for label in selected:
        prefs = PROFILES[label]
        recommendations = recommend_songs(prefs, songs, k=5, weights=weights, diversity=diversity)
        _print_header(label, prefs, mode_name=weights.name)
        _print_results_table(recommendations, max_score=weights.max_score)
        print("-" * _WIDTH)


if __name__ == "__main__":
    main()
