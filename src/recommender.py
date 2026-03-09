from typing import List, Dict, Tuple, Optional
import csv
from dataclasses import dataclass, field

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

# ---------------------------------------------------------------------------
# SCORING MODES  (Strategy pattern)
# ---------------------------------------------------------------------------
# Each ScoringWeights instance is one "strategy". Pass it to score_song() or
# recommend_songs() to switch the ranking behaviour without touching any logic.
#
# Weight meaning:
#   genre / mood     — flat bonus added when there is an exact string match
#   energy / valence / acousticness / popularity / decade
#                    — multiplier applied to a 0–1 proximity value
#   tag_per_hit      — bonus per matching mood_tag (capped at 2 hits)
#
# max_score = genre + mood + energy + valence + acousticness
#           + (tag_per_hit * 2) + popularity + decade
# ---------------------------------------------------------------------------

@dataclass
class ScoringWeights:
    """Holds all per-feature multipliers for one scoring strategy."""
    name:         str
    genre:        float   # flat bonus on exact genre match
    mood:         float   # flat bonus on exact mood match
    energy:       float   # multiplier  (0–1 proximity → 0–energy)
    valence:      float   # multiplier  (0–1 proximity → 0–valence)
    acousticness: float   # multiplier  (0–1 fit     → 0–acousticness)
    tag_per_hit:  float   # bonus per matching mood_tag (max 2 hits)
    popularity:   float   # multiplier  (0–1 fit     → 0–popularity)
    decade:       float   # multiplier  (0–1 fit     → 0–decade)

    @property
    def max_score(self) -> float:
        return round(
            self.genre + self.mood + self.energy + self.valence
            + self.acousticness + (self.tag_per_hit * 2)
            + self.popularity + self.decade,
            4,
        )


# --- Preset strategies ---

SCORING_MODES: Dict[str, ScoringWeights] = {
    # Current default — energy matters most, genre is a secondary tiebreaker
    "balanced": ScoringWeights(
        name="balanced",
        genre=1.0, mood=1.5, energy=2.0, valence=0.75,
        acousticness=0.5, tag_per_hit=0.5,
        popularity=0.75, decade=0.75,
    ),
    # Genre label is the dominant signal — good for loyal genre listeners
    "genre-first": ScoringWeights(
        name="genre-first",
        genre=3.5, mood=1.0, energy=1.0, valence=0.5,
        acousticness=0.25, tag_per_hit=0.25,
        popularity=0.5, decade=0.5,
    ),
    # Emotional feel is king — mood tag matches and valence carry more weight
    "mood-first": ScoringWeights(
        name="mood-first",
        genre=0.5, mood=3.5, energy=1.0, valence=1.0,
        acousticness=0.25, tag_per_hit=0.5,
        popularity=0.5, decade=0.5,
    ),
    # Pure sonic texture — energy + valence dominate, labels almost ignored
    "energy-focused": ScoringWeights(
        name="energy-focused",
        genre=0.5, mood=0.5, energy=4.0, valence=1.0,
        acousticness=0.5, tag_per_hit=0.25,
        popularity=0.25, decade=0.25,
    ),
}

_DEFAULT_MODE = SCORING_MODES["balanced"]


# ---------------------------------------------------------------------------
# DIVERSITY CONFIG
# ---------------------------------------------------------------------------
# Controls the greedy re-ranking pass in recommend_songs().
#
# After all songs are scored independently, the top-k list is assembled one
# song at a time.  Before each pick the adjusted score for every remaining
# candidate is calculated as:
#
#   adjusted = base_score
#            - (artist_penalty  * times artist already appears in selected)
#            - (genre_penalty   * times genre  already appears in selected)
#
# The candidate with the highest adjusted score is selected next.
# The penalty is visible in the explanation string so users can see why a
# song was demoted.
# ---------------------------------------------------------------------------

@dataclass
class DiversityConfig:
    """Penalty amounts applied per repeat artist / genre during greedy selection."""
    artist_penalty: float = 1.5   # deducted per duplicate artist already selected
    genre_penalty:  float = 0.8   # deducted per duplicate genre  already selected


def _greedy_diverse_select(
    scored: List[Tuple[Dict, float, str]],
    k: int,
    diversity: DiversityConfig,
) -> List[Tuple[Dict, float, str]]:
    """Greedily build the top-k list, applying diversity penalties at each step.

    Algorithm
    ---------
    1. Start with an empty selected list and empty seen-artist / seen-genre counts.
    2. For every remaining candidate compute:
           adjusted = base - (artist_penalty * seen_artists[artist])
                           - (genre_penalty  * seen_genres[genre])
    3. Pick the candidate with the highest adjusted score.
    4. Append it to selected (with the penalty noted in its explanation).
    5. Repeat until k songs are selected or the pool is exhausted.
    """
    seen_artists: Dict[str, int] = {}
    seen_genres:  Dict[str, int] = {}
    remaining = list(scored)   # shallow copy so we can pop without mutating caller's list
    selected:  List[Tuple[Dict, float, str]] = []

    while len(selected) < k and remaining:
        best_idx  = 0
        best_adj  = float("-inf")
        best_pen  = 0.0

        for i, (song, base_score, _explanation) in enumerate(remaining):
            artist  = song.get("artist", "")
            genre   = song.get("genre",  "")
            penalty = (seen_artists.get(artist, 0) * diversity.artist_penalty
                       + seen_genres.get(genre,   0) * diversity.genre_penalty)
            adj = base_score - penalty
            if adj > best_adj:
                best_adj  = adj
                best_idx  = i
                best_pen  = penalty

        song, base_score, explanation = remaining.pop(best_idx)
        if best_pen > 0:
            explanation = explanation + f"; diversity penalty (-{best_pen:.2f})"

        selected.append((song, round(best_adj, 4), explanation))

        artist = song.get("artist", "")
        genre  = song.get("genre",  "")
        seen_artists[artist] = seen_artists.get(artist, 0) + 1
        seen_genres[genre]   = seen_genres.get(genre,   0) + 1

    return selected


@dataclass
class UserProfile:
    """A user's stated taste preferences used to score and rank songs."""
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    mood_tags: str = ""         # pipe-separated detail tags, e.g. "cozy|calm"
    prefers_popular: bool = True
    target_decade: int = 2020

# ---------------------------------------------------------------------------
# ALGORITHM RECIPE
# ---------------------------------------------------------------------------
# Maximum possible score: 8.25
#
#   +1.00  genre match      — exact string match on favorite_genre
#   +1.50  mood match       — exact string match on favorite_mood
#   +2.00  energy fit       — 2.0 * (1 - |song.energy - target_energy|)
#   +0.75  valence fit      — 0.75 * (1 - |song.valence - target_valence|)
#   +0.50  acousticness fit — song.acousticness if likes_acoustic
#                             else (1 - song.acousticness)
#   +1.00  mood tag bonus   — +0.50 per matching pipe-separated mood_tag
#                             (up to 2 tags, so max +1.00)
#   +0.75  popularity fit   — 0.75 * (song.popularity / 100) if prefers_popular
#                             else 0.75 * (1 - song.popularity / 100)
#   +0.75  decade fit       — 0.75 * (1 - |song.release_decade - target_decade| / 40)
#                             clamped to 0; max gap rewarded = 40 years (one step)
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


def score_song(
    user_prefs: Dict,
    song: Dict,
    weights: Optional[ScoringWeights] = None,
) -> Tuple[float, List[str]]:
    """Return (total_score, reasons) using the given ScoringWeights strategy.

    Defaults to the 'balanced' mode when weights is None.
    """
    w = weights if weights is not None else _DEFAULT_MODE
    score = 0.0
    reasons = []

    # --- Genre match ---
    if song.get("genre") == user_prefs.get("favorite_genre"):
        score += w.genre
        reasons.append(f"genre match (+{w.genre:.2f})")

    # --- Mood match ---
    if song.get("mood") == user_prefs.get("favorite_mood"):
        score += w.mood
        reasons.append(f"mood match (+{w.mood:.2f})")

    # --- Energy proximity: 0 – w.energy ---
    target_energy = user_prefs.get("target_energy", 0.5)
    energy_score = round(w.energy * (1.0 - abs(song["energy"] - target_energy)), 4)
    score += energy_score
    reasons.append(f"energy proximity (+{energy_score:.2f})")

    # --- Valence proximity: 0 – w.valence ---
    # Use explicit target_valence if provided, otherwise derive from mood
    target_valence = user_prefs.get(
        "target_valence",
        _MOOD_VALENCE.get(user_prefs.get("favorite_mood", ""), 0.5)
    )
    valence_score = round(w.valence * (1.0 - abs(song["valence"] - target_valence)), 4)
    score += valence_score
    reasons.append(f"valence proximity (+{valence_score:.2f})")

    # --- Acousticness fit: 0 – w.acousticness ---
    likes_acoustic = user_prefs.get("likes_acoustic", False)
    raw_acoustic = song["acousticness"] if likes_acoustic else (1.0 - song["acousticness"])
    acoustic_score = round(w.acousticness * raw_acoustic, 4)
    score += acoustic_score
    reasons.append(f"acousticness fit (+{acoustic_score:.2f})")

    # --- Mood tag bonus: up to w.tag_per_hit * 2 ---
    # +tag_per_hit for each matching pipe-separated tag, capped at 2 hits.
    user_mood_tags = [t.strip() for t in user_prefs.get("mood_tags", "").split("|") if t.strip()]
    song_mood_tags = [t.strip() for t in str(song.get("mood_tags", "")).split("|") if t.strip()]
    tag_hits = min(sum(1 for t in user_mood_tags if t in song_mood_tags), 2)
    tag_score = round(w.tag_per_hit * tag_hits, 4)
    score += tag_score
    if tag_score > 0:
        reasons.append(f"mood tag match x{tag_hits} (+{tag_score:.2f})")

    # --- Popularity fit: 0 – w.popularity ---
    prefers_popular = user_prefs.get("prefers_popular", True)
    pop_norm = song.get("popularity", 50) / 100.0
    raw_pop = pop_norm if prefers_popular else (1.0 - pop_norm)
    pop_score = round(w.popularity * raw_pop, 4)
    score += pop_score
    reasons.append(f"popularity fit (+{pop_score:.2f})")

    # --- Decade fit: 0 – w.decade ---
    target_decade = user_prefs.get("target_decade", 2020)
    decade_gap = abs(song.get("release_decade", 2020) - target_decade)
    decade_score = round(w.decade * max(0.0, 1.0 - decade_gap / 40), 4)
    score += decade_score
    reasons.append(f"decade fit (+{decade_score:.2f})")

    return round(score, 4), reasons


def _score_song(
    song: Dict,
    user_prefs: Dict,
    weights: Optional[ScoringWeights] = None,
) -> Tuple[float, str]:
    """Internal helper: returns (score, explanation_string) for pipeline use."""
    total, reasons = score_song(user_prefs, song, weights)
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
            "mood_tags":       user.mood_tags,
            "prefers_popular": user.prefers_popular,
            "target_decade":   user.target_decade,
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
            "mood_tags":       user.mood_tags,
            "prefers_popular": user.prefers_popular,
            "target_decade":   user.target_decade,
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
            row["popularity"]      = int(row["popularity"])
            row["release_decade"]  = int(row["release_decade"])
            # mood_tags stays as a string; callers split on "|"
            songs.append(row)
    return songs


def recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    weights:   Optional[ScoringWeights]  = None,
    diversity: Optional[DiversityConfig] = None,
) -> List[Tuple[Dict, float, str]]:
    """Score every song and return the top-k as (song, score, explanation) tuples.

    If diversity is provided, a greedy re-ranking pass applies artist/genre
    penalties so the final list is more varied.  Without it, songs are simply
    sorted by raw score descending.
    """
    # Step 1: score every song
    scored = []
    for song in songs:
        total, reasons = score_song(user_prefs, song, weights)
        scored.append((song, total, "; ".join(reasons)))

    # Step 2: rank highest score first
    ranked = sorted(scored, key=lambda item: item[1], reverse=True)

    # Step 3: optionally apply diversity re-ranking, then slice
    if diversity is not None:
        return _greedy_diverse_select(ranked, k, diversity)
    return ranked[:k]
