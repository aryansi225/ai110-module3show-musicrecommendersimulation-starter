from typing import List, Dict, Tuple, Optional
import csv
from dataclasses import dataclass

@dataclass
class Song:
    """A single song and its audio attributes loaded from the CSV catalog."""
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """A user's stated taste preferences used to score and rank songs."""
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

# ---------------------------------------------------------------------------
# ALGORITHM RECIPE
# ---------------------------------------------------------------------------
# Maximum possible score: 5.75
#
#   +1.00  genre match      — exact string match on favorite_genre
#   +1.50  mood match       — exact string match on favorite_mood
#   +2.00  energy fit       — 2.0 * (1 - |song.energy - target_energy|)
#   +0.75  valence fit      — 0.75 * (1 - |song.valence - target_valence|)
#                             target_valence is derived from mood (see below)
#   +0.50  acousticness fit — song.acousticness if likes_acoustic
#                             else (1 - song.acousticness)
#
# Ranking: sort descending by total score; ties broken by energy proximity.
# ---------------------------------------------------------------------------

# Derived valence targets per mood — used when user_prefs has no target_valence
_MOOD_VALENCE = {
    "happy":      0.85,
    "euphoric":   0.90,
    "romantic":   0.75,
    "nostalgic":  0.65,
    "relaxed":    0.65,
    "peaceful":   0.70,
    "focused":    0.55,
    "chill":      0.55,
    "moody":      0.40,
    "melancholic":0.30,
    "sad":        0.25,
    "intense":    0.45,
    "angry":      0.20,
}


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Return (total_score, reasons) by applying the 5-rule algorithm recipe to one song."""
    score = 0.0
    reasons = []

    # --- Genre match: +1.0 (halved for weight-shift experiment) ---
    if song.get("genre") == user_prefs.get("favorite_genre"):
        score += 1.0
        reasons.append(f"genre match (+1.0)")

    # --- Mood match: +1.5 ---
    if song.get("mood") == user_prefs.get("favorite_mood"):
        score += 1.5
        reasons.append(f"mood match (+1.5)")

    # --- Energy proximity: 0–2.0 (doubled for weight-shift experiment) ---
    target_energy = user_prefs.get("target_energy", 0.5)
    energy_score = round(2.0 * (1.0 - abs(song["energy"] - target_energy)), 4)
    score += energy_score
    reasons.append(f"energy proximity (+{energy_score:.2f})")

    # --- Valence proximity: 0–0.75 ---
    # Use explicit target_valence if provided, otherwise derive from mood
    target_valence = user_prefs.get(
        "target_valence",
        _MOOD_VALENCE.get(user_prefs.get("favorite_mood", ""), 0.5)
    )
    valence_score = round(0.75 * (1.0 - abs(song["valence"] - target_valence)), 4)
    score += valence_score
    reasons.append(f"valence proximity (+{valence_score:.2f})")

    # --- Acousticness fit: 0–0.5 ---
    likes_acoustic = user_prefs.get("likes_acoustic", False)
    if likes_acoustic:
        acoustic_score = round(0.5 * song["acousticness"], 4)
    else:
        acoustic_score = round(0.5 * (1.0 - song["acousticness"]), 4)
    score += acoustic_score
    reasons.append(f"acousticness fit (+{acoustic_score:.2f})")

    return round(score, 4), reasons


def _score_song(song: Dict, user_prefs: Dict) -> Tuple[float, str]:
    """Internal helper: returns (score, explanation_string) for pipeline use."""
    total, reasons = score_song(user_prefs, song)
    return total, "; ".join(reasons)


class Recommender:
    """OOP wrapper around the scoring and ranking logic for use in tests."""

    def __init__(self, songs: List[Song]):
        """Store the song catalog for repeated recommendation calls."""
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top-k Song objects best matching the given UserProfile."""
        user_prefs = {
            "favorite_genre": user.favorite_genre,
            "favorite_mood":  user.favorite_mood,
            "target_energy":  user.target_energy,
            "likes_acoustic": user.likes_acoustic,
        }
        scored = []
        for song in self.songs:
            song_dict = {
                "genre": song.genre, "mood": song.mood,
                "energy": song.energy, "valence": song.valence,
                "acousticness": song.acousticness,
            }
            total, _ = _score_song(song_dict, user_prefs)
            scored.append((song, total))

        scored.sort(key=lambda x: (x[1], -abs(x[0].energy - user.target_energy)), reverse=True)
        return [s for s, _ in scored[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a semicolon-joined string of scoring reasons for one song."""
        user_prefs = {
            "favorite_genre": user.favorite_genre,
            "favorite_mood":  user.favorite_mood,
            "target_energy":  user.target_energy,
            "likes_acoustic": user.likes_acoustic,
        }
        song_dict = {
            "genre": song.genre, "mood": song.mood,
            "energy": song.energy, "valence": song.valence,
            "acousticness": song.acousticness,
        }
        _, explanation = _score_song(song_dict, user_prefs)
        return explanation


def load_songs(csv_path: str) -> List[Dict]:
    """Read songs.csv and return a list of dicts with numeric fields cast to float."""
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["energy"]       = float(row["energy"])
            row["tempo_bpm"]    = float(row["tempo_bpm"])
            row["valence"]      = float(row["valence"])
            row["danceability"] = float(row["danceability"])
            row["acousticness"] = float(row["acousticness"])
            songs.append(row)
    return songs


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Score every song, sort by score descending, and return the top-k as (song, score, explanation) tuples."""
    # Step 1: score every song — build list of (song, score, joined_reasons)
    scored = []
    for song in songs:
        total, reasons = score_song(user_prefs, song)
        scored.append((song, total, "; ".join(reasons)))

    # Step 2: rank highest score first (sorted returns a new list)
    ranked = sorted(scored, key=lambda item: item[1], reverse=True)

    # Step 3: slice top k
    return ranked[:k]
