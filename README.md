# Fleet

One source of truth for portable [Agent Skills](https://agentskills.io/specification),
synchronized across agent harnesses.

Skills live in `skills/<name>/`. Fleet links the same folder into every
configured harness path. There are no copied variants to drift.

Content edits propagate immediately through the links. Run `make sync` after
adding, renaming, or deleting a skill. Sync adds missing links and removes only
stale links that point back into this repo. It refuses to replace anything else.

## Commands

```sh
make list
make check
make targets
make status
make sync-dry-run
make sync
```

The target registry is [harnesses.toml](harnesses.toml). Its default paths
cover:

- `~/.agents/skills/<name>` for Codex, Cursor, Gemini CLI, GitHub Copilot,
  Goose, OpenCode, Windsurf, and Zed
- `~/.claude/skills/<name>` for Claude Code
- `~/.cline/skills/<name>` for Cline

Add another target to `harnesses.toml` when a harness does not support the
shared `.agents/skills` standard.

## Add a skill

1. Add `skills/<name>/SKILL.md`.
2. Keep `name` equal to the folder name.
3. Put Agent Skills fields in the YAML frontmatter. Preserve source invocation
   fields when a skill needs them.
4. Run `make check`, then `make sync`.

Optional `scripts/`, `references/`, `assets/`, and agent-specific metadata may
live inside the skill folder. Keep the core `SKILL.md` portable.

## Why this layout

The shared path is documented by
[Codex](https://developers.openai.com/codex/skills),
[Cursor](https://cursor.com/docs/skills),
[Gemini CLI](https://geminicli.com/docs/cli/using-agent-skills/),
[GitHub Copilot](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills),
[Goose](https://goose-docs.ai/docs/guides/context-engineering/using-skills/),
[OpenCode](https://opencode.ai/docs/skills),
[Windsurf](https://docs.windsurf.com/windsurf/cascade/skills), and
[Zed](https://zed.dev/docs/ai/skills). Claude Code uses its own
[skill path](https://code.claude.com/docs/en/skills), as does
[Cline](https://docs.cline.bot/getting-started/config).
