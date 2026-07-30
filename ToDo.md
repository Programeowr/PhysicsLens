# Architecture Improvement Roadmap

## Current UI Work

- [x] Move the Diagram Atlas below the hero text so the home page reads as a single clean page instead of a packed split layout.
- [x] Keep the Get Started area as a dedicated input page so users can focus on one task at a time.
- [x] Replace heavy navigation blocks on the Start page with lighter text-style navigation.
- [x] Add subtle magnetic cursor interactions for the new brutalist frontend.
- [x] Add a small set of reactive effects or motion details in the hero section so the home page feels more alive without becoming busy.
- [x] Revisit the home page spacing after the hero effect lands so the Atlas preview and scenario grid stay balanced on mobile.
- [x] Keep the Atlas preview below the hero copy and avoid reintroducing a side-by-side layout.
- [x] Keep the Start page lightweight: one clear input area, one generate action, and one small back link.

## High Priority

### Rendering Pipeline Consolidation
- [x] Introduce a `DiagramIntent` or `RenderHints` layer between `ParseResult + ForceSolution` and `SceneGraph` to hold visual decisions separately from physics facts.
- [x] Replace the active hardcoded `renderer.py` path with the documented `scene_graph.py -> layout.py -> svg_renderer.py` pipeline.
- [x] Add `SceneCanvas`, `SceneGraph`, `SceneObject`, `SceneSurface`, `SceneForce`, and `SceneAnnotation` to the shared schema module.
- [x] Create a single rendering facade, such as `render_diagram(parse_result, force_solution, output_path, render_options)`, so API and batch callers do not need to know which internal renderer is active.
- [x] Remove or deprecate duplicate rendering logic after parity is proven.
- [x] Update `Architecture.md` to match the actual parser architecture.

### Input Feature Extraction for Sharper Diagrams
- [ ] Extend parsing output with visual-semantic features: `object_type`, `surface_type`, `motion_state`, `requested_view`, `force_mentions`, `constraint_relationships`, and `known_unknown_quantities`. Impact: High. Difficulty: Medium. Dependencies: schema update and parser fixtures.
- [ ] Extract object appearance cues such as box, cart, ball, sphere, crate, block, projectile, hanging mass, pulley mass, and spring endpoint. Impact: High. Difficulty: Easy. Dependencies: render-hints schema. Quick win.
- [ ] Extract surface and environment cues such as rough floor, smooth table, frictionless ramp, inclined plane, ground baseline, pulley support, spring anchor, and air resistance context. Impact: High. Difficulty: Medium. Dependencies: render-hints schema.
- [ ] Extract motion direction and state cues such as at rest, moving up incline, moving down incline, accelerating, sliding left/right, launched upward, descending, and equilibrium. Impact: High. Difficulty: Medium. Dependencies: parser fixtures and validation rules.
- [ ] Extract explicit visual mode requests such as free-body diagram only, full scene plus FBD, show force components, show trajectory, show velocity, show acceleration, symbolic labels only, or numeric labels. Impact: High. Difficulty: Medium. Dependencies: API render options and `DiagramIntent`.
- [ ] Extract force direction provenance for push, pull, applied force, tension, friction, air resistance, normal, weight, spring force, and component forces so labels and arrows reflect the wording. Impact: High. Difficulty: Medium. Dependencies: force schema additions.
- [ ] Add ambiguity handling for visual features, returning clarification or conservative render hints when object type, motion direction, or requested view cannot be inferred confidently. Impact: High. Difficulty: Medium. Dependencies: confidence/provenance fields.
- [ ] Add golden parser fixtures that assert visual features separately from physics quantities. Impact: High. Difficulty: Easy. Dependencies: feature schema. Quick win.

### Image Quality and Layout Reliability
- [ ] Implement collision-aware label placement for force labels, object labels, angle labels, and derived-value annotations. Impact: High. Difficulty: Hard. Dependencies: scene graph pipeline active.
- [ ] Clamp force arrows to canvas bounds after magnitude scaling, including diagonal vectors on steep inclines and long applied forces. Impact: High. Difficulty: Medium. Dependencies: scene graph pipeline active.
- [ ] Add per-scenario layout invariants: no object outside canvas, no force label outside canvas, no label overlapping object bounds, and all arrows above minimum visible length. Impact: High. Difficulty: Medium. Dependencies: renderer test utilities.
- [ ] Add SVG snapshot or visual regression tests for inclined plane, horizontal friction, Atwood pulley, projectile motion, incomplete parse fallback, and unsupported scenarios. Impact: High. Difficulty: Medium. Dependencies: stable renderer facade.
- [ ] Add a layout diagnostics mode that emits bounding boxes and element IDs for debugging overlap failures. Impact: High. Difficulty: Medium. Dependencies: scene graph objects include stable IDs.
- [ ] Use `DiagramIntent` / `RenderHints` to select sharper visual primitives, such as cart wheels, ball markers, hanging-mass blocks, pulley ropes, surface texture marks, velocity vectors, acceleration vectors, and component construction lines. Impact: High. Difficulty: Medium. Dependencies: input feature extraction.

### API, Storage, and Request Flow
- [ ] Stop writing API responses through temporary files for normal `/solve` requests. Return SVG text or bytes directly from the renderer to reduce filesystem overhead and race surface. Impact: High. Difficulty: Medium. Dependencies: renderer facade returns an in-memory SVG option.
- [ ] Add request size limits and validation for `SolveRequest.text`, including max length, empty text handling, and clear 4xx responses. Impact: High. Difficulty: Easy. Dependencies: none. Quick win.
- [ ] Replace permissive CORS configuration with environment-specific allowed origins. Impact: High. Difficulty: Easy. Dependencies: frontend deployment origin config. Quick win.
- [ ] Introduce structured error responses with stable error codes for `needs_clarification`, `unsupported_scenario`, parser failure, solver failure, renderer failure, and internal error. Impact: High. Difficulty: Medium. Dependencies: API response contract update.
- [ ] Add a correlation/request ID propagated through parser, solver, renderer, and API logs. Impact: High. Difficulty: Easy. Dependencies: logging setup. Quick win.

### Failure Handling and Correctness
- [ ] Wrap pipeline stages in explicit stage-level exceptions so parser, validation, solver, layout, and SVG rendering failures are distinguishable. Impact: High. Difficulty: Medium. Dependencies: structured API errors.
- [ ] Add solver guardrails for invalid physical values such as negative mass, zero or negative speed, extreme angles, invalid friction coefficients, and non-finite derived values. Impact: High. Difficulty: Medium. Dependencies: validation schema rules.
- [ ] Add renderer fallback behavior when a solved force references an unknown object anchor. Impact: High. Difficulty: Easy. Dependencies: scene graph pipeline active. Quick win.
- [ ] Add tests for incomplete and unsupported scenarios returning useful diagrams or useful errors across both `/solve` and `/solve.svg`. Impact: High. Difficulty: Medium. Dependencies: API test harness.

## Medium Priority

### Prompt and Parsing Pipeline
- [ ] Decide whether the product architecture is fully deterministic or LLM-assisted, then encode that decision in `Architecture.md`, README, tests, and deployment notes. Impact: Medium. Difficulty: Easy. Dependencies: product decision. Quick win.
- [ ] If LLM parsing returns, isolate it behind a `ParserProvider` interface with deterministic rule-based parsing as the default fallback. Impact: Medium. Difficulty: Medium. Dependencies: parser architecture decision.
- [ ] If LLM parsing returns, add prompt templates that separately request physics facts, visual-semantic features, uncertainty/provenance, and render intent; include JSON schema versioning, model/version metadata, temperature/seed settings, retry policy, and golden parse fixtures. Impact: Medium. Difficulty: Hard. Dependencies: `ParserProvider` and render-hints schema.
- [ ] Add confidence and ambiguity handling to classification so mixed prompts, multiple scenarios, and underspecified wording produce clarification instead of accidental routing. Impact: Medium. Difficulty: Medium. Dependencies: parser contract update.
- [ ] Add normalized units and extraction provenance to `ParseResult`, such as source span, original unit, normalized value, parser strategy, and whether the field affects physics, rendering, or both. Impact: Medium. Difficulty: Medium. Dependencies: schema migration.
- [ ] Split parser tests into physics extraction, render-hint extraction, and ambiguity resolution suites so sharpness improvements do not accidentally change solver behavior. Impact: Medium. Difficulty: Easy. Dependencies: feature schema. Quick win.

### Caching and Cost Optimization
- [ ] Add deterministic cache keys from normalized input text, parser version, render-hints version, solver version, renderer version, and render options. Impact: Medium. Difficulty: Medium. Dependencies: normalized parse metadata.
- [ ] Cache final SVG responses for repeated identical requests. Impact: Medium. Difficulty: Medium. Dependencies: cache key strategy.
- [ ] Cache parsed physics facts and render hints separately from rendered SVG so different canvas sizes, styles, and visual modes can reuse extraction and solving. Impact: Medium. Difficulty: Medium. Dependencies: parser, render-hints, and renderer versioning.
- [ ] If LLM parsing returns, cache LLM parse outputs aggressively and prefer rule-based extraction for supported simple scenarios to minimize model calls. Impact: Medium. Difficulty: Medium. Dependencies: `ParserProvider`.
- [ ] Add benchmark tests for parse, solve, scene graph, layout, SVG render, Base64 encode, and HTTP response time. Impact: Medium. Difficulty: Medium. Dependencies: stable pipeline stage boundaries.

### Async Processing and Scalability
- [ ] Keep current synchronous API for small deterministic SVGs, but define thresholds for when requests should move to background jobs, such as expensive LLM parse, high-resolution export, PNG/PDF conversion, or batch generation. Impact: Medium. Difficulty: Easy. Dependencies: performance benchmarks.
- [ ] Add an optional job model with `POST /jobs`, `GET /jobs/{id}`, and `GET /jobs/{id}/artifact` for future long-running render/export tasks. Impact: Medium. Difficulty: Hard. Dependencies: storage backend and job state model.
- [ ] Add idempotency keys for async jobs and repeated frontend submissions. Impact: Medium. Difficulty: Medium. Dependencies: job model or cache key strategy.
- [ ] Add concurrency limits around expensive parser providers and export workers. Impact: Medium. Difficulty: Medium. Dependencies: async/job architecture.

### Asset Handling and Storage
- [ ] Define an artifact abstraction that supports in-memory SVG, local file output, and future object storage without changing the core pipeline. Impact: Medium. Difficulty: Medium. Dependencies: renderer facade.
- [ ] Store artifact metadata separately from content: hash, scenario, canvas size, renderer version, created time, and status. Impact: Medium. Difficulty: Medium. Dependencies: artifact abstraction.
- [ ] Sanitize SVG output consistently and keep all text escaped at render boundaries. Impact: Medium. Difficulty: Easy. Dependencies: renderer facade. Quick win.
- [ ] Add configurable canvas sizes and render options through the API, with bounded min/max values. Impact: Medium. Difficulty: Medium. Dependencies: scene graph pipeline active.

### Observability
- [ ] Add structured JSON logs for request received, parse complete, validation result, solve complete, layout complete, render complete, and response sent. Impact: Medium. Difficulty: Easy. Dependencies: request ID. Quick win.
- [ ] Add metrics for request count, status codes, scenario distribution, missing-field frequency, render duration, parser duration, cache hit rate, and output SVG size. Impact: Medium. Difficulty: Medium. Dependencies: metrics library choice.
- [ ] Add tracing spans across parser, validation, solver, scene graph, layout, renderer, storage, and API serialization. Impact: Medium. Difficulty: Medium. Dependencies: OpenTelemetry or equivalent.
- [ ] Add quality metrics for SVG layout, including overlap count, out-of-bounds elements, label count, and force count. Impact: Medium. Difficulty: Medium. Dependencies: layout diagnostics.

## Low Priority

### Developer Experience
- [ ] Add an architecture decision record explaining deterministic SVG generation versus AI raster image generation. Impact: Low. Difficulty: Easy. Dependencies: architecture decision. Quick win.
- [ ] Add a small CLI command for `solve`, `render`, `render-json`, and `inspect-layout`. Impact: Low. Difficulty: Medium. Dependencies: renderer facade.
- [ ] Add typed API response models for successful solve, clarification, unsupported scenario, and errors. Impact: Low. Difficulty: Medium. Dependencies: API response contract.
- [ ] Add a contributor checklist for adding a scenario: classifier triggers, slot extraction, validation, solver, scene graph builder, layout rules, renderer coverage, API fixtures, and visual snapshots. Impact: Low. Difficulty: Easy. Dependencies: scenario architecture stabilized.
- [ ] Add fixtures for canonical prompts and expected parse/solution/render metadata. Impact: Low. Difficulty: Easy. Dependencies: stable schema.

### API Ergonomics
- [ ] Add `GET /health` and `GET /version` endpoints reporting parser version, renderer version, supported scenarios, and optional dependency availability. Impact: Low. Difficulty: Easy. Dependencies: version constants. Quick win.
- [ ] Add `GET /scenarios` so the frontend can render supported and unsupported scenarios from backend metadata instead of duplicating scenario knowledge. Impact: Low. Difficulty: Medium. Dependencies: scenario registry metadata.
- [ ] Add response fields for `parse_result`, `render_metadata`, and `warnings` behind an optional `debug=true` flag. Impact: Low. Difficulty: Medium. Dependencies: stable response models.

### Rendering Polish
- [ ] Add force component rendering mode for incline diagrams, including `mg sin(theta)` and `mg cos(theta)` construction lines. Impact: Low. Difficulty: Medium. Dependencies: scene graph annotations.
- [ ] Add theme tokens for textbook, high-contrast, and print-friendly output. Impact: Low. Difficulty: Medium. Dependencies: renderer style abstraction.
- [ ] Add SVG accessibility improvements: `<title>`, `<desc>`, semantic group labels, and meaningful IDs for forces and objects. Impact: Low. Difficulty: Easy. Dependencies: renderer facade. Quick win.
- [ ] Add optional frontend hover highlighting for forces and derived values using stable SVG IDs. Impact: Low. Difficulty: Medium. Dependencies: SVG semantic IDs and frontend state mapping.

## Future Enhancements

### Advanced Scenarios
- [ ] Implement circular motion end to end: classifier confidence, slot extraction, solver, scene graph, layout, renderer, tests. Impact: Future. Difficulty: Hard. Dependencies: scenario contributor checklist.
- [ ] Implement spring-mass systems end to end with Hooke's law forces and spring-specific SVG primitives. Impact: Future. Difficulty: Hard. Dependencies: scenario contributor checklist.
- [ ] Add connected blocks and multi-object force diagrams with object-specific force panels. Impact: Future. Difficulty: Hard. Dependencies: generalized scene graph and collision-aware layout.
- [ ] Add multi-pulley systems with reusable rope/path layout primitives. Impact: Future. Difficulty: Hard. Dependencies: generalized pulley surface model.

### Export and Delivery
- [ ] Add PNG export through a controlled server-side renderer only after SVG quality and caching are stable. Impact: Future. Difficulty: Medium. Dependencies: artifact abstraction and async jobs.
- [ ] Add PDF export for worksheet or report generation. Impact: Future. Difficulty: Medium. Dependencies: artifact abstraction and async jobs.
- [ ] Add persistent object storage for generated artifacts when sharing, history, or async export becomes a product requirement. Impact: Future. Difficulty: Hard. Dependencies: artifact metadata model.

### Quality Automation
- [ ] Add a visual test gallery that renders every canonical prompt at multiple canvas sizes. Impact: Future. Difficulty: Medium. Dependencies: visual regression framework.
- [ ] Add property-based tests for layout under randomized masses, angles, friction coefficients, and canvas sizes. Impact: Future. Difficulty: Hard. Dependencies: layout invariants.
- [ ] Add automated cost/performance reports if any LLM provider or paid export service is introduced. Impact: Future. Difficulty: Medium. Dependencies: provider abstraction and metrics.
