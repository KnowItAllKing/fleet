# Repository instructions

- Treat `skills/<name>/` as the canonical source. Never keep copied variants
  for different agents.
- Follow the Agent Skills specification. The folder and frontmatter `name`
  must match and use lowercase letters, digits, and hyphens.
- Keep shared frontmatter portable. Put agent-specific configuration in
  separate files inside the skill folder.
- Write descriptions that state what the skill does and when it should load.
- Keep `SKILL.md` focused. Put conditional detail in `references/` and reusable
  automation in `scripts/` only when needed.
- Run `make check` and `make test` after every change.
- Keep harness paths and their coverage in `harnesses.toml`.
- Do not run `make sync` unless the user asks. It writes links into the
  user's home directory.
