# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

Give your model a short, descriptive name.  
Example: **VibeFinder 1.0**  

---

## 2. Intended Use  

Describe what your recommender is designed to do and who it is for. 

Prompts:  

- What kind of recommendations does it generate  
- What assumptions does it make about the user  
- Is this for real users or classroom exploration  

---

## 3. How the Model Works  

Explain your scoring approach in simple language.  

Prompts:  

- What features of each song are used (genre, energy, mood, etc.)  
- What user preferences are considered  
- How does the model turn those into a score  
- What changes did you make from the starter logic  

Avoid code here. Pretend you are explaining the idea to a friend who does not program.

---

## 4. Data  

Describe the dataset the model uses.  

Prompts:  

- How many songs are in the catalog  
- What genres or moods are represented  
- Did you add or remove data  
- Are there parts of musical taste missing in the dataset  

---

## 5. Strengths  

Where does your system seem to work well  

Prompts:  

- User types for which it gives reasonable results  
- Any patterns you think your scoring captures correctly  
- Cases where the recommendations matched your intuition  

---

## 6. Limitations and Bias

Where the system struggles or behaves unfairly.

Prompts:

- Features it does not consider
- Genres or moods that are underrepresented
- Cases where the system overfits to one preference
- Ways the scoring might unintentionally favor some users

**Identified weakness — medium-energy filter bubble:**
The 18-song catalog has a bimodal energy distribution: nine songs cluster between 0.28–0.44 and nine between 0.72–0.97, with only one song (*Slow Burn*, 0.55) in the middle range. Because energy proximity is now weighted at 2.0×, a user whose target energy sits around 0.50–0.65 will never receive a strong recommendation — every song in the catalog is at least 0.15 energy units away, costing a minimum of 0.30 points before any other factor is considered. This creates an invisible "medium-energy penalty" where moderate listeners consistently see top scores in the 3.0–4.0 range while high- or low-energy users routinely score 5.0+, making the system appear less confident for an entire class of users through no fault of their preferences. The problem is compounded by the weight-shift experiment: doubling the energy multiplier amplified a pre-existing data gap into a meaningful scoring disparity. A fairer system would either normalize scores against the best available match in the catalog or ensure the song catalog covers the full energy spectrum before assigning high weight to that feature.

---

## 7. Evaluation

How you checked whether the recommender behaved as expected.

Prompts:

- Which user profiles you tested
- What you looked for in the recommendations
- What surprised you
- Any simple tests or comparisons you ran

No need for numeric metrics unless you created some.

**Testing notes:**

Six profiles were tested: three straightforward listener types (High-Energy Pop, Chill Lofi, Deep Intense Rock) and three deliberately tricky ones designed to stress-test the system (High-Energy Sad, Unknown Genre, and Max Energy + Max Acoustic).

The straightforward profiles mostly behaved as expected — a lofi fan got lofi songs at the top, and a rock fan got a rock song at #1. That was reassuring. What became interesting was everything ranked #3 and below, where the system's priorities started to show.

**The "Gym Hero" problem — explained simply:**

Imagine you tell a music assistant: "I love happy pop songs." It returns your favorites, but also sneaks in a gym pump-up track called *Gym Hero*. Why? Because *Gym Hero* is a pop song and its energy level (0.93) is extremely close to yours (0.90) — so on two out of five scoring criteria it scores almost perfectly. The fact that it's tagged "intense" rather than "happy" only costs it 1.5 points in mood, which the strong energy match partially compensates for. After the weight-shift experiment doubled the value of energy matching, this effect got stronger: a song that *feels* wrong can still rank in the top 3 simply because its tempo and loudness happen to match yours on paper.

**What surprised us:**

The most unexpected result came from the High-Energy Sad profile — a user who wants high-energy music but sad lyrics (think angry driving playlist after a breakup). The system surfaced a metal song called *Shatter the Crown* at #1, not because it matched the "sad" mood (it's tagged "angry"), but because its energy of 0.97 was the closest in the entire catalog to the user's target of 0.90. A human curator would immediately flag this as wrong; the system saw it as a near-perfect energy fit and promoted it anyway. This revealed that the system has no understanding of *why* someone might want sad music — it treats mood as just another checkbox rather than the emotional core of the request.

The Deep Intense Rock profile showed a related issue: by positions #3–5, the recommendations had drifted completely away from "rock" into electronic and synthwave territory, purely because those songs happened to sit closer to the target energy. The system was technically doing its job, but a rock fan handed an electronic playlist would not feel heard.

---

## 8. Future Work  

Ideas for how you would improve the model next.  

Prompts:  

- Additional features or preferences  
- Better ways to explain recommendations  
- Improving diversity among the top results  
- Handling more complex user tastes  

---

## 9. Personal Reflection  

A few sentences about your experience.  

Prompts:  

- What you learned about recommender systems  
- Something unexpected or interesting you discovered  
- How this changed the way you think about music recommendation apps  
