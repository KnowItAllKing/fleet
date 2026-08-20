Engineering Principles
======================

High-level principles distilled from recurring architecture review feedback in this repo.
Each principle links the PRs where it was articulated. These complement
[norms.md](norms.md) (team practices) and [testing.md](testing.md) (test taxonomy).

## 1. Move every guarantee to the earliest stage it can live

Past a certain point, mistakes are forever. The stages, earliest to latest:
**design → test → runtime → persistence.** Push every correctness guarantee as far
left as it can go.

- **Design time — build only what today's named problem requires.** Reversible
  hardcoding beats speculative configuration: a hardcoded path can be changed
  tomorrow, a persisted config schema is a future data migration. Scope you can't
  justify today gets a ticket, not code. Proposals are prompts for the next
  iteration, not waterfall documentation of an end state. (#14416, #18131)
- **Design time — distinct behaviors get distinct types.** Two modes squashed into
  one node/class/message is a design smell; introduce a new node type and let the
  workflow definition branch. (#14416)
- **Test time — only the real system can vouch for the real system.** No mocks,
  ever: stand up the real gRPC server, the real emulator, in the test. No-op fakes
  hide broken output until production finds it. (#17631, #10463's sibling: the only
  allowed `DELETE FROM` lives in test code)
- **Runtime — "runs twice" must be harmless by construction.** Every workflow node
  executes under at-least-once delivery: concurrent execution and redelivery are
  normal, not exceptional. Node-level idempotency is a MUST — and note that
  node-level idempotency does not compose into workflow-level idempotency. (#7434,
  [workflows_101.md](workflows_101.md))
- **Persistence — there is no undo.** We never hard delete data from Spanner.
  Persisted shapes and published APIs are supported forever; think about
  backwards-compat up front. (#10463)
