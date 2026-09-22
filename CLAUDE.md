## Agent routing

The project-manager uses the standard agents by default. The heavy variants run on a larger model and cost more per call, so use them only where these rules say.

### developer-heavy

Use `developer-heavy` instead of `developer` when a task:
- changes concurrency, locking, transactions, or background job coordination
- is a refactor that changes behaviour across more than one module or public interface
- changes authentication, authorisation, session or token handling, or cryptography
- touches any path listed under "Security-critical paths" below
- is an escalation (the standard developer failed the same gate twice for the same finding)

Do not use it for large but mechanical changes (renames, boilerplate, CRUD endpoints that follow an existing pattern, test data).

### security-reviewer-heavy

Use `security-reviewer-heavy` instead of `security-reviewer` when the diff:
- touches any path listed under "Security-critical paths" below, regardless of which developer wrote it
- adds or changes an endpoint, route, or handler that enforces access control
- adds or changes cryptography, token generation or verification, or secret handling
- adds a new third-party dependency that runs at a trust boundary (parsers, auth libraries, crypto libraries)

### Security-critical paths

<!-- Replace with your project's actual paths. -->
- `src/auth/`
- `src/permissions/`
- `src/crypto/`
- `src/api/middleware/`
- Any database migration that changes roles, permissions, or tenant isolation

### Limits

- If `developer-heavy` fails the same gate twice for the same finding, stop and report to the user. Do not keep looping.
- The code-reviewer, tester, and documenter have no heavy variants.

## Feature workflow (mandatory)

Every request for a new feature MUST run this gate sequence, in
order. Do not skip a gate unless the user explicitly waives it for
that request.

1. **Grill** — invoke `mattpocock-skills:grilling` to stress-test the
   idea and requirements before any design work. If grilling surfaces
   new domain terms or an architectural decision, run
   `mattpocock-skills:domain-modeling` (CONTEXT.md / ADR) before
   planning. If a design question can only be answered by trying it,
   run `mattpocock-skills:prototype`; if it needs external facts,
   `mattpocock-skills:research`.
2. **Plan** — enter plan mode; get the plan approved before touching
   code.
3. **Delegate** — hand the approved plan to the `project-manager`
   agent. The PM runs the pipeline: `developer` implements via
   `mattpocock-skills:tdd` (test-first; red-green-refactor) →
   `code-reviewer` gate → `security-reviewer` gate; failed gates
   route fixes back to the `developer` until both PASS.
4. **Review** — run `mattpocock-skills:code-review` against the
   merge-base (Standards axis + Spec axis vs the approved plan);
   route confirmed findings back through the `project-manager`.
5. **Commit** — `tester` runs the full test suite(s) (both repos if
   the change touches both) and commits per repo only when everything
   passes; then `documenter` updates docs (including
   `docs/integration-contract.md` if the handoff changed).
6. **Verify** — invoke `superpowers:verification-before-completion`:
   show fresh test output before claiming the feature is done.

## Bug workflow

Bugs skip Grill/Plan. Diagnose first via
`mattpocock-skills:diagnosing-bugs` (reproduce before you touch
code), then enter the pipeline at **Delegate**: the `developer`
turns the reproduction into a failing test, fixes it, and the same
gates (code-reviewer → security-reviewer → tester → documenter)
apply.

