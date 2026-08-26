# PhysicsLens TODO

## Future Enhancements

### Structured Input UI
**Priority:** Medium  
**Effort:** 2–3 days

Add a structured form interface alongside the free-text input to eliminate parsing ambiguity for common cases.

**Design:**
```
┌─────────────────────────────────────────────────┐
│ Quick Setup                                     │
├─────────────────────────────────────────────────┤
│ Scenario:  [Inclined Plane ▾]                   │
│ Object:    [Box ▾]  Mass: [5] kg                │
│ Angle:     [30] degrees                          │
│ Friction:  [Frictionless ▾]                      │
│ Find:      [☑ Normal Force  ☑ Required Force]   │
│                                                  │
│ [Generate Diagram]                               │
└─────────────────────────────────────────────────┘
  or paste free-form text below ↓
```

**Benefits:**
- Zero parsing errors for guided input
- Faster input for repetitive problems
- Educational — shows users what parameters each scenario needs
- Falls back to text parser for advanced/custom problems

**Implementation notes:**
- Add `frontend/src/components/StructuredForm.jsx`
- Map form state → canonical text string → existing pipeline
- No backend changes required — just client-side text generation
- Keep free-text input as the primary UX; form is optional shortcut

**Related:**
- Could auto-populate form fields when user pastes text (reverse parsing)
- Consider scenario templates library (e.g., "Atwood Machine Presets")
