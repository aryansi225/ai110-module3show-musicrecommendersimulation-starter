# Model Card: Music Recommender Simulation

---

## 1. Model Name

**VibeFinder 1.0**

---

## 2. Goal / Task

VibeFinder suggests songs from a small catalog that best match a listener's taste profile.

It tries to answer one question: *given what you told us about your favorite genre, mood, and energy level, which songs in the catalog are the closest fit?*

This is a classroom simulation. It is not connected to a real streaming service or live data.

---

## 3. Algorithm Summary

Every song gets a score out of 5.75. Higher score = better match. Here is how the points break down:

- **Genre match (+1.0):** Does the song's genre label match yours exactly? If yes, add 1 point.
- **Mood match (+1.5):** Does the song's mood tag match yours exactly? If yes, add 1.5 points.
- **Energy fit (up to +2.0):** How close is the song's energy level to your target? A perfect match adds 2 points. A big gap adds almost nothing.
- **Valence fit (up to +0.75):** Valence is roughly "how positive the song sounds." Songs closer to your expected positivity level score higher.
- **Acousticness fit (up to +0.50):** If you like acoustic music, songs with high acousticness score better. If you prefer produced/electric sound, low-acousticness songs score better.

The songs are then ranked from highest to lowest score. The top 5 are your recommendations.

**One change we made:** We doubled the weight of energy (from 1.0× to 2.0×) and halved the weight of genre (from +2.0 to +1.0). This was an experiment to see if "how a song feels" matters more than what genre bin it belongs to.

---

## 4. Data

- **Catalog size:** 18 songs.
- **Features per song:** title, artist, genre, mood, energy (0–1), tempo in BPM, valence (0–1), danceability (0–1), acousticness (0–1).
- **Genres represented:** pop, lofi, rock, ambient, jazz, synthwave, indie pop, hip-hop, classical, metal, folk, r&b, electronic, country, blues — 15 genres total.
- **Moods represented:** happy, chill, intense, nostalgic, peaceful, focused, moody, relaxed, euphoric, angry, romantic, sad, melancholic — 13 moods total.
- **Key gap:** Most genres and moods appear only once. If your favorite genre is "blues," there is exactly one song in the whole catalog that can earn you a genre bonus.
- **No data was added or removed** from the original dataset.

---

## 5. Strengths

- Works well for listeners with clear, extreme preferences — someone who wants high-energy lofi or low-energy chill will get consistent, sensible results at #1 and #2.
- The acousticness dimension is surprisingly effective. It quietly separates "unplugged/organic" songs from "produced/electronic" ones without the user having to explain why.
- Energy proximity as the highest-weighted feature means the top result almost always *sounds* right to a listener, even when the genre label does not match perfectly.
- The explanation system (the bullet points under each recommendation) makes it easy to see *why* a song ranked where it did, which helps catch mistakes quickly.

---

## 6. Limitations and Bias

**Medium-energy filter bubble:**
The 18-song catalog has a bimodal energy distribution: nine songs cluster between 0.28–0.44 and nine between 0.72–0.97, with only one song (*Slow Burn*, 0.55) in the middle range. Because energy proximity is weighted at 2.0×, a user whose target energy sits around 0.50–0.65 will never receive a strong recommendation — every song in the catalog is at least 0.15 energy units away, costing a minimum of 0.30 points before any other factor is considered. This creates an invisible "medium-energy penalty" where moderate listeners consistently see top scores in the 3.0–4.0 range while high- or low-energy users routinely score 5.0+, making the system appear less confident for an entire class of users through no fault of their preferences. The problem is compounded by the weight-shift experiment: doubling the energy multiplier amplified a pre-existing data gap into a meaningful scoring disparity. A fairer system would either normalize scores against the best available match in the catalog or ensure the song catalog covers the full energy spectrum before assigning high weight to that feature.

**Other known biases:**
- Mood is treated as a binary checkbox. "Sad" and "melancholic" are treated as completely unrelated, even though a human listener would accept both.
- Genre matching is also binary. "Indie pop" and "pop" score zero for a pop fan — exact string match only.
- 13 of 15 genres have only one representative song. If your genre is rare in the catalog, you lose the genre bonus almost every time.

---

## 7. Evaluation

Six profiles were tested: three straightforward listener types (High-Energy Pop, Chill Lofi, Deep Intense Rock) and three deliberately tricky ones designed to stress-test the system (High-Energy Sad, Unknown Genre, and Max Energy + Max Acoustic).

The straightforward profiles mostly behaved as expected — a lofi fan got lofi songs at the top, and a rock fan got a rock song at #1. What became interesting was everything ranked #3 and below, where the system's priorities started to show.

**The "Gym Hero" problem — explained simply:**

Imagine you tell a music assistant: "I love happy pop songs." It returns your favorites, but also sneaks in a gym pump-up track called *Gym Hero*. Why? Because *Gym Hero* is a pop song and its energy level (0.93) is extremely close to yours (0.90) — so on two out of five scoring criteria it scores almost perfectly. The fact that it's tagged "intense" rather than "happy" only costs it 1.5 points in mood, which the strong energy match partially compensates for. After the weight-shift experiment doubled the value of energy matching, this effect got stronger: a song that *feels* wrong can still rank in the top 3 simply because its tempo and loudness happen to match yours on paper.

**What surprised us:**

The most unexpected result came from the High-Energy Sad profile — a user who wants high-energy music but sad lyrics (think angry driving playlist after a breakup). The system surfaced a metal song called *Shatter the Crown* at #1, not because it matched the "sad" mood (it's tagged "angry"), but because its energy of 0.97 was the closest in the entire catalog to the user's target of 0.90. A human curator would immediately flag this as wrong; the system saw it as a near-perfect energy fit and promoted it anyway. This revealed that the system has no understanding of *why* someone might want sad music — it treats mood as just another checkbox rather than the emotional core of the request.

The Deep Intense Rock profile showed a related issue: by positions #3–5, the recommendations had drifted completely away from "rock" into electronic and synthwave territory, purely because those songs happened to sit closer to the target energy. The system was technically doing its job, but a rock fan handed an electronic playlist would not feel heard.

**Experiment run:** We also ran a weight-shift test — halving the genre bonus and doubling the energy weight — to see how sensitive the rankings are to scoring changes. Top results barely moved; lower-ranked results shuffled noticeably. That told us the #1 pick is robust, but positions #3–5 are fragile.

---

## 8. Intended Use and Non-Intended Use

**Intended use:**
- A classroom project for learning how scoring-based recommender systems work.
- A starting point for experimenting with weights and feature design.
- A tool for understanding how small math decisions affect what users see.

**Not intended for:**
- Real music recommendations to actual users.
- Any production or commercial use.
- Drawing conclusions about what makes music "objectively" good or bad.
- Representing the diversity of real-world listening habits — 18 songs is far too small for that.

---

## 9. Ideas for Improvement

1. **Soft matching for mood and genre.** Instead of awarding points only for exact matches, group similar moods together (e.g., "sad" and "melancholic" share partial credit) and treat closely related genres the same way. This would reduce the harsh binary penalty for near-misses.

2. **Normalize scores against the catalog.** Instead of scoring out of a fixed 5.75, show how a song compares to the *best available match* in the current catalog. A user should know if their #1 result is genuinely a good fit or just the least-bad option in a sparse dataset.

3. **Enforce result diversity.** Cap the number of songs from the same genre or artist in the top 5. Right now, a lofi fan can get three lofi songs in a row, which is repetitive. A simple rule — "no more than two songs from the same genre" — would make playlists feel more curated.

---

## 10. Personal Reflection

**Biggest learning moment:**
The weight-shift experiment was supposed to be a quick test. Double energy, halve genre — simple enough. But it exposed something that was already broken and hiding in plain sight: a gap in the catalog between energy 0.44 and 0.72 that no scoring formula can paper over. The learning was not about the weights themselves. It was that *changing a number in the formula made a data problem visible for the first time*. Before the experiment, the system looked fine. After it, the medium-energy users clearly stood out as getting worse results. That taught me to treat weight changes as diagnostic tools, not just tuning knobs.

**How AI tools helped — and when to double-check:**
The AI agent was useful for applying the weight-shift edit precisely across the file and verifying the max-score math stayed at 5.75. That kind of mechanical consistency check — "did every reference to the old number get updated?" — is exactly where it saves time and catches copy-paste mistakes. Where I needed to slow down and verify was in the *interpretation* of results. The agent can confirm that `2.0 * (1 - |gap|)` is mathematically correct, but it cannot tell you whether a metal song ranked above a blues song for a "sad" user is a real problem or an acceptable tradeoff. That judgment required reading the actual output and thinking about what a real listener would feel. AI handles the "did I write it right" question well. The "does this make sense for a person" question still needs a human pass.

**What surprised me about simple algorithms feeling like recommendations:**
The scoring formula is five arithmetic operations. There is no machine learning, no user history, no collaborative filtering. And yet, for the first two results on most profiles, it genuinely feels like something that *knows* your taste. That surprised me. The reason, I think, is that energy and valence together approximate the emotional shape of a song well enough that matching them numerically produces something that *sounds* right even when the genre label is off. The system is not understanding music — it is just finding the closest point in a five-dimensional space — but to a user reading the output, those two things are indistinguishable at position #1. The illusion breaks down at #3 and below, which is where the algorithm's limitations start showing. Real streaming apps probably face the same cliff: the first result feels magical, and everything after it is where the engineering actually matters.

**What I would try next:**
First, I would add soft mood matching — a lookup table that gives partial credit when moods are emotionally adjacent (e.g., "sad" and "melancholic" sharing 0.75 of the full bonus). That one change would fix the most glaring failures in the edge-case profiles. Second, I would grow the catalog to at least 100 songs with intentional coverage across the full energy range, so the medium-energy gap disappears. Third, I would try replacing the fixed max-score bar with a percentile rank — instead of "4.2 out of 5.75," show "better than 80% of songs in this catalog for your profile." That framing is honest about catalog size and gives users a more meaningful signal than a raw number.
