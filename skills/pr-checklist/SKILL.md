---
name: pr-checklist
description: Review this checklist, which is based on recurring feedback patterns.
---
Please review the current branch's changes according to the following guidelines.

## PR Basics
- [ ] PR is focused on one concern (avoid bundling unrelated changes)
- [ ] PR has a description explaining what was done and why (not just linking the ticket)
- [ ] Manual QA steps included, or explicitly stated if not possible
- [ ] No commented-out code committed
- [ ] Code being modified has been checked for other consumers (grep for usages)

## AI/LLM-Generated Code Review
- [ ] Removed redundant null/empty checks where methods already handle those cases
- [ ] No silent `continue` or `return` statements that could drop data
- [ ] Defensive fallbacks are intentional, not just "safe" defaults that produce nonsense
- [ ] Prefer failing fast with clear errors over silently masking problems
- [ ] Reviewed every `if (x != null)` and `if (!x.isEmpty())` check

## Java Code Style
- [ ] Using `var` instead of explicit type declarations
- [ ] Using `@SneakyThrows` instead of consuming/ignoring exceptions
- [ ] Fields are `private final` where appropriate
- [ ] Return types use `List<X>` not concrete implementations like `ArrayList<X>`
- [ ] Using primitive `boolean` over `Boolean` unless nullability needed
- [ ] Using `map.putIfAbsent()` instead of `if (!map.containsKey())`
- [ ] Imports not collapsed (IntelliJ count set to 999)
- [ ] No `UPPER_CASE` names for local variables
- [ ] No ignored IntelliJ IDEA warnings
- [ ] Mock/test-double REST classes implement an interface (same as real implementations)
- [ ] `catch-and-throw` is an anti-pattern, always use `@SneakyThrows`!!!!
- [ ] Use `OkHttpClient` instead of `HttpURLConnection` for HTTP requests

## Protobuf
- [ ] Enums start with `UNSPECIFIED = 0` or `MY_ENUM_UNSPECIFIED = 0`
- [ ] Enum values don't have prefix: `FOO = 1` not `MY_ENUM_VALUE_FOO = 1`
- [ ] No changes to existing field numbers
- [ ] No `reserved` shit for backwards compatibility
- [ ] No unused fields in proto definitions
- [ ] Considered using protobuf instead of `Map<String, Object>` or `JsonNode`
- [ ] Prefer `oneof` for mutually exclusive options over separate optional fields
- [ ] Use `map<string, string>` for flexible key-value params (substitutions, config)
- [ ] Whenever making ANY change to a protobuf file, examine ALL possible downstream impacts. This often includes other language packages and even Terraform, like Cloud Scheduler payloads
- [ ] Do not duplicate parent-message concepts inside nested messages unless the semantics are truly different
- [ ] Unless the proto is tenant/job-specific, new proto fields should represent generic domain concepts, not one tenant/job’s current implementation details

## Testing
- [ ] New/changed code has corresponding tests
- [ ] Tests are at the lowest level possible (unit > integration)
- [ ] Useful tests disabled with `@Disable` rather than deleted
- [ ] Test code stays in `src/test`, not leaking into `src/main`
- [ ] No-op mocks aren't hiding real integration issues (verify mock behavior matches production)
- [ ] All unit tests must use gRPC services and connections and send data over the wire. No mocking or in-memory testing for services!
- [ ] Reusable test setup belongs in the test harness, not duplicated across individual test files
- [ ] When CI already has integration tests for an external service (e.g., Google Drive), new interactions with that service need integration tests too

## Data & Database
- [ ] No hard deletes from Spanner (soft delete only)
- [ ] `DELETE FROM` only in test code
- [ ] Queries include `AND deleted = FALSE` where applicable
- [ ] IDs never reassigned or reused

## Architecture
- [ ] No class hierarchies without abstract methods (use composition)
- [ ] Hardcoded values moved to configuration
- [ ] Module boundaries are explicit: `lib` owns reusable, non-`Nut` abstractions/helpers; `nut` owns `Nut`-based runtime adapters and wiring
- [ ] Public interfaces belong in the lowest reusable layer that does not require runtime lifecycle concerns; nut should implement/adapt them rather than redefine them
- [ ] Follow established Java config patterns (`java/config/...`) for new config classes instead of ad hoc env/config helpers
- [ ] Large files processed with streaming, not loaded into memory
- [ ] CSV parsing uses Apache CSV library, not `split(",")`
- [ ] Shared code extracted to `shared/` libraries where appropriate
- [ ] Not extending deprecated/dead code - use the maintained solution instead (e.g., CEL over custom templates)
- [ ] If adding a "mode" or conditional behavior to shared code, consider separate classes instead
- [ ] Understand implicit contracts (e.g., output formats consumed by other systems like GCS Transfer Jobs)
- [ ] Keep configurations for different concerns decoupled (e.g., delivery paths vs output structure)
- [ ] Extend existing classes/mocks rather than creating parallel ones that do similar things
- [ ] When adding methods that don't fit the class name, rename the class or create a proper new abstraction — don't stuff unrelated functionality into an existing class
- [ ] New behavior should compose with existing idempotency, retry, metadata, logging, and error-handling mechanisms
- [ ] If a change bypasses existing shared machinery, call that out explicitly and justify it. DOUBLE CHECK THAT EVERY CHANGE DOESN'T ALREADY HAVE SHARED MACHINERY.

## Service & Workflow Architecture
- [ ] Prefer gRPC over PubSub for synchronous service-to-service calls
- [ ] Reuse existing APIs (e.g., `common_reports.proto`) instead of creating new communication channels
- [ ] Use CDC + `workflow_update_event` topic for workflow status propagation, not custom PubSub topics
- [ ] Use standard `WorkflowWatcherNode` for watching external workflows, not custom nodes
- [ ] Use `LazyResource` for heavy client initialization (BigQuery, external APIs)
- [ ] Make shared nodes self-sufficient with params (`substitutions`, `parameters` maps) instead of requiring subclasses
- [ ] YAGNI: Delete unnecessary abstractions (e.g., base classes with only one implementation)
- [ ] YAGNI: If hardcoding works today and tomorrow's requirements are unknown, leave it hardcoded
- [ ] Follow existing BFF routing patterns (e.g., generic `PokeWorkflowRequest` with workflow definition) instead of creating per-use-case endpoints
- [ ] No in-process polling loops with sleep for workflow waits; use durable workflow/event/watcher mechanisms
- [ ] Do not make API request latency depend on long-running external work unless the API is explicitly synchronous
- [ ] If a workflow publishes external work, completion should be represented durably and resumed asynchronously
- [ ] PubSub handlers should process one clear message semantic; avoid reusing a topic for unrelated operation models

## GCP/Infrastructure
- [ ] No endpoints that can access arbitrary GCS paths (security)
- [ ] Using `BlobId` API for GCS URIs, not manual string manipulation
- [ ] Using `EMULATOR_HOST` env vars for local/test, not project name checks
- [ ] Workflow state stored properly, not reconstructed from assumptions

## Plan Sanity Check
- [ ] Before editing, identify the existing abstraction/API this change is extending
- [ ] Confirm whether the change is a new use case of an existing abstraction or a genuinely new abstraction
- [ ] If adding a new mode/branch to shared code, explain why the existing model cannot express the behavior
- [ ] Avoid duplicating existing concepts under new names; reuse existing source/destination/config fields where possible
- [ ] Check whether the planned change alters semantics for existing callers, not just whether it compiles
- [ ] For shared infrastructure code, list known current consumers before changing behavior

## Diff Against Plan
- [ ] Re-read the final diff and verify it still matches the planned abstraction
- [ ] Search for duplicate concepts introduced by the change, especially source, destination, status, metadata, and mode fields
- [ ] Search for new blocking waits, sleeps, retries, or polling loops
- [ ] Search for changed shared contracts and verify every known producer/consumer was updated or proven compatible
- [ ] Confirm tests cover old behavior for existing consumers, not only the new happy path
