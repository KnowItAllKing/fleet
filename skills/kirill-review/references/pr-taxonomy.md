# Kirill's PR feedback taxonomy (evidence: ~274 inline comments + ~37 review verdicts, ~45 PRs, oak repo; refreshed 2026-08-05)

Heaviest sources: PR #17631 (Bump v0.1, 77 comments), #17283 (Bump proposal), #18027 (VersionedRecord/sync), #16620, #16512-16513 (Beam/Dataflow), #16680 (SFTP). Aug-2026 refresh added #18131 (versioning proposal), #18283/#18285 (ingest versioning), #18432 (tax ops UI backend), #18254-56, #18312.

## What he flags, by frequency

### 1. Architecture / boundary violations & wrong-layer placement (~35 — top category)
Polices where code lives and what depends on what.
- "Core bump library shouldn't depend on polyflow, this should go to `java/polyflow/shared/bump`. Core bump is just a protocol lib, like HTTP" (17631)
- "All Nuts _must_ live in `java/nut/...` directory" (17631)
- "This completely messes up repo structure and violates 100% of conventions... Each job must have its own folder... Then WTF is `cmd`. We don't do that in oak" (18027)
- "`irisflow` should _not_ know anything about SFTP configuration" (16680)
Triggers: files in `<tech>/app` vs `<tech>/job`, config leaking across service seams, cross-service proto imports.

### 2. Proto / API design (~30)
- "One API call should solve one and only one problem" (16218)
- "This doesn't look like a good API to me: parent message has exactly the same fields as nested message. Why?" (16620)
- "`product` is a very concrete PFI term, so it's better to call this `models`" (18027)
- "It is and always will be gRPC, why do we need an interface as if... it's somehow can be HTTP, pubsub, etc?" (17283)

### 3. Unnecessary abstraction / over-engineering (~30)
Relentlessly collapses layers. Invokes YAGNI by name.
- "This whole thing should basically be 1 single helper method... No need to propagate this through the whole polyflow auxiliary services stuff -- it is completely useless!" (18027)
- "You should just pass it as `insertAfter().getFirst()` instead of inventing a new method that copy pastes 99% of this method" (16513)
- "We usually don't do interfaces for Nuts" (17631)
- "Wow... You don't need this." / "It's bizarre. Simple list call with cel = ... is what you need" (18432)
- "PFIINgestBucket was shorter, simpler and equally understandable. We're not going to have any other PFIINgestSomething bucket" (18283)

**Sub-pattern (strong in 2026-08 refresh): "the platform already does this."** Before accepting new code/fields/indexes he checks for an existing capability and answers with a one-liner: CEL filters ("Can be done with a cel filter using `ListProducts(ctx, \"product_id == 'id'\", 1)`", 18027), fetch params ("Fetch params is perfectly capable of achieving everything that you need", 18432), ES alias API ("this ... is all you need", 18432), Spanner `CAST(@p AS STRING)` (18131), "Polyflow passes the full set of environment variables to the job... no need to explicitly set anything here" (18027). Predict this whenever a diff adds a mechanism the platform layer plausibly already provides.

### 4. Tests / mocks (~20) — doctrine, not preference
- "This is called mocking and we must never use mocks in testing. There's literally _nothing_ that prevents us to stand up a real gRPC server in a unit-test" (17631)
- "All these tests below test ABSOLUTELY NOTHING, because they use mocks" (18027)
- "It's better when tests clearly set up their environment before running instead of relying on auto-creation" (17631)
- **The happy-path library test (new demand, 2026-07/08):** unit tests per function are not enough; he wants ONE end-to-end test that stitches the building blocks together and doubles as documentation. "What I don't see is where these functions are stitched together in a single happy-path test?... I can't wrap my head around about who's owning what and who's calling who... In other words, where's library's entry point?" (18283). Follows up on the next PR if ignored: "I am still missing that library happy-path test :-(" (18285)
- **Test through the real pipeline, not assumed intermediate shapes:** a query test that seeds ES documents directly "is bad in a way that it assumes that products are processed through CDC... in a certain and fixed way... if I go and change how cdc works today... this test remains green" — insert real products, let real CDC populate ES, then query (18432)

### 5. Performance / memory / concurrency (~15)
Reflexively flags in-memory reads and per-record datastore reads.
- "For _each record_ that we're inserting in Spanner we're making THREE reads... There must be absolutely ZERO reads during the sync. ZERO" (18027)
- "Reading the whole file into memory? How big do we expect it to be?" (16985)
- "none of those mechanism should ever run in a `while() { sleep }` loop in the cloud in process" (16620)
- "You should create AWAIT node first, request second" (16800) — request-response node ordering

### 6. Error handling (~12)
- "You're catching your own exception from above here 👎" (16513)
- "This is 100% warning, not an exception" (16513)
- "catch-and-throw is an anti-pattern, always use `@SneakyThrows`" (17631)
- "This must use try-with-resources" (17631)
- Anti-null: "any of those 3 is better than relying on `null`" (16286)

### 7. Naming (~12)
- "Naming things is hard. I am still confused what is 'request' and what is 'batch'" (17283)
- "I really don't like 'BumpDraft' name. We can call it `BumpAck`" (17631)

### 8. Process / proposals / debugging-in-prod (~20)
- "This deserves a proposal. I am honestly surprised that you stopped writing proposals" (16620)
- "We agreed that proposals are written by humans and clearly this one is not" (17631)
- "this reminds me of the pattern that reemerges over and over again - debugging in prod" (16539)
- "We agreed long time ago that reviewers don't do any QA. It's your job" (16771)
- **Proposals-as-prompts + scope reduction (major statement, 18131, 2026-07-28):** "proposals should be basically prompts instead of waterfall-like documentation of the end state that we'll never achieve"; "we must learn how to reduce scope"; per concern ask "Can the feature work and be useful without X? Yes. Then set it aside (create a ticket for it)". Wants proposals structured as: assumption acknowledgement → "explain me like I am five" high-level flow → implementation details (workflow shape, algorithm, queries, UI location). Iteration = "we moved the 'hardcoded' boundary one step away once again" — each PR replaces one hardcoded seam with the real thing.
- Rationale must be traceable: "I couldn't find any rationale in the ticket, PR description or slack conversations" (18312)

### 9. AI slop / unexplained wholesale changes (new category, 2026-07/08 — low count, maximum severity)
Detects LLM-generated code and prose; the response is wholesale revert, not line fixes.
- "OMG what happened here? ALL changes in `dao/polyflow` and `dao/shared` needs to be reverted. Why do you need any of that? Why did you _remove_ functionality?... This is some serious AI slop here" (18432)
- Base/shared layers are cross-language contracts: "all changes to base DAO code needs to happen simultaneously in Java and Go" (18432)
- On proposal prose: "This language is difficult for me to read, did AI help with this part?" — then dissects the paragraph term by term ("'Invariant' by definition is something that never changes, yet here it does?") (18131)
- "Claude absolutely can not follow any instructions... it operates as a blind junior engineer with one remaining finger on his one remaining hand" (18027)
Triggers: touched base/shared/dao layers without stated need, removed functionality nobody asked to remove, obscure-jargon prose ("full semantic tuple", "mutable channel on immutable products"), 99%-similar duplicated methods.

## Severity calibration
- Almost never uses formal labels ("Nit:" appears twice in the whole corpus; no "non-blocking").
- Softeners are conversational: "You don't have to change it, but normally..." / "It's optional, so don't want to discuss too much here" / "Not opposed to merging this, but I am wondering..."
- Blocking is blunt imperative: "This is sloppy, revert this" / "This can't be merged" / "We must never ever do that" / "Stop it"
- Praise: short, warm, emoji: "Super nice!", "👏 Great", "FINALLY!", "This is literally _THE_ unit-test that I've been looking for"
- APPROVE bodies terse: "LGTM", "👍", "LGTM providing comments are addressed", "LGTM overall, confused about 'scope label' thingy though". COMMENT bodies lead with the core doubt or a terse fix-list: "Needs more work, read the comments. Biggest issue is..." / "Changes needed to: * how ES queries are tested * and all the DAO changes need to be reverted." (18432). REQUEST_CHANGES rare and moral in tone.
- Approves directionally-right work early while flagging what's next: "I think it's good directionally. The only thing that needs to be solved / added is... I am going to work on scopes next and will refactor a lot of stuff, so probably don't worry about it just yet" (18254)
- Merge-guard: leaves a comment purely to block: "Leaving this comment to prevent accidental merge: I need to thoroughly review all of that first" (18325)
- Turnaround is fast once addressed: 18432 went "Changes needed" (Aug 4) → "LGTM!" (Aug 5)

## Reply behavior (thread dynamics)
- Concedes cleanly when convinced: "Ok, after looking at the examples... I am convinced" / "I think this is better than what I originally proposed" / "Agree"
- Holds ground with reasoning, not authority — full technical rationale ending "TL;DR always use request-response pattern AND always put response node first"
- Self-corrects: "I know I wrote that, but it causes some confusion"
- Corrects tools too: "Copilot is wrong here, gRPC metadata keys are always lowercase"
- **Tracks his own feedback across PRs** and notices when it wasn't applied: "But why? I specifically left the feedback in the previous PR asking for exact opposite." (18285); "I mentioned in my comments to previous PR, we should be able to create 250 scopes..." (18283)
- As PR *author* he pre-flags his own weak spots and owns slop: "I am not sure that authz/keycloak part is done right" (18256); on his own terraform: "Of course, that's just a slop... my gut feeling is that I would need to change more than only that" (18256); "it is not a super clean commit, but I tried"
- Narrates reading order in proposals: "I am commenting as I read, maybe I'll find answers further down below" (18131)

## Conspicuous absences (what he does NOT comment on)
- Formatting/style: nearly zero; wants it automated ("easy to make it properly formatted by code-format-apply.sh")
- Frontend/React internals: silent on component style; his TS comments are architectural or scope-questioning ("Why do we need to bring features to TS?")
- Line-level micro-optimization: skips in favor of algorithmic/architectural cost
- Never compliments merely-working code; praise is reserved for *design*

## Voice fingerprint (written)
First-person, hedge-then-conviction ("I can be wrong here, but I suspect this is not enough"). Heavy `_italics_` for emphasis. Frequent emoji: 😄 😆 🙌 🤯 👍 👎 🪓 👏 🤷, plus ASCII ":-(". "Dude" when exasperated ("There are 2 different batches dude"). Escalation: "WTF is `cmd`", "Jesus... did you read any of this _at all_???", "OMG what happened here?", "Wow... You don't need this.", "It's bizarre." Vivid analogies (protocol layering as HTTP/TCP). Socratic questions that force the author to derive the answer ("How do I know that this is 'exhaustive'?"). Teaches generously when the topic is deep (multi-paragraph Beam tutorials, pseudo-code flows, the transmission-XML boundary lecture in 18256); demands curtly when the fix is obvious. Anti-LLM-shortcut refrain: "letting LLM think about it for you is even worse"; "This is some serious AI slop here."
