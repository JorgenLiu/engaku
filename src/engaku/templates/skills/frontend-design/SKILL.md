---
name: frontend-design
description: "Design and build distinctive, production-grade frontend interfaces with a strong visual point of view. Use when the user asks for landing pages, dashboards, websites, app screens, React components, HTML/CSS layouts, UI polish, visual redesigns, styling refactors, or when a web interface feels generic and needs stronger art direction."
argument-hint: "Describe the UI, audience, stack, constraints, and the aesthetic direction you want."
user-invocable: true
disable-model-invocation: true
---

# Frontend Design

Use this skill to turn frontend requests into real, working UI with a deliberate aesthetic direction instead of default, interchangeable layouts.

## When To Use

- Build or redesign a web page, component, dashboard, or app screen.
- Improve the visual quality of an existing frontend.
- Add styling, motion, layout, or typography direction to React, HTML, CSS, Tailwind, or similar UI code.
- Push a design away from generic AI-looking output.

## Working Method

1. Identify the product context.
   Ask or infer the audience, purpose, content density, and device expectations.
2. Choose a concrete art direction.
   Pick a clear design lane such as editorial, brutalist, luxe minimal, retro-futurist, toy-like, industrial, organic, or another strong visual identity.
3. Match complexity to the concept.
   If the direction is expressive, use richer composition, type, animation, and surface treatment. If the direction is restrained, focus on spacing, typography, and proportion.
4. Implement working code.
   Produce code that runs, fits the existing stack, and preserves usability and accessibility.
5. Refine details.
   Tighten spacing, hierarchy, contrast, motion timing, states, and responsive behavior.

## Design Rules

### Typography

- Prefer distinctive font pairings over default stacks.
- Use typography to establish mood and hierarchy, not just legibility.
- Avoid recurring default choices unless the existing product already uses them.

### Color And Theme

- Commit to a cohesive palette with a strong primary mood.
- Define reusable CSS variables or theme tokens when editing styles.
- Use accent colors intentionally instead of scattering them everywhere.

### Layout And Composition

- Favor intentional composition over safe component grids.
- Use asymmetry, overlap, framing, rhythm, or large negative space when it improves the concept.
- Keep responsive behavior clean on both desktop and mobile.

### Motion

- Use a few meaningful transitions or reveals instead of constant animation noise.
- Prefer motion that clarifies hierarchy, state, or delight.
- Respect reduced-motion expectations when relevant.

### Surfaces And Atmosphere

- Build depth with gradients, textures, shadows, patterns, masks, borders, or layered surfaces when appropriate.
- Backgrounds should support the concept rather than default to flat filler.

## Avoid

- Generic startup aesthetics with interchangeable cards and bland spacing.
- Overused font and palette defaults when they are not part of the existing system.
- Random visual flourishes that do not support the chosen direction.
- Styling that looks impressive in isolation but harms clarity or usability.

## Output Expectations

- Deliver working frontend code, not design-only prose.
- Keep implementation aligned with the project's framework and conventions.
- If editing an existing UI, preserve its functional behavior unless the task requires behavioral changes.
- Briefly state the chosen visual direction when it helps explain the implementation.

## Token Budget

- Answer in English by default; switch language only when explicitly requested.
- State visual direction in one or two sentences; do not enumerate every option when a clear pick fits.
- Cut filler before code; let the implementation carry the detail.
