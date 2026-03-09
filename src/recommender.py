from typing import List, Dict, Tuple, Optional
import csv
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
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
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

# ---------------------------------------------------------------------------
# ALGORITHM RECIPE
# ---------------------------------------------------------------------------
# Maximum possible score: 5.75
#
#   +2.00  genre match      — exact string match on favorite_genre
#   +1.50  mood match       — exact string match on favorite_mood
#   +1.00  energy fit       — 1.0 * (1 - |song.energy - target_energy|)
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


def _score_song(song: Dict, user_prefs: Dict) -> Tuple[float, str]:
    """
    Apply the algorithm recipe to a single song.
    Returns (total_score, explanation_string).
    """
    score = 0.0
    reasons = []

    # --- Genre match: +2.0 ---
    if song.get("genre") == user_prefs.get("favorite_genre"):
        score += 2.0
        reasons.append(f"genre match ({song['genre']})")

    # --- Mood match: +1.5 ---
    if song.get("mood") == user_prefs.get("favorite_mood"):
        score += 1.5
        reasons.append(f"mood match ({song['mood']})")

    # --- Energy proximity: 0–1.0 ---
    target_energy = user_prefs.get("target_energy", 0.5)
    energy_score = 1.0 * (1.0 - abs(song["energy"] - target_energy))
    score += energy_score
    reasons.append(f"energy {song['energy']} vs target {target_energy} (+{energy_score:.2f})")

    # --- Valence proximity: 0–0.75 ---
    # Use explicit target_valence if provided, otherwise derive from mood
    target_valence = user_prefs.get(
        "target_valence",
        _MOOD_VALENCE.get(user_prefs.get("favorite_mood", ""), 0.5)
    )
    valence_score = 0.75 * (1.0 - abs(song["valence"] - target_valence))
    score += valence_score
    reasons.append(f"valence {song['valence']} vs target {target_valence:.2f} (+{valence_score:.2f})")

    # --- Acousticness fit: 0–0.5 ---
    likes_acoustic = user_prefs.get("likes_acoustic", False)
    if likes_acoustic:
        acoustic_score = 0.5 * song["acousticness"]
    else:
        acoustic_score = 0.5 * (1.0 - song["acousticness"])
    score += acoustic_score
    reasons.append(f"acousticness fit (+{acoustic_score:.2f})")

    explanation = "; ".join(reasons)
    return round(score, 4), explanation


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
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
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """
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
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py
    Returns list of (song_dict, score, explanation) sorted by score descending.
    """
    scored = [(_score_song(song, user_prefs) + (song,)) for song in songs]
    # scored items: (score, explanation, song)
    scored.sort(key=lambda x: x[0], reverse=True)
    return [(song, score, explanation) for score, explanation, song in scored[:k]]
