# PhysicsLens — Research & Resource Guide

---

## 1. The Core Problem — Physics Education Research

Start here to understand *why* this matters and what research backs it up.

- **Cognitive Load Theory** — John Sweller. The foundational framework behind why visual aids reduce mental effort. Understanding this sharpens every product decision you make. Search Google Scholar.
- **Mayer's Multimedia Learning Theory** — Explains why text + diagram outperforms text alone. This is your product's scientific justification.
- **NCERT Class 11 Physics Chapter 5 (Laws of Motion)** — The actual curriculum your users are studying. Read it like a student, not an engineer. Free at [ncert.nic.in](https://ncert.nic.in)
- **AP Physics 1 Curriculum Framework** — College Board. Relevant if you want international scope later.
- **Van Heuvelen — *Learning to Think Like a Physicist* (1991)** — Old but foundational on FBD pedagogy specifically. Search Google Scholar.

---

## 2. NLP & AI Parsing

Your hardest technical problem — going from messy English to clean structured data.

- **Anthropic Tool Use / Function Calling Docs** — [docs.anthropic.com](https://docs.anthropic.com) — Exactly how your backend extracts structured JSON from problem text. Read the structured output examples carefully.
- **Anthropic Cookbook** — [github.com/anthropics/anthropic-cookbook](https://github.com/anthropics/anthropic-cookbook) — Worked examples of extracting JSON from scientific text. Study the system prompt patterns.
- **Stanford NLP Book** — [web.stanford.edu/~jurafsky/slp3](https://web.stanford.edu/~jurafsky/slp3) — Free online. Chapters 17 and 18 on Information Extraction are most relevant.
- **SpaCy Docs** — [spacy.io](https://spacy.io) — Even if you use Claude for all parsing, understanding named entity recognition gives you a mental model for what Claude is doing internally and how to prompt it better.

---

## 3. SVG & Diagram Rendering

D3.js is your rendering engine. Go deep on this.

- **D3.js Official Docs** — [d3js.org](https://d3js.org) — Specifically the `d3-force`, `d3-scale`, and `d3-path` modules.
- ***Interactive Data Visualization for the Web* — Scott Murray** — The best D3 book. Free online at [alignedleft.com/work/d3-book](http://alignedleft.com/work/d3-book). Chapters on scales, paths, and SVG transforms are most relevant.
- **SVG Specification — MDN Web Docs** — [developer.mozilla.org/en-US/docs/Web/SVG](https://developer.mozilla.org/en-US/docs/Web/SVG) — You'll be hand-writing SVG arrowheads, transforms, and coordinate systems. Know the spec.
- **TikZ FBD Examples** — Search "TikZ FBD examples" on TeX Stack Exchange. Not your stack but looking at how physicists draw FBDs in LaTeX teaches you the visual grammar: where arrows originate, how labels sit, what a correct diagram looks like.
- **Manim** — [manim.community](https://www.manim.community) — 3Blue1Brown's animation library. Study how they render physics vectors and scenes. Same visual problem, different stack. Their approach to coordinate systems and arrow geometry is instructive.

---

## 4. Free Body Diagram Standards

You need to know what a correct FBD actually looks like before you can build one.

- ***University Physics* — Young & Freedman** — The gold standard textbook. Chapters 4 and 5 walk through FBD construction in detail. Cross-reference this with Halliday.
- ***Halliday, Resnick & Krane*** — Same domain, different style. Understand which conventions are universal vs. which vary by textbook.
- **The Physics Classroom** — [physicsclassroom.com](https://www.physicsclassroom.com) — Free, extremely well-written explanations of FBD conventions. This is what your target users read. Study how they explain forces.
- **Khan Academy Physics** — [khanacademy.org](https://www.khanacademy.org) — Watch the Newton's Laws section. Not for content but to understand the pedagogical voice and step size your users are accustomed to.
- **HyperPhysics — Georgia State** — [hyperphysics.phy-astr.gsu.edu](http://hyperphysics.phy-astr.gsu.edu) — Reference-style physics, excellent for checking notation correctness.

---

## 5. Existing Tools — Know Your Landscape

Study these carefully. Understand exactly where they stop and where your product begins.

| Tool | What it does | Where it stops |
|---|---|---|
| [Wolfram Alpha](https://www.wolframalpha.com) | Solves physics problems numerically | No diagram of the problem setup |
| [Photomath](https://photomath.com) | Solves equations from photos | No diagram generation |
| [PhET Simulations](https://phet.colorado.edu) | Interactive physics simulations | Not problem-specific, manual setup |
| [GeoGebra Physics](https://www.geogebra.org) | Closest existing thing to PhysicsLens | Requires manual setup — no NLP parsing |
| [Desmos](https://www.desmos.com) | Mathematical visualization | No physics-specific domain |
| [Brilliant.org](https://brilliant.org) | Sequenced physics problems | Study their step-reveal UX pattern |

---

## 6. Frontend Architecture

- **React Docs** — [react.dev](https://react.dev) — Specifically state management and `useEffect`, which you'll use heavily for diagram re-renders.
- **Vite Docs** — [vitejs.dev](https://vitejs.dev) — Your build tool. Fast, minimal config.
- **Zustand** — [zustand-demo.pmnd.rs](https://zustand-demo.pmnd.rs) — Simpler than Redux, enough for this app. Read the docs in one sitting.
- **Tailwind CSS Docs** — [tailwindcss.com/docs](https://tailwindcss.com/docs) — Have this open while building.
- **FileSaver.js** — [github.com/eligrey/FileSaver.js](https://github.com/eligrey/FileSaver.js) — Your PNG/SVG export library. Read the README — there are browser quirks.

---

## 7. Backend Architecture

- **FastAPI Docs** — [fastapi.tiangolo.com](https://fastapi.tiangolo.com) — Read the full tutorial section, especially async endpoints and Pydantic integration.
- **Pydantic v2 Docs** — [docs.pydantic.dev](https://docs.pydantic.dev) — Your schema validation layer. Validators and model serialization sections are most relevant.
- **slowapi** — [github.com/laurentS/slowapi](https://github.com/laurentS/slowapi) — FastAPI rate limiting library. Five-minute integration.
- **Railway Docs** — [railway.app/docs](https://railway.app/docs) — Your deployment target. Free tier, supports Python containers.
- **Render Docs** — [render.com/docs](https://render.com/docs) — Alternative deployment. Same story.

---

## 8. Indian Education Context

Matters for curriculum alignment and eventual language support.

- **CBSE Physics Syllabus Class 11** — [cbseacademic.nic.in](https://cbseacademic.nic.in) — The exact topics, sequence, and problem types your primary users encounter.
- **NCERT Exemplar Problems Physics Class 11** — Harder problems. Great for building your benchmark test set.
- **JEE Main & Advanced Previous Papers (Physics — Laws of Motion)** — [jeemain.nta.nic.in](https://jeemain.nta.nic.in) — The most complex NLM problems Indian students face. Test your parser on these.
- **NEET Physics Papers** — Secondary target audience. Similar problem structure.
- **Bhashini** — [bhashini.gov.in](https://bhashini.gov.in) — Government of India's translation API for Indian languages. Your v2 multilingual pipeline for Hindi/Tamil input.
- **IndicNLP / AI4Bharat** — [github.com/AI4Bharat/indicnlp_catalog](https://github.com/AI4Bharat/indicnlp_catalog) — NLP resources for Indian languages. Bookmark for v2.

---

## 9. Design & UX

- ***Don't Make Me Think* — Steve Krug** — The best short book on web UX. Particularly relevant for your student audience who has zero patience for friction.
- **Nielsen Norman Group** — [nngroup.com](https://www.nngroup.com) — Search "e-learning UX" and "progressive disclosure." Your step-by-step panel maps directly to progressive disclosure research.
- **Figma** — [figma.com](https://www.figma.com) — Design your UI before building it. Free tier is enough. Look at physics/education app UI on Dribbble and Mobbin for inspiration.
- **WCAG Contrast Checker** — [webaim.org/resources/contrastchecker](https://webaim.org/resources/contrastchecker) — Your force vector colors need to pass WCAG AA contrast against both white and dark backgrounds.

---

## 10. Research Papers Worth Reading

Search all of these on [Google Scholar](https://scholar.google.com) or [ResearchGate](https://www.researchgate.net).

- **The Effectiveness of Free Body Diagrams in Learning Newtonian Mechanics** — Multiple papers. Filter to any post-2010 meta-analysis.
- **AI in Physics Education** — Search this phrase, filter 2020–2024. The field is young and you'll find papers citing the exact gap you're solving.
- **Automatic Generation of Physics Problems** — Tangential but reveals how researchers think about problem structure, which informs your parsing approach.
- **Intelligent Tutoring Systems (ITS)** — The 40-year research tradition your product sits within. Bloom's *2 Sigma Problem* (1984) is the landmark paper.
- **Physical Review Physics Education Research** — Free, open-access journal. The most useful academic publication for your domain. [journals.aps.org/prper](https://journals.aps.org/prper)

---

## 11. Communities to Follow

- **Anthropic Discord** — [discord.gg/anthropic](https://discord.gg/anthropic) — Active community. People building exactly the AI-parsing pipelines you need.
- **AI4Bharat** — [ai4bharat.org](https://ai4bharat.org) — Indian AI research org. Directly relevant to your multilingual roadmap.
- **IndiaAI** — [indiaai.gov.in](https://indiaai.gov.in) — Government AI initiative. Track for grants and partnerships.
- **Physics Education Research Community** — Follow *Physical Review Physics Education Research* journal.
- **r/learnpython** and **r/webdev** — Practical build questions.

---

## Recommended Starting Order

| Priority | What | Why |
|---|---|---|
| 1 | Cognitive Load Theory summary (one paper) | Scientific foundation for every decision |
| 2 | Paste 20 JEE problems into Wolfram Alpha | Feel the gap your product fills |
| 3 | D3.js Scott Murray book (Chapters 1–8) | Core technical risk #1 |
| 4 | Anthropic Tool Use docs + Cookbook examples | Core technical risk #2 |
| 5 | NCERT Chapter 5 + PhysicsClassroom.com FBD section | Understand your user's actual curriculum |
| 6 | GeoGebra Physics — spend 30 mins using it | Know your closest competitor deeply |
