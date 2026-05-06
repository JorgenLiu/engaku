---
name: frontend-design
description: "Design and build distinctive, production-grade frontend interfaces with a strong visual point of view. Use when the user asks for landing pages, dashboards, websites, app screens, React components, HTML/CSS layouts, UI polish, visual redesigns, styling refactors, or when a web interface feels generic and needs stronger art direction."
context: fork
argument-hint: "Describe the UI, audience, stack, constraints, and the aesthetic direction you want."
user-invocable: true
disable-model-invocation: true
---

# Frontend Design

Turn frontend requests into real, working UI with a deliberate aesthetic direction — not default, interchangeable layouts.

## When To Use

- Build/redesign a page, component, dashboard, or app screen.
- Improve visual quality of an existing frontend.
- Add styling, motion, layout, or typography direction to React/HTML/CSS/Tailwind.
- Push design away from generic AI-looking output.

## Working Method

1. **Identify product context** — audience, purpose, content density, devices.
2. **Choose a concrete art direction** — editorial, brutalist, luxe minimal, retro-futurist, toy-like, industrial, organic, etc.
3. **Match complexity to concept** — expressive direction → richer composition/type/motion/surfaces; restrained → spacing/typography/proportion.
4. **Implement working code** — runs, fits the existing stack, preserves usability and accessibility.
5. **Refine details** — spacing, hierarchy, contrast, motion timing, states, responsive behavior.

## Design Rules

### Typography
- Distinctive font pairings over default stacks.
- Type sets mood and hierarchy, not just legibility.
- Avoid recurring defaults unless the existing product uses them.

### Color And Theme
- Cohesive palette with a strong primary mood.
- Reusable CSS variables / theme tokens when editing styles.
- Accent colors used intentionally, not scattered.

### Layout And Composition
- Intentional composition over safe component grids.
- Asymmetry, overlap, framing, rhythm, large negative space when it serves the concept.
- Clean responsive behavior on desktop and mobile.

### Motion
- A few meaningful transitions instead of constant animation.
- Motion clarifies hierarchy/state/delight.
- Respect reduced-motion preferences.

### Surfaces And Atmosphere
- Build depth with gradients, textures, shadows, patterns, masks, borders, layered surfaces when appropriate.
- Backgrounds support the concept, not flat filler.

## Avoid

- Generic startup aesthetics with interchangeable cards.
- Overused font/palette defaults outside the existing system.
- Random flourishes that don't support the chosen direction.
- Styling that looks impressive in isolation but harms clarity.

## Output

- Working frontend code, not design-only prose.
- Aligned with the project's framework and conventions.
- Preserve functional behavior of existing UI unless the task requires changes.
- Briefly state the chosen visual direction when it explains the implementation.
