# arxiv-sanity-lite v2.0: The Next Evolution

## A Vision Document

*Simulating 1,000 build iterations, 1,000,000 users, 12 programmers watching over shoulders*

---

## Part I: What We Learned (Simulated User Insights)

### The Million User Simulation

After simulating a million dedicated users across diverse research contexts, clear patterns emerged:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    USER BEHAVIOR HEAT MAP (Simulated)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Action                          Frequency    Frustration    Value          │
│  ────────────────────────────────────────────────────────────────────       │
│  Browse recent papers            ████████████    Low         Medium         │
│  Search by keyword               ██████████      Medium      High           │
│  Tag papers                      ████            High        Very High      │
│  Get recommendations             ██████          Medium      Very High      │
│  Find similar papers             ████████        Low         High           │
│  ABANDON mid-session             ██████████      -           -              │
│  Share paper with colleague      ░░░░░░░░░░      Very High   Very High      │
│  Read paper on site              ░░░░░░░░░░      Very High   High           │
│  Track citation network          ░░░░░░░░░░      Very High   Very High      │
│  Collaborate on reading list     ░░░░░░░░░░      Very High   Very High      │
│                                                                             │
│  ████ = Currently Supported    ░░░░ = Desperately Wanted                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### The 1,000 Builds: Patterns That Emerged

Through iterative development, we discovered **five fundamental truths**:

#### Truth 1: The Tagging Paradox
> Users who tag 50+ papers get 10x better recommendations, but 94% of users never tag more than 5 papers.

**Why it happens**: The value is delayed. Users don't see immediate reward for tagging.

**What builds 400-600 discovered**: Micro-rewards, instant similar-paper suggestions on tag, gamification all helped but weren't enough.

**What build 847 finally cracked**: **Implicit tagging** - reading time, scroll depth, tab-open duration, return visits all count as soft positive signals.

#### Truth 2: The Cold Start Problem
> New users see the same "recent papers" view as experts. They leave within 30 seconds.

**What builds 200-400 tried**: Onboarding wizards, category selection, sample tags.

**What build 512 discovered**: Show them papers that *people like them* found valuable. But we don't know who they are yet.

**What build 723 cracked**: **The 3-Paper Bootstrap** - Ask users to thumbs-up just 3 papers from a diverse sample. Train instant micro-model. Show personalized results immediately.

#### Truth 3: The Context Collapse
> The same user needs different recommendations at different times.

Monday morning: "What's new in transformers?"
Thursday afternoon: "Deep dive into a specific technique"
Paper deadline: "Find everything related to my current work"
Exploration mode: "Show me something surprising"

**What build 891 introduced**: **Research Modes** - switchable contexts with their own tag sets and recommendation tuning.

#### Truth 4: The Social Blind Spot
> 73% of paper discoveries come from colleagues, Twitter, or Slack - not from recommendation systems.

**What builds 600-800 explored**: Social features, following researchers, public reading lists.

**What build 934 synthesized**: **The Invisible College** - see what researchers in your citation network are reading, without explicit social features.

#### Truth 5: The Understanding Gap
> Users want to understand papers, not just find them.

Reading an abstract isn't enough. Users need:
- Key contributions in plain language
- How it relates to papers they know
- What they need to understand first
- Whether it's worth their time

**What build 978 began**: **The Comprehension Layer** - AI-powered paper summarization, prerequisite mapping, contribution extraction.

---

## Part II: The Architecture That Emerged

### From 1,000 Iterations: The Converged Design

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ARXIV-SANITY v2.0 ARCHITECTURE                          │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │   USER LAYER    │
                              └────────┬────────┘
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        │                              │                              │
        ▼                              ▼                              ▼
┌───────────────┐            ┌───────────────┐            ┌───────────────┐
│   WEB APP     │            │  MOBILE APP   │            │  API CLIENTS  │
│   (React)     │            │  (React Nat.) │            │  (REST/GQL)   │
└───────┬───────┘            └───────┬───────┘            └───────┬───────┘
        │                            │                            │
        └──────────────────────────────────────────────────────────┘
                                       │
                              ┌────────▼────────┐
                              │   API GATEWAY   │
                              │   (Kong/Envoy)  │
                              └────────┬────────┘
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        │                              │                              │
        ▼                              ▼                              ▼
┌───────────────┐            ┌───────────────┐            ┌───────────────┐
│    CORE       │            │  DISCOVERY    │            │  SOCIAL       │
│   SERVICE     │            │   SERVICE     │            │   SERVICE     │
│               │            │               │            │               │
│ • Auth        │            │ • Search      │            │ • Following   │
│ • Users       │            │ • Recommend   │            │ • Sharing     │
│ • Tags        │            │ • Similar     │            │ • Activity    │
│ • Prefs       │            │ • Trending    │            │ • Collab      │
└───────┬───────┘            └───────┬───────┘            └───────┬───────┘
        │                            │                            │
        └──────────────────────────────────────────────────────────┘
                                       │
                              ┌────────▼────────┐
                              │   EVENT BUS     │
                              │   (Kafka)       │
                              └────────┬────────┘
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        │                              │                              │
        ▼                              ▼                              ▼
┌───────────────┐            ┌───────────────┐            ┌───────────────┐
│   INGESTION   │            │     ML        │            │  UNDERSTAND   │
│   PIPELINE    │            │   PIPELINE    │            │   PIPELINE    │
│               │            │               │            │               │
│ • arXiv Fetch │            │ • Embeddings  │            │ • Summarize   │
│ • PDF Parse   │            │ • User Models │            │ • Extract     │
│ • Metadata    │            │ • Clustering  │            │ • Relate      │
│ • Citations   │            │ • Ranking     │            │ • Prereqs     │
└───────┬───────┘            └───────┬───────┘            └───────┬───────┘
        │                            │                            │
        └──────────────────────────────────────────────────────────┘
                                       │
                              ┌────────▼────────┐
                              │   DATA LAYER    │
                              └────────┬────────┘
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        │                              │                              │
        ▼                              ▼                              ▼
┌───────────────┐            ┌───────────────┐            ┌───────────────┐
│  PostgreSQL   │            │  Pinecone/    │            │    Redis      │
│  (Metadata)   │            │  Qdrant       │            │   (Cache)     │
│               │            │  (Vectors)    │            │               │
└───────────────┘            └───────────────┘            └───────────────┘
        │                              │                              │
        ▼                              ▼                              ▼
┌───────────────┐            ┌───────────────┐            ┌───────────────┐
│  ClickHouse   │            │     S3        │            │ Elasticsearch │
│  (Analytics)  │            │   (PDFs)      │            │  (Search)     │
└───────────────┘            └───────────────┘            └───────────────┘
```

### The New Data Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EVOLVED DATA MODEL                                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                                 PAPER                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  id              │ arxiv_id (2312.12345)                                    │
│  version         │ latest version number                                    │
│  ─────────────────────────────────────────────────────────────────────────  │
│  ORIGINAL DATA                                                              │
│  title           │ original title                                           │
│  abstract        │ original abstract                                        │
│  authors         │ [Author] with affiliations, ORCIDs                       │
│  categories      │ [cs.CV, cs.LG, ...]                                      │
│  submitted_at    │ timestamp                                                │
│  updated_at      │ timestamp                                                │
│  ─────────────────────────────────────────────────────────────────────────  │
│  ENRICHED DATA (The Understanding Layer)                                    │
│  summary         │ AI-generated 2-sentence summary                          │
│  contributions   │ [bullet points of key contributions]                     │
│  methods         │ [techniques/methods used]                                │
│  datasets        │ [datasets mentioned]                                     │
│  prerequisites   │ [Paper IDs you should read first]                        │
│  reading_time    │ estimated minutes                                        │
│  difficulty      │ 1-5 scale                                                │
│  ─────────────────────────────────────────────────────────────────────────  │
│  VECTOR EMBEDDINGS                                                          │
│  embedding_title │ float[768] - title embedding                             │
│  embedding_abs   │ float[768] - abstract embedding                          │
│  embedding_full  │ float[768] - full paper embedding                        │
│  ─────────────────────────────────────────────────────────────────────────  │
│  GRAPH DATA                                                                 │
│  citations       │ [Paper IDs this paper cites]                             │
│  cited_by        │ [Paper IDs citing this paper]                            │
│  related         │ [Paper IDs - computed similarity]                        │
│  ─────────────────────────────────────────────────────────────────────────  │
│  AGGREGATE SIGNALS                                                          │
│  view_count      │ total views                                              │
│  save_count      │ times saved to libraries                                 │
│  share_count     │ times shared                                             │
│  trending_score  │ velocity of engagement                                   │
│  quality_score   │ ML-predicted quality                                     │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                                 USER                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  id              │ unique identifier                                        │
│  ─────────────────────────────────────────────────────────────────────────  │
│  IDENTITY                                                                   │
│  email           │ for auth and notifications                               │
│  auth_provider   │ Google, GitHub, ORCID, institutional                     │
│  orcid           │ optional ORCID for researcher identity                   │
│  ─────────────────────────────────────────────────────────────────────────  │
│  RESEARCH PROFILE                                                           │
│  interests       │ [auto-learned topic vectors]                             │
│  expertise_level │ {topic: level} - inferred from behavior                  │
│  active_projects │ [ResearchMode IDs]                                       │
│  ─────────────────────────────────────────────────────────────────────────  │
│  PREFERENCES                                                                │
│  notification_prefs │ {email: weekly, push: realtime, ...}                  │
│  display_prefs   │ {density: compact, theme: dark, ...}                     │
│  ─────────────────────────────────────────────────────────────────────────  │
│  EMBEDDINGS                                                                 │
│  user_embedding  │ float[768] - learned user preference vector              │
│  context_embeddings │ {mode_id: float[768]} - per research mode             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                            RESEARCH MODE                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  id              │ unique identifier                                        │
│  user_id         │ owner                                                    │
│  name            │ "Transformer Architectures" / "PhD Thesis" / ...         │
│  ─────────────────────────────────────────────────────────────────────────  │
│  CONFIGURATION                                                              │
│  categories      │ [cs.CL, cs.LG] - filter to these                         │
│  keywords        │ [attention, transformer] - boost these                   │
│  time_window     │ "last_month" / "last_year" / "all_time"                  │
│  novelty_weight  │ 0.0-1.0 (0=familiar, 1=surprising)                       │
│  ─────────────────────────────────────────────────────────────────────────  │
│  LEARNED STATE                                                              │
│  mode_embedding  │ float[768] - learned from interactions in this mode      │
│  positive_papers │ [Paper IDs explicitly saved]                             │
│  negative_papers │ [Paper IDs explicitly rejected]                          │
│  implicit_signals│ [{paper_id, signal_type, strength, timestamp}]           │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              INTERACTION                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  id              │ unique identifier                                        │
│  user_id         │ who                                                      │
│  paper_id        │ what                                                     │
│  mode_id         │ in which research context                                │
│  timestamp       │ when                                                     │
│  ─────────────────────────────────────────────────────────────────────────  │
│  INTERACTION TYPE                                                           │
│  type            │ view | click | scroll | save | share | cite | ...        │
│  ─────────────────────────────────────────────────────────────────────────  │
│  IMPLICIT SIGNALS                                                           │
│  dwell_time      │ seconds on page                                          │
│  scroll_depth    │ 0.0-1.0 how far scrolled                                 │
│  pdf_opened      │ boolean                                                  │
│  pdf_time        │ seconds in PDF                                           │
│  returned        │ came back to this paper                                  │
│  ─────────────────────────────────────────────────────────────────────────  │
│  EXPLICIT SIGNALS                                                           │
│  saved           │ added to library                                         │
│  tags            │ [tag names applied]                                      │
│  rating          │ optional 1-5                                             │
│  notes           │ optional free text                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Part III: The Features That Won

### From 1,000 Builds: The Survivors

After brutal A/B testing across a million users, these features had the highest impact:

---

### Feature 1: The 3-Paper Bootstrap

**The Problem**: Cold start kills engagement

**The Solution**:
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE 3-PAPER BOOTSTRAP                                │
└─────────────────────────────────────────────────────────────────────────────┘

  New User Arrives
        │
        ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │                                                                     │
  │   "Help us learn your interests in 30 seconds"                      │
  │                                                                     │
  │   ┌─────────────────────────────────────────────────────────────┐  │
  │   │                                                             │  │
  │   │  Here are 9 diverse papers from the last month.             │  │
  │   │  Thumbs-up at least 3 that interest you:                    │  │
  │   │                                                             │  │
  │   │  ┌─────────┐  ┌─────────┐  ┌─────────┐                     │  │
  │   │  │ NLP     │  │ Vision  │  │ RL      │                     │  │
  │   │  │ Paper   │  │ Paper   │  │ Paper   │                     │  │
  │   │  │   👍?   │  │   👍?   │  │   👍?   │                     │  │
  │   │  └─────────┘  └─────────┘  └─────────┘                     │  │
  │   │  ┌─────────┐  ┌─────────┐  ┌─────────┐                     │  │
  │   │  │ Theory  │  │ Accel.  │  │ Accel.  │                     │  │
  │   │  │ Paper   │  │ Paper   │  │ Paper   │                     │  │
  │   │  │   👍?   │  │   👍?   │  │   👍?   │                     │  │
  │   │  └─────────┘  └─────────┘  └─────────┘                     │  │
  │   │  ┌─────────┐  ┌─────────┐  ┌─────────┐                     │  │
  │   │  │ Ethics  │  │ Accel.  │  │ accel.  │                     │  │
  │   │  │ Paper   │  │ Paper   │  │ Paper   │                     │  │
  │   │  │   👍?   │  │   👍?   │  │   👍?   │                     │  │
  │   │  └─────────┘  └─────────┘  └─────────┘                     │  │
  │   │                                                             │  │
  │   │                              [Show My Feed →]               │  │
  │   │                                                             │  │
  │   └─────────────────────────────────────────────────────────────┘  │
  │                                                                     │
  └─────────────────────────────────────────────────────────────────────┘
        │
        │  User selects 3+ papers
        ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │  INSTANT MICRO-MODEL                                                │
  │                                                                     │
  │  1. Average embeddings of selected papers                           │
  │  2. Use as initial user_embedding                                   │
  │  3. Nearest-neighbor search for recommendations                     │
  │  4. Time: <100ms                                                    │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ▼
  Personalized feed from first second!
```

**Impact**: +340% first-session engagement, +180% Day-7 retention

---

### Feature 2: Research Modes

**The Problem**: One set of interests doesn't fit all contexts

**The Solution**:
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            RESEARCH MODES                                    │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────────┐
  │  Header Bar                                                             │
  │  ┌──────────────────────────────────────────────────────────────────┐  │
  │  │  arxiv-sanity    [🔬 PhD Thesis ▼]    Search...    [Profile]     │  │
  │  └──────────────────────────────────────────────────────────────────┘  │
  │                           │                                             │
  │                           ▼                                             │
  │              ┌────────────────────────────┐                             │
  │              │  Your Research Modes       │                             │
  │              │  ────────────────────────  │                             │
  │              │  🔬 PhD Thesis        ✓    │  ← active                   │
  │              │  🧪 Side Project           │                             │
  │              │  📚 Literature Review      │                             │
  │              │  🌟 Explore New Areas      │                             │
  │              │  ────────────────────────  │                             │
  │              │  + Create New Mode         │                             │
  │              └────────────────────────────┘                             │
  │                                                                         │
  └─────────────────────────────────────────────────────────────────────────┘

  Each mode has:
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                                                                         │
  │  Mode: PhD Thesis (Efficient Transformers)                              │
  │  ─────────────────────────────────────────                              │
  │                                                                         │
  │  Categories: cs.CL, cs.LG                                               │
  │  Keywords: efficient, sparse attention, linear complexity              │
  │  Time window: All time                                                  │
  │  Novelty: Low (stick to known territory)                                │
  │                                                                         │
  │  Saved: 47 papers                                                       │
  │  Implicit likes: 230 papers (from reading behavior)                     │
  │                                                                         │
  │  [Recommendations for this mode]                                        │
  │  [Export bibliography]                                                  │
  │  [Share reading list]                                                   │
  │                                                                         │
  └─────────────────────────────────────────────────────────────────────────┘
```

**Impact**: +85% papers saved, +120% recommendation satisfaction

---

### Feature 3: Implicit Signals

**The Problem**: Explicit tagging is too much work

**The Solution**: Learn from behavior without requiring action

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           IMPLICIT SIGNAL WEIGHTS                            │
└─────────────────────────────────────────────────────────────────────────────┘

  Signal                          Weight    Confidence    Decay
  ─────────────────────────────────────────────────────────────────────────
  Explicit save to library        +1.0      High          None
  Explicit thumbs up              +0.9      High          None
  Explicit thumbs down            -1.0      High          None
  ─────────────────────────────────────────────────────────────────────────
  Opened PDF                      +0.4      Medium        7 days
  Read abstract >30s              +0.3      Medium        7 days
  Scrolled to end of abstract     +0.2      Medium        7 days
  Returned to paper               +0.5      High          14 days
  Shared paper                    +0.6      High          30 days
  ─────────────────────────────────────────────────────────────────────────
  Clicked but bounced <5s         -0.2      Low           3 days
  Scrolled past without clicking  -0.1      Low           1 day
  ─────────────────────────────────────────────────────────────────────────

  User embedding update (online learning):

  user_embedding = α * user_embedding + (1-α) * Σ(signal_weight * paper_embedding)

  where α = 0.95 (slow adaptation to new interests)
```

**Impact**: 10x more training signal, +65% recommendation accuracy

---

### Feature 4: The Understanding Layer

**The Problem**: Abstracts are dense, jargon-heavy, time-consuming

**The Solution**: AI-powered paper comprehension

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE UNDERSTANDING LAYER                              │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────────┐
  │                                                                         │
  │  Attention Is All You Need                                              │
  │  Vaswani et al. • NeurIPS 2017 • cs.CL                                  │
  │                                                                         │
  │  ┌───────────────────────────────────────────────────────────────────┐ │
  │  │ 📝 TL;DR (AI Generated)                                           │ │
  │  │                                                                   │ │
  │  │ Introduces the Transformer, a neural network architecture that    │ │
  │  │ relies entirely on self-attention mechanisms, eliminating the     │ │
  │  │ need for recurrence or convolution in sequence modeling tasks.    │ │
  │  └───────────────────────────────────────────────────────────────────┘ │
  │                                                                         │
  │  ┌───────────────────────────────────────────────────────────────────┐ │
  │  │ 🎯 Key Contributions                                              │ │
  │  │                                                                   │ │
  │  │ • Self-attention mechanism for sequence modeling                  │ │
  │  │ • Multi-head attention for multiple representation subspaces      │ │
  │  │ • Positional encoding for sequence order information              │ │
  │  │ • Achieves SOTA on WMT translation with less training time        │ │
  │  └───────────────────────────────────────────────────────────────────┘ │
  │                                                                         │
  │  ┌───────────────────────────────────────────────────────────────────┐ │
  │  │ 📚 Prerequisites (papers you should read first)                   │ │
  │  │                                                                   │ │
  │  │ • Sequence to Sequence Learning (Sutskever 2014) - [You've read]  │ │
  │  │ • Neural Machine Translation (Bahdanau 2015) - [Recommended]      │ │
  │  │ • Layer Normalization (Ba 2016) - [Optional]                      │ │
  │  └───────────────────────────────────────────────────────────────────┘ │
  │                                                                         │
  │  ┌───────────────────────────────────────────────────────────────────┐ │
  │  │ 🔗 Reading Path                                                   │ │
  │  │                                                                   │ │
  │  │ This paper → BERT → GPT → GPT-2 → T5 → GPT-3 → ...               │ │
  │  │              ↓                                                    │ │
  │  │         Vision Transformer → CLIP → DALL-E → ...                 │ │
  │  └───────────────────────────────────────────────────────────────────┘ │
  │                                                                         │
  │  ⏱️ ~45 min read  •  📊 Difficulty: Intermediate  •  📈 Citations: 90K+ │
  │                                                                         │
  │  [Read Abstract] [View PDF] [Save] [Share] [Similar Papers]             │
  │                                                                         │
  └─────────────────────────────────────────────────────────────────────────┘
```

**Impact**: +200% paper evaluation speed, +45% successful paper selection

---

### Feature 5: The Invisible College

**The Problem**: Social features feel like noise, but social signals are valuable

**The Solution**: Surface social information passively, without explicit social graph

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          THE INVISIBLE COLLEGE                               │
└─────────────────────────────────────────────────────────────────────────────┘

  Instead of:                      We do:
  ─────────────────────────────────────────────────────────────────────────
  "Follow researchers"       →    Infer your network from citations
  "See what friends like"    →    "Researchers in your area are reading..."
  "Public reading lists"     →    Anonymous aggregate signals
  "Social feed"              →    Subtle social proof indicators

  ┌─────────────────────────────────────────────────────────────────────────┐
  │                                                                         │
  │  Paper Card                                                             │
  │  ──────────────────────────────────────────────────────────────────    │
  │                                                                         │
  │  [Title of Paper]                                                       │
  │  Authors • Date • Categories                                            │
  │                                                                         │
  │  Abstract preview...                                                    │
  │                                                                         │
  │  ┌─────────────────────────────────────────────────────────────────┐   │
  │  │  📈 Trending in your area                                       │   │
  │  │  👥 47 researchers similar to you saved this                    │   │
  │  │  🔥 3 authors you cite are discussing this on Twitter           │   │
  │  └─────────────────────────────────────────────────────────────────┘   │
  │                                                                         │
  └─────────────────────────────────────────────────────────────────────────┘

  How "researchers similar to you" works:

  1. Extract user's citation network from their saved/tagged papers
  2. Find other users with overlapping citation networks
  3. Weight by network similarity
  4. Show aggregate behavior: "N similar researchers saved this"

  No explicit following, no social anxiety, just useful signals.
```

**Impact**: +55% click-through on papers with social signals, +30% quality of discoveries

---

### Feature 6: Smart Notifications

**The Problem**: Email digests are ignored or overwhelming

**The Solution**: Intelligent, multi-channel, contextual notifications

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SMART NOTIFICATIONS                                 │
└─────────────────────────────────────────────────────────────────────────────┘

  Notification Types:
  ─────────────────────────────────────────────────────────────────────────

  1. THE DAILY BRIEF (email, 8am)
     "3 papers highly relevant to your PhD Thesis research mode"
     - Only if papers score >0.9 relevance
     - Max 1 email per day
     - Unsubscribe per mode

  2. THE INSTANT ALERT (push, realtime)
     "A paper citing your work was just published"
     "New paper from [author you follow]"
     - Only for high-signal events
     - Configurable threshold

  3. THE WEEKLY ROUNDUP (email, Sunday)
     "This week in [your areas]: 12 papers, 3 trending, 1 breakthrough"
     - Curated summary with AI
     - Reading time estimate

  4. THE SERENDIPITY NUDGE (push, random)
     "Step outside your bubble: Here's a surprising paper you might like"
     - 1x per week max
     - Papers from adjacent fields
     - Opt-in only

  Notification Intelligence:
  ─────────────────────────────────────────────────────────────────────────

  - Learns optimal send time per user
  - Backs off if user ignores
  - Increases if user engages
  - Never more than 1 push per day
  - Respects "focus time" calendar blocks
```

---

## Part IV: The Technical Deep Dive

### The ML Pipeline That Scaled

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ML PIPELINE ARCHITECTURE                             │
└─────────────────────────────────────────────────────────────────────────────┘

                           ┌─────────────────────┐
                           │   Paper Ingestion   │
                           │   (Continuous)      │
                           └──────────┬──────────┘
                                      │
                ┌─────────────────────┼─────────────────────┐
                │                     │                     │
                ▼                     ▼                     ▼
      ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
      │  Text Embedding │   │  Citation Graph │   │  PDF Processing │
      │  (SPECTER2)     │   │  (Semantic Sch.)│   │  (GROBID+LLM)   │
      └────────┬────────┘   └────────┬────────┘   └────────┬────────┘
               │                     │                     │
               └─────────────────────┼─────────────────────┘
                                     │
                                     ▼
                           ┌─────────────────────┐
                           │   Paper Index       │
                           │   (Qdrant)          │
                           │                     │
                           │   768-dim vectors   │
                           │   + metadata        │
                           │   + graph edges     │
                           └──────────┬──────────┘
                                      │
                ┌─────────────────────┼─────────────────────┐
                │                     │                     │
                ▼                     ▼                     ▼
      ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
      │  User Modeling  │   │  Ranking Model  │   │  Understanding  │
      │  (Online)       │   │  (Two-Tower)    │   │  (LLM Pipeline) │
      └────────┬────────┘   └────────┬────────┘   └────────┬────────┘
               │                     │                     │
               │                     │                     │
               ▼                     ▼                     ▼
      ┌─────────────────────────────────────────────────────────────┐
      │                    SERVING LAYER                             │
      │                                                              │
      │  Request → User Embedding → ANN Search → Rerank → Response  │
      │                                                              │
      │  Latency budget: 100ms p99                                   │
      └─────────────────────────────────────────────────────────────┘


  MODEL DETAILS:
  ═══════════════════════════════════════════════════════════════════════════

  1. Paper Embedding Model: SPECTER2 (AllenAI)
     - Input: Title + Abstract
     - Output: 768-dim vector
     - Fine-tuned on citation prediction
     - Batch inference on new papers

  2. User Embedding Model: Two-Tower Architecture
     ┌─────────────────┐         ┌─────────────────┐
     │   User Tower    │         │   Paper Tower   │
     │                 │         │                 │
     │ - Interaction   │         │ - SPECTER2      │
     │   history       │         │   embedding     │
     │ - Explicit tags │         │ - Metadata      │
     │ - Mode context  │         │ - Social signals│
     │                 │         │                 │
     │ Output: 768-dim │         │ Output: 768-dim │
     └────────┬────────┘         └────────┬────────┘
              │                           │
              └───────────┬───────────────┘
                          │
                          ▼
                   Dot Product Score

  3. Online Learning: User embeddings update in real-time

     On each interaction:
       user_emb = momentum * user_emb + (1-momentum) * interaction_signal

     Where interaction_signal = weighted sum of paper embeddings
     momentum = 0.95 (slow drift) to 0.8 (fast adaptation)

  4. Approximate Nearest Neighbor: Qdrant with HNSW
     - Index: ~500K papers
     - Query time: <10ms
     - Recall@100: 0.95

  5. Reranking: LightGBM model
     Features:
     - Vector similarity score
     - Recency
     - Social signals (saves, shares)
     - User-paper category match
     - Author familiarity
     - Citation network proximity
```

### The Serving Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SERVING ARCHITECTURE                                 │
└─────────────────────────────────────────────────────────────────────────────┘

                              Internet
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   CloudFlare    │
                        │   (CDN + WAF)   │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   Load Balancer │
                        │   (AWS ALB)     │
                        └────────┬────────┘
                                 │
           ┌─────────────────────┼─────────────────────┐
           │                     │                     │
           ▼                     ▼                     ▼
    ┌─────────────┐       ┌─────────────┐       ┌─────────────┐
    │   Web Pod   │       │   Web Pod   │       │   Web Pod   │
    │   (Next.js) │       │   (Next.js) │       │   (Next.js) │
    └──────┬──────┘       └──────┬──────┘       └──────┬──────┘
           │                     │                     │
           └─────────────────────┼─────────────────────┘
                                 │
                        ┌────────▼────────┐
                        │   API Gateway   │
                        │   (Kong)        │
                        └────────┬────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
 ┌─────────────┐          ┌─────────────┐          ┌─────────────┐
 │   Core      │          │  Discovery  │          │  Social     │
 │   Service   │          │  Service    │          │  Service    │
 │   (Go)      │          │  (Python)   │          │  (Go)       │
 └──────┬──────┘          └──────┬──────┘          └──────┬──────┘
        │                        │                        │
        │                        │                        │
        ▼                        ▼                        ▼
 ┌─────────────┐          ┌─────────────┐          ┌─────────────┐
 │  Postgres   │          │   Qdrant    │          │   Redis     │
 │  (Users)    │          │  (Vectors)  │          │  (Cache)    │
 └─────────────┘          └─────────────┘          └─────────────┘


  SCALING TARGETS:
  ═══════════════════════════════════════════════════════════════════════════

  Daily Active Users:     1,000,000
  Peak QPS:               10,000
  Paper Index Size:       2,000,000 papers

  Latency Budgets:
  - Homepage load:        < 200ms p99
  - Search results:       < 300ms p99
  - Recommendations:      < 150ms p99
  - Save/tag action:      < 100ms p99

  Availability Target:    99.9% uptime


  CACHING STRATEGY:
  ═══════════════════════════════════════════════════════════════════════════

  Layer 1: CDN (CloudFlare)
  - Static assets: 30 days
  - Paper metadata pages: 1 hour
  - API responses: 0 (dynamic)

  Layer 2: Application Cache (Redis)
  - Paper objects: 24 hours, LRU eviction
  - User sessions: 7 days
  - Feature flags: 5 minutes
  - Rate limit counters: sliding window

  Layer 3: Computed Results Cache (Redis)
  - "Trending papers": 15 minutes
  - "Papers in category X": 1 hour
  - User recommendations: 30 minutes (invalidate on interaction)

  Layer 4: Database Query Cache (PgBouncer)
  - Prepared statements
  - Connection pooling
```

---

## Part V: The Roadmap

### Phase 1: Foundation (Months 1-3)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 1: FOUNDATION                                                         │
│  "Make the current system production-ready"                                  │
└─────────────────────────────────────────────────────────────────────────────┘

Week 1-2: Infrastructure
├── [ ] Migrate from SQLite to PostgreSQL
├── [ ] Set up Redis for caching
├── [ ] Containerize with Docker
├── [ ] Set up CI/CD pipeline (GitHub Actions)
└── [ ] Deploy to Kubernetes (EKS/GKE)

Week 3-4: Authentication & Security
├── [ ] Implement OAuth2 (Google, GitHub, ORCID)
├── [ ] Add CSRF protection
├── [ ] Implement rate limiting
├── [ ] Add input validation layer
└── [ ] Security audit

Week 5-6: API Modernization
├── [ ] Design REST API v1
├── [ ] Add OpenAPI documentation
├── [ ] Implement API versioning
├── [ ] Add request/response logging
└── [ ] Build API client SDKs (Python, JS)

Week 7-8: Frontend Rebuild
├── [ ] Migrate to Next.js 14
├── [ ] Implement responsive design
├── [ ] Add dark mode
├── [ ] Improve accessibility (WCAG 2.1)
└── [ ] Add PWA support

Week 9-12: ML Pipeline v1
├── [ ] Replace TF-IDF with SPECTER2 embeddings
├── [ ] Set up Qdrant for vector search
├── [ ] Implement basic two-tower model
├── [ ] Add A/B testing infrastructure
└── [ ] Build ML monitoring dashboard
```

### Phase 2: Intelligence (Months 4-6)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 2: INTELLIGENCE                                                       │
│  "Make recommendations actually good"                                        │
└─────────────────────────────────────────────────────────────────────────────┘

Week 13-16: Advanced Recommendations
├── [ ] Implement implicit signal collection
├── [ ] Build online learning pipeline
├── [ ] Add diversity/serendipity controls
├── [ ] Implement Research Modes
└── [ ] Build recommendation explanation UI

Week 17-20: Understanding Layer
├── [ ] Integrate LLM for paper summarization
├── [ ] Build prerequisite extraction pipeline
├── [ ] Generate paper relationships
├── [ ] Create reading path suggestions
└── [ ] Add difficulty estimation

Week 21-24: Search Enhancement
├── [ ] Implement hybrid search (vector + keyword)
├── [ ] Add faceted search
├── [ ] Build query understanding
├── [ ] Add search suggestions
└── [ ] Implement saved searches
```

### Phase 3: Social (Months 7-9)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 3: SOCIAL                                                             │
│  "Leverage the invisible college"                                            │
└─────────────────────────────────────────────────────────────────────────────┘

Week 25-28: Citation Graph
├── [ ] Integrate Semantic Scholar API
├── [ ] Build citation network visualization
├── [ ] Implement "papers citing your saves"
├── [ ] Add author profiles
└── [ ] Create research lineage view

Week 29-32: Social Signals
├── [ ] Implement anonymous aggregate signals
├── [ ] Build "trending in your area"
├── [ ] Add "researchers like you" matching
├── [ ] Create shareable reading lists
└── [ ] Implement collaborative collections

Week 33-36: Notifications
├── [ ] Build notification preference center
├── [ ] Implement smart email digests
├── [ ] Add push notifications
├── [ ] Build notification ML model
└── [ ] Add calendar integration
```

### Phase 4: Scale (Months 10-12)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 4: SCALE                                                              │
│  "Serve a million researchers"                                               │
└─────────────────────────────────────────────────────────────────────────────┘

Week 37-40: Performance
├── [ ] Optimize database queries
├── [ ] Implement edge caching
├── [ ] Add read replicas
├── [ ] Optimize ML inference
└── [ ] Load testing to 10K QPS

Week 41-44: Expansion
├── [ ] Add bioRxiv, medRxiv support
├── [ ] Integrate with Zotero, Mendeley
├── [ ] Build browser extension
├── [ ] Create mobile app (React Native)
└── [ ] Add institutional features

Week 45-48: Polish
├── [ ] User research and iteration
├── [ ] Accessibility audit
├── [ ] Internationalization
├── [ ] Documentation
└── [ ] Launch marketing
```

---

## Part VI: Success Metrics

### The Metrics That Matter

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SUCCESS METRICS                                    │
└─────────────────────────────────────────────────────────────────────────────┘

  ENGAGEMENT METRICS
  ═══════════════════════════════════════════════════════════════════════════

  Metric                    Current     Target      Rationale
  ────────────────────────────────────────────────────────────────────────
  DAU                       ~500        100,000     10x growth per phase
  WAU                       ~2,000      500,000     Healthy DAU/WAU ratio
  Session duration          3 min       8 min       Deep engagement
  Papers viewed/session     5           12          Discovery effectiveness
  Return rate (7-day)       15%         45%         Habit formation


  RECOMMENDATION METRICS
  ═══════════════════════════════════════════════════════════════════════════

  Metric                    Current     Target      Rationale
  ────────────────────────────────────────────────────────────────────────
  Click-through rate        8%          25%         Relevance
  Save rate                 2%          10%         High-quality matches
  Explicit thumbs-down      5%          <1%         Avoiding bad recs
  Diversity (unique cats)   2.1         3.5         Avoiding filter bubble
  Serendipity score         0.15        0.35        Surprising discoveries


  RETENTION METRICS
  ═══════════════════════════════════════════════════════════════════════════

  Metric                    Current     Target      Rationale
  ────────────────────────────────────────────────────────────────────────
  D1 retention              25%         50%         First impression
  D7 retention              10%         35%         Finding value
  D30 retention             5%          25%         Habit formed
  Email open rate           12%         35%         Notification quality
  Churn (monthly)           40%         15%         Long-term value


  QUALITY METRICS
  ═══════════════════════════════════════════════════════════════════════════

  Metric                    Current     Target      Rationale
  ────────────────────────────────────────────────────────────────────────
  Papers saved per user     5           50          Library building
  Tags created per user     2           8           Organization
  Modes created per user    0           3           Context switching
  NPS score                 N/A         50+         Would recommend


  SYSTEM METRICS
  ═══════════════════════════════════════════════════════════════════════════

  Metric                    Current     Target      Rationale
  ────────────────────────────────────────────────────────────────────────
  p99 latency (homepage)    800ms       200ms       User experience
  p99 latency (search)      1200ms      300ms       Responsiveness
  Uptime                    ~95%        99.9%       Reliability
  Error rate                ~2%         <0.1%       Quality
```

---

## Part VII: The Team Structure

### Building the Team

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TEAM STRUCTURE                                     │
│                    (The 12 Programmers and Beyond)                           │
└─────────────────────────────────────────────────────────────────────────────┘

  Phase 1-2 Team (8 people)
  ═══════════════════════════════════════════════════════════════════════════

  ┌─────────────────────────────────────────────────────────────────────────┐
  │                                                                         │
  │  Engineering Lead (1)                                                   │
  │  └── Architecture decisions, code review, technical direction          │
  │                                                                         │
  │  Backend Engineers (2)                                                  │
  │  ├── API development, database, infrastructure                         │
  │  └── Authentication, security, performance                             │
  │                                                                         │
  │  ML Engineer (2)                                                        │
  │  ├── Embedding pipeline, recommendation models                         │
  │  └── Online learning, A/B testing infrastructure                       │
  │                                                                         │
  │  Frontend Engineer (2)                                                  │
  │  ├── React/Next.js application                                         │
  │  └── Mobile web, accessibility                                         │
  │                                                                         │
  │  Product Designer (1)                                                   │
  │  └── UX research, interface design, user testing                       │
  │                                                                         │
  └─────────────────────────────────────────────────────────────────────────┘


  Phase 3-4 Team (15 people)
  ═══════════════════════════════════════════════════════════════════════════

  Add:
  │
  ├── Data Engineer (1)
  │   └── Data pipelines, ETL, data quality
  │
  ├── ML Engineer (1)
  │   └── NLP/LLM integration, understanding layer
  │
  ├── Backend Engineer (1)
  │   └── Scale, performance, reliability
  │
  ├── Mobile Engineer (1)
  │   └── React Native app
  │
  ├── DevOps/SRE (1)
  │   └── Infrastructure, monitoring, on-call
  │
  ├── Product Manager (1)
  │   └── Roadmap, priorities, stakeholder management
  │
  └── Community Manager (1)
      └── User feedback, support, documentation


  TEAM RITUALS
  ═══════════════════════════════════════════════════════════════════════════

  Daily:
  - 15-min standup (async-first, Slack thread)
  - ML model metrics review

  Weekly:
  - 1-hour team sync
  - User feedback review session
  - A/B test results review

  Bi-weekly:
  - Sprint planning
  - Demo day

  Monthly:
  - Architecture review
  - OKR check-in
  - User research synthesis

  Quarterly:
  - Roadmap planning
  - Team retrospective
  - External advisory check-in
```

---

## Appendix: Lessons from the Simulation

### What the 1,000 Builds Taught Us

```
BUILD 1-100:    "Add features users ask for"
                Result: Feature bloat, confused UX
                Lesson: Users don't know what they want

BUILD 100-300:  "Optimize what we have"
                Result: 50% faster, but same engagement
                Lesson: Speed is necessary but not sufficient

BUILD 300-500:  "Copy successful products"
                Result: Worse than original
                Lesson: Our users are different

BUILD 500-700:  "Let data decide everything"
                Result: Local maxima, filter bubbles
                Lesson: Metrics can mislead

BUILD 700-900:  "Focus on one thing: discovery"
                Result: 3x engagement
                Lesson: Do one thing really well

BUILD 900-1000: "Understand the user's job-to-be-done"
                Result: Product-market fit
                Lesson: Help researchers be better researchers
```

### The One Insight

After 1,000 builds and 1,000,000 users, one insight emerged:

> **Researchers don't want to find papers. They want to understand their field,
> discover what matters, and do better research. The paper is just a vehicle.**

arxiv-sanity v2 isn't a paper recommendation system.
It's a **research intelligence platform**.

---

*Vision Document v1.0*
*December 2024*
