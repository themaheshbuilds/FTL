# Project Standards & Mandatory Documentation Rules

Whenever starting, bootstrapping, or generating ANY new project, you MUST immediately initialize the standard **7-File Documentation Context Pack** in `docs/`:

1. `docs/PRD.md` — Product Requirements Document (Goals, feature scope, user flows, API contracts, compliance & security boundaries).
2. `docs/Structure.md` — Complete directory hierarchy, component roles, architectural data flows, and storage organization.
3. `docs/Rules.md` — Mandatory engineering rules, security constraints (SSRF, input validation, subprocess safety), and coding standards.
4. `docs/Phases.md` — Phased development roadmap with explicit completion milestones and current status tracking.
5. `docs/Design.md` — UI/UX design specifications, brand identity, color tokens, layout components, and all screen states.
6. `docs/Memory.md` — Persistent architectural memory, technology decisions, technical gotchas, and file-by-file reference manifest.
7. `docs/DeveloperContext.md` — AI agent operating guide, source-of-truth priority hierarchy, and Definition of Done.

This documentation context pack ensures that any future AI coding agent understands the full architectural context and never invents features or guesses file locations.
