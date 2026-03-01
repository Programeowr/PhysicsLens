# PhysicsLens — Detailed Submission Content

## 1) Detailed Problem Statement
Physics students, especially at school and early undergraduate levels, consistently face a conceptual bottleneck between **reading a word problem** and **drawing the correct Free Body Diagram (FBD)**. While they may memorize formulas, many struggle to identify all physical interactions in context (normal force direction, friction type, rope tension relationships, pseudo-effects in accelerating frames, etc.). This disconnect leads to a weak conceptual foundation, repeated calculation mistakes, and low confidence in solving Newtonian mechanics questions.

The challenge is larger in real classrooms because:
- Word problems are written in varied styles (textbook language, exam shorthand, handwritten notes).
- Teachers often re-explain the same FBD setup repeatedly for common scenarios (inclines, pulleys, elevators, horizontal blocks).
- Existing digital tools are either static drawing canvases (manual effort) or equation solvers that skip conceptual visualization.
- Most students are learning under time pressure, where one missed force in a diagram propagates into a full wrong solution.

As a result, there is a practical and pedagogical need for a system that can take a problem in natural language (or image form), interpret the scenario correctly, and generate a **clean, standardized, pedagogically reliable FBD** in seconds.

---

## 2) Detailed: What is your idea about?
Our idea, **PhysicsLens**, is an AI-assisted educational platform that transforms physics questions into accurate, color-coded Free Body Diagrams automatically.

At its core, PhysicsLens acts as a "concept translation layer" between problem text and visual reasoning:
1. The user submits a physics question via typed input or image upload.
2. The AI parsing layer extracts entities, scenario type, and force relationships.
3. A strict validation layer checks consistency and completeness of extracted physics structure.
4. The diagram engine generates a standardized SVG FBD tailored to the detected scenario.
5. The frontend presents the visual instantly and allows export for assignments, revision, and teaching use.

The product is not just a drawing assistant—it is a **learning accelerator**. It reduces cognitive overhead in the setup phase so students can focus on solving and understanding mechanics principles.

PhysicsLens is designed for:
- Students preparing for board exams, JEE/NEET foundations, and introductory engineering physics.
- Teachers who need faster classroom explanation assets.
- EdTech workflows where visual pedagogy can improve concept retention.

---

## 3) Detailed: What problem are you trying to solve?
PhysicsLens targets four tightly connected problems in mechanics education:

### A. Concept-to-visual translation failure
Students often know formulas but cannot map real situations into force diagrams. This leads to wrong assumptions such as missing normal force components on inclines or incorrect tension directions in pulley systems.

### B. High time cost in repetitive FBD construction
In classroom and exam prep settings, manually drawing FBDs for each problem consumes significant time. Teachers repeatedly redraw canonical setups; students repeatedly make avoidable setup errors.

### C. Input mismatch with real learning environments
Learners work from textbooks, PDFs, whiteboard snapshots, and handwritten notes. Most tools do not support this mixed input reality effectively.

### D. Lack of standardized diagram quality
Even when students attempt diagrams, notation and direction conventions vary, creating confusion and making peer/teacher review slower.

**PhysicsLens solves these by** automating extraction, validation, and rendering of scenario-aware FBDs (incline, horizontal, pulley, vertical), producing consistent visuals that can be immediately used for explanation or solution-building.

---

## 4) Detailed Technology Stack
PhysicsLens uses a modular full-stack architecture optimized for rapid interpretation and reliable rendering.

### Frontend Layer
- **React 19 + TypeScript + Vite**
- Responsibilities:
  - Text input and image-upload experience
  - Parsed output preview
  - Generated SVG rendering and export workflow
  - Fast, responsive UI suitable for classroom demos

### Backend/API Layer
- **FastAPI + Uvicorn**
- Responsibilities:
  - Endpoint orchestration (`/parse`, `/parse-image`, `/diagram`)
  - Request validation and response formatting
  - Serving deterministic diagram generation workflows

### AI Understanding Layer
- **Google Gemini 2.5 Flash (text + vision)**
- Responsibilities:
  - Parse natural-language problem statements
  - Parse uploaded question images (OCR + semantic extraction)
  - Identify scenario type and candidate force relationships

### Data Modeling and Validation Layer
- **Pydantic v2 models**
- Responsibilities:
  - Enforce strict schemas for parsed physics data
  - Catch malformed or incomplete AI outputs
  - Guarantee diagram engine receives structured, reliable input

### Reliability and Guardrail Layer
- **tenacity** for retry logic on transient AI/API failures
- **slowapi** for request rate limiting and abuse prevention

### Diagram Engine
- Custom SVG generation modules for:
  - Inclined plane
  - Horizontal surface
  - Pulley (Atwood-style)
  - Vertical/elevator scenarios
- Consistent color mappings for force categories to improve interpretability

### Testing and Quality
- **pytest** for model, parser, and diagram-level tests
- Modular architecture allows extension into new scenario types without rewriting core flow

---

## 5) Detailed Impact of your Solution
PhysicsLens delivers impact across learning outcomes, teacher productivity, and scalability.

### Student Learning Impact
- Faster understanding of force interactions through instant visual feedback.
- Reduced setup mistakes in Newtonian mechanics problems.
- Better retention through consistent, color-coded representation.
- Lower intimidation barrier for beginners who struggle with first-step diagraming.

### Teacher/Institution Impact
- Significant reduction in repetitive blackboard drawing effort.
- Ability to demonstrate multiple variants of a problem quickly.
- Reusable visual assets for lectures, notes, and LMS uploads.
- More class time available for higher-order reasoning (derivation, interpretation, edge cases).

### EdTech and Product Impact
- Strong foundation for integration into digital classrooms and test-prep platforms.
- API-first architecture enables embedding into LMS or adaptive tutoring systems.
- Expandable toward step-wise solution generation, interactive simulations, and multilingual support.

### Broader Educational Impact
By standardizing the diagramming step, PhysicsLens can improve conceptual clarity at scale in physics education. Instead of students memorizing equations blindly, the solution encourages **visual-first reasoning**, which is central to durable understanding in mechanics.
