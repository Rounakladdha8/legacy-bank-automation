# Design Report

## 1. Architecture

The system separates computer-use automation into two phases: **LLM-driven discovery** and **deterministic replay**.

During discovery, the user provides a natural-language goal such as:

> Find member 12345 and return their savings balance.

The discovery agent opens the LegacyBank web application through Playwright and observes the current browser state. The observation contains the current URL, page title, visible text, and available controls. This information, together with the goal, previous actions, and previously extracted data, is provided to the LLM.

The LLM does not directly control the browser. Instead, it returns one structured action such as `fill`, `click`, `extract`, `finish`, or `escalate`. The discovery executor validates and executes that action through the `WebSurface` abstraction. The page is then observed again, producing an iterative:

```text
Goal
 |
 v
Observe UI
 |
 v
LLM chooses structured action
 |
 v
Execute through WebSurface / Playwright
 |
 v
Observe new UI state
 |
 +--------------------> repeat until finish
```

For the savings-balance goal, discovery learns a workflow approximately equivalent to:

```text
Fill Member ID
      |
Click Search
      |
Click View Savings
      |
Extract Available Balance
```

A successful discovery trace is passed to the compiler. The compiler converts the observed interaction into a versioned capability artifact and replaces discovery-specific values such as `12345` with runtime parameters such as `{{member_id}}`.

Replay then executes that artifact directly:

```text
Natural-language goal
        |
        v
  LLM Discovery
        |
        v
Successful interaction trace
        |
        v
     Compiler
        |
        v
Capability Artifact
        |
        v
Deterministic Replay
```

The primary architectural decision was therefore to use the LLM where flexibility is useful—understanding an unfamiliar UI—and remove it from the repeated execution path once the workflow is known.

This creates a trade-off. Discovery is more adaptable but can be slower and nondeterministic because it depends on an LLM. Replay is faster, cheaper, easier to audit, and more predictable, but it depends on the compiled artifact continuing to match the target surface.

The browser interaction itself is isolated behind `WebSurface`. This keeps Playwright-specific operations separate from discovery reasoning and replay orchestration and provides a natural boundary for supporting other computer-use surfaces in the future.

---

## 2. Artifact schema

A discovered capability is stored as a versioned JSON artifact rather than as an unstructured recording.

The artifact contains:

- `schema_version`
- `capability_id`
- `name`
- `version`
- typed inputs
- typed outputs
- ordered steps
- locator strategies
- retry policies
- checkpoints
- risk classifications
- a success condition
- business outcomes

For example, a discovered input operation is represented conceptually as:

```json
{
  "step_id": "discovered_1_fill",
  "action": "fill",
  "target": {
    "strategy": "label",
    "value": "Member ID"
  },
  "value": "{{member_id}}",
  "retry": {
    "max_attempts": 2,
    "wait_seconds": 1.0
  },
  "checkpoint": null,
  "risk": "safe"
}
```

The important distinction is that the artifact stores **intentional UI operations**, not raw mouse coordinates or a video recording.

Targets can use strategies such as semantic labels, button roles, link roles, or CSS selectors. This makes the artifact more understandable and generally more resilient than absolute screen coordinates.

The artifact also separates discovery-time values from runtime inputs. During discovery, the agent may enter member `12345`. The compiler recognizes that this corresponds to the capability input and stores:

```text
{{member_id}}
```

instead.

That allows one successful discovery to become a reusable capability rather than a recording that only works for one customer.

Pydantic models validate the artifact before execution. This provides a typed contract between discovery, compilation, and replay and prevents malformed artifacts from silently becoming executable workflows.

Versioning is included because both the artifact format and individual capabilities can evolve independently. In a production system, schema migrations and capability-version compatibility would be managed explicitly.

---

## 3. Determinism & error handling

Determinism is achieved primarily by removing the LLM from normal replay.

During discovery, the LLM determines what action should happen next. During replay, the system instead loads an already validated artifact and executes its ordered steps.

Given the same capability version, runtime inputs, target application state, and environment, replay therefore follows the same planned sequence.

Each step can define retry behavior:

```json
{
  "max_attempts": 2,
  "wait_seconds": 1.0
}
```

This distinguishes transient execution problems from immediate hard failures.

Checkpoints provide an additional correctness mechanism. For example, navigation may expect `Member Search` to appear, while the extraction step expects `Available Balance`. A successful Playwright click alone is therefore not necessarily considered evidence that the workflow reached the expected state.

The demo surface includes multiple exceptional states to exercise these distinctions.

Member `88888` simulates a temporary system-busy condition. This represents a recoverable runtime state where retrying may succeed.

Member `77777` produces a permission-denied state. This is treated differently from a transient browser failure because retrying the same operation should not bypass an authorization restriction.

An unknown member ID represents a legitimate business outcome rather than an infrastructure failure. A real automation platform needs to distinguish "automation failed" from "automation successfully discovered that the requested record does not exist."

Member `33333` introduces a manual-verification boundary and is handled through escalation rather than automatic continuation.

Replay also produces structured results containing fields such as status, failure code, step ID, expected state, observed state, and message. Evidence logs and screenshots provide additional debugging and audit information.

UI drift remains a limitation. Semantic locators such as labels and ARIA roles are preferred where possible because they are less brittle than coordinates. However, sufficiently large UI changes can invalidate a compiled capability. A production implementation could detect repeated locator/checkpoint failures, mark the capability unhealthy, and trigger controlled rediscovery rather than allowing the LLM to silently improvise inside deterministic replay.

---

## 4. Heterogeneity & multi-tenant

The current implementation demonstrates one web surface, but the architecture separates surface interaction from capability semantics.

`WebSurface` encapsulates browser-specific operations such as navigation, filling labeled fields, clicking buttons or links, reading text, taking screenshots, and observing available controls.

Conceptually, additional surfaces could implement the same higher-level interface:

```text
Capability / Replay Engine
            |
            v
      Surface Interface
       /      |       \
      /       |        \
 WebSurface Desktop   Other Adapter
```

For example, a desktop surface could translate a `click` operation into an accessibility-tree or computer-use action while preserving the capability/replay model above it.

Heterogeneous surfaces also require locator strategies to remain explicit in the artifact. A web capability may use `role_button`, `label`, or CSS, while another surface could use accessibility identifiers or other stable application-specific references.

For multi-tenant operation, capability definitions should be separated from tenant-specific configuration and credentials. The artifact should describe **what workflow to perform**, while execution context supplies information such as tenant identity, base URL, authorization context, and secrets.

A production design would likely scope capability storage using identifiers similar to:

```text
tenant
  -> application
      -> capability
          -> version
```

This prevents one customer's configuration or credentials from being embedded into another customer's reusable automation.

The current project intentionally keeps this layer lightweight because it runs against a local demonstration application, but the discovery/artifact/replay separation provides a path toward that model.

---

## 5. Escalation & handoff

Not every state should be solved automatically.

The system therefore supports explicit human intervention. Member `33333` demonstrates this by presenting a manual-verification page.

When replay detects this state, it pauses rather than automatically clicking the verification control.

The operator receives an intervention prompt such as:

```text
=== HUMAN INTERVENTION REQUIRED ===
Reason: LegacyBank requires manual verification.

Available commands:
  click <text>
  resume
```

The important design decision is that handoff occurs in the **same browser session**.

The human can interact with the existing page and then issue:

```text
resume
```

to return control to automation.

This preserves cookies, navigation history, application state, and other session context. Restarting the workflow after intervention would be problematic for applications containing multi-step sessions or stateful authentication.

Escalation is also conceptually different from failure. A failure means the system could not safely or correctly complete execution. Escalation means the system intentionally stopped because continuing required human judgment, authorization, or interaction.

A production system could extend this mechanism with remote operator queues, approval workflows, timeout policies, and structured handoff metadata.

---

## 6. Safety

Safety is enforced outside the LLM rather than relying only on prompt instructions.

The `PolicyGuard` defines allowed hosts and allowed action types. The demo is restricted to the local LegacyBank environment:

```text
127.0.0.1:8000
localhost:8000
```

An artifact attempting to navigate to an unauthorized external host is rejected.

Actions are also allowlisted. The current capability supports controlled operations such as:

```text
navigate
fill
click
extract
```

Each step includes a risk classification:

```text
safe
reversible
risky
irreversible
```

Risky and irreversible operations require human approval rather than being automatically executed.

This creates a security boundary between an LLM-generated discovery decision or stored artifact and the actual computer-use executor. Even if discovery produced an inappropriate action, policy enforcement can reject it before execution.

Secrets are not stored in capability artifacts. API credentials are supplied through environment configuration and excluded from source control.

The artifact is also validated before replay, reducing the chance that arbitrary malformed JSON becomes executable automation.

For a production multi-tenant environment, I would additionally isolate browser sessions, encrypt credentials through a secret manager, apply tenant-scoped authorization, sign capability artifacts, restrict network egress, and maintain immutable audit records.

---

## 7. Cuts

I intentionally prioritized a complete vertical slice over implementing every possible automation-platform feature.

The implemented path covers:

```text
natural-language goal
        ->
LLM UI discovery
        ->
real browser execution
        ->
successful trace
        ->
compiled capability artifact
        ->
parameterized deterministic replay
        ->
runtime checks / policy
        ->
human intervention
        ->
structured evidence
```

Several production features were deliberately left out.

First, the system does not implement a general visual locator or computer-vision layer. The demonstration uses DOM and accessibility information because this provides more stable locators and allowed the project to focus on discovery-to-replay architecture.

Second, automatic repair of capabilities after major UI drift is not implemented. I preferred explicit failure/checkpoint detection over allowing replay to silently fall back to unconstrained LLM behavior. A next step would be a controlled rediscovery or repair workflow that creates a new capability version.

Third, tenant management, persistent capability registries, distributed workers, remote human-approval queues, and production secret management are represented architecturally but not implemented.

Fourth, discovery currently targets a constrained action vocabulary rather than attempting arbitrary browser behavior. This reduces flexibility but creates a clearer validation and safety boundary.

Finally, the included LegacyBank application is intentionally a local test surface rather than a production banking integration. It allows deterministic testing of success, retries, permission failures, legitimate business outcomes, and human intervention without depending on an external service.

Given additional time, my next priorities would be stronger capability-health monitoring, automated drift detection, controlled rediscovery/versioning, broader surface adapters, and expanded integration tests.

The core design choice would remain the same: **use an intelligent agent to discover how to perform a task, compile that knowledge into an explicit artifact, and use deterministic execution for repeated production runs.**
