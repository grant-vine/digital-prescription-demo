# User Stories

**Parent:** [Root AGENTS.md](../AGENTS.md)

## OVERVIEW

25 user stories (001-025) covering MVP through production phases. Index in `README.md`.

## NAMING

```
###-descriptive-slug.md
```
- `###`: Zero-padded 3-digit (001-025, next available: 026)
- `slug`: Lowercase, hyphen-separated
- Numbering reflects implementation order and dependency chain

## REQUIRED SECTIONS

Every story MUST include (in order):
1. **Title** — Clear, concise
2. **User Story** — "As a [role], I want [goal], so that [benefit]"
3. **Description** — 2-3 sentences
4. **Context** — Background, constraints, business rules
5. **Acceptance Criteria** — Checkboxes `- [ ]`, testable
6. **API Integration Points** — Endpoints if applicable
7. **Technical Implementation** — Code examples, schemas
8. **Notes** — Edge cases, demo simplifications
9. **Estimation** — Story Points (Fibonacci), Time, Dependencies (US-###)
10. **Related Stories** — Cross-references

## PHASES

| Phase | Stories | Timeline |
|-------|---------|----------|
| MVP Core Workflow | 001-011 | Weeks 1-4 |
| Core System Features | 012-016 | Weeks 3-4 |
| Enhanced/Production | 017-025 | Weeks 7-14 |

## DEPENDENCY CHAIN

```
001 → 002 → 003 → 004 → 006 → 007 → 008 → 010 → 011
                                              ↑
                                            009
```

## WHEN ADDING/MODIFYING

- Next story number: **026**
- Update `user-stories/README.md` index table
- Verify dependency references match actual story numbers
- Keep acceptance criteria testable (not vague)
- Add `Related Stories` cross-references both ways
