# LegacyBank Computer-Use Automation System

An end-to-end computer-use automation system that converts a natural-language goal into a reusable, deterministic capability.

The system uses an LLM during **discovery** to inspect and operate a live UI. Once a successful workflow is discovered, the interaction trace is compiled into a structured capability artifact. Future executions **replay the artifact deterministically**, without using the LLM for action selection.

The repository also includes a local FastAPI-based LegacyBank application used to demonstrate successful execution, recoverable failures, hard failures, business outcomes, policy enforcement, and human-in-the-loop intervention.

---

## System Overview

```text
Natural-Language Goal
        |
        v
+-----------------------+
|   Discovery Agent     |
|   LLM Decision Loop   |
+-----------+-----------+
            |
            | observe -> decide -> act
            v
+-----------------------+
|      WebSurface       |
| Playwright + Browser  |
+-----------+-----------+
            |
            v
+-----------------------+
| LegacyBank Demo App   |
| FastAPI + HTML UI     |
+-----------------------+

Successful Discovery
        |
        v
+-----------------------+
| Capability Compiler   |
+-----------+-----------+
            |
            v
+-----------------------+
| Versioned JSON        |
| Capability Artifact   |
+-----------+-----------+
            |
            v
+-----------------------+
| Deterministic Replay  |
| No LLM Action Choice  |
+-----------+-----------+
            |
            +----> Policy Guard
            +----> Checkpoints / Retries
            +----> Human Intervention
            +----> Evidence / Logs
```

## Key Design Idea

The architecture separates **discovery** from **execution**.

During discovery, the LLM receives information about the current browser state, including:

- the user's natural-language goal,
- current URL and page title,
- visible page text,
- observable UI controls,
- previous actions,
- previously extracted data.

The LLM returns one structured action at a time, such as:

- `fill`
- `click`
- `extract`
- `finish`
- `escalate`

The selected action is executed against the real browser using Playwright. The application is then observed again and the loop continues.

For the example goal:

```text
Find member 12345 and return their savings balance.
```

discovery determines a workflow similar to:

```text
Fill "Member ID"
        |
        v
Click "Search"
        |
        v
Click "View Savings"
        |
        v
Extract "Available Balance"
        |
        v
Finish
```

After successful discovery, the trace is compiled into a reusable capability artifact.

The concrete discovery value:

```text
12345
```

is converted into the runtime parameter:

```text
{{member_id}}
```

This means subsequent executions can reuse the same capability with different member IDs.

The important architectural distinction is:

> **Use the LLM to discover the workflow; use deterministic software to repeat it.**

---

## Requirements

The project was developed using:

- Python 3.11
- FastAPI
- Uvicorn
- Playwright
- Pydantic
- OpenAI API access for live LLM discovery
- pytest

Replay of an already-discovered capability does not require the LLM to choose browser actions.

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/Rounakladdha8/legacy-bank-automation.git
cd legacy-bank-automation
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

If `requirements.txt` is included:

```bash
pip install -r requirements.txt
```

Alternatively, the core dependencies can be installed directly:

```bash
pip install fastapi uvicorn jinja2 playwright pydantic openai python-dotenv pytest
```

### 4. Install Playwright Chromium

```bash
python -m playwright install chromium
```

### 5. Configure the API key

Live LLM-based discovery requires an OpenAI API key.

Create a `.env` file in the repository root:

```text
OPENAI_API_KEY=your_api_key_here
```

Do **not** commit the `.env` file or API credentials to Git.

The repository's `.gitignore` excludes local secret/configuration files.

### Running Without a Live LLM Service

A previously generated capability artifact is included under:

```text
artifacts/
```

Therefore, the deterministic replay path can be exercised without performing a new live discovery run.

The local LegacyBank FastAPI application still needs to be running because replay operates against the browser UI.

---

# Demo Path

The following is the exact demonstration path for discovering and replaying the savings-balance capability.

## 1. Start the LegacyBank Application

From the repository root:

```bash
uvicorn app.main:app --reload
```

The local application runs at:

```text
http://127.0.0.1:8000
```

Keep this terminal running.

---

## 2. Run LLM-Based Discovery

Open another terminal and activate the virtual environment.

Run:

```bash
python -m automation.discovery
```

The demonstration goal is:

```text
Find member 12345 and return their savings balance.
```

The discovery agent repeatedly performs:

```text
Observe UI
    |
    v
Ask LLM for next structured action
    |
    v
Validate action
    |
    v
Execute with Playwright
    |
    v
Observe resulting UI
```

For the normal member flow, discovery should determine:

```text
fill Member ID
        ->
click Search
        ->
click View Savings
        ->
extract Available Balance
        ->
finish
```

A successful discovery generates:

```text
artifacts/discovered_get_savings_balance.json
```

The discovered workflow is parameterized so that:

```text
12345
```

becomes:

```text
{{member_id}}
```

---

## 3. Replay the Resulting Artifact

After discovery has produced the capability artifact, run:

```bash
python -m automation.replay
```

Replay loads the saved artifact and executes its steps deterministically.

The LLM does **not** choose each action again during replay.

A successful replay returns a structured result similar to:

```json
{
  "status": "success",
  "code": null,
  "outputs": {
    "savings_balance": "$7481.22"
  },
  "step_id": null,
  "expected": null,
  "observed": null,
  "message": "Replay completed successfully."
}
```

The exact balance depends on the member used for the replay.

---

# Capability Artifact

Discovery is compiled into a versioned JSON capability.

The generated artifact contains information such as:

- schema version,
- capability ID,
- capability version,
- typed inputs,
- typed outputs,
- ordered execution steps,
- target locator strategies,
- parameterized runtime values,
- retry policies,
- checkpoints,
- risk classifications,
- success conditions.

A discovered fill step resembles:

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

An extraction step uses a stable locator such as:

```json
{
  "target": {
    "strategy": "css",
    "value": "#savings-balance"
  }
}
```

The artifact is validated against Pydantic models before being treated as an executable capability.

---

# Deterministic Replay

The replay engine executes the compiled artifact rather than asking the LLM to rediscover the workflow.

This provides several benefits:

- lower runtime variability,
- lower LLM usage,
- easier auditing,
- explicit retry behavior,
- explicit checkpoints,
- structured failure information,
- reusable parameterized capabilities.

Replay therefore acts more like a conventional workflow engine once discovery has produced a valid capability.

---

# Human-in-the-Loop Intervention

Member ID:

```text
33333
```

demonstrates a human-verification boundary.

The application presents:

```text
Manual Verification Required
```

The automation does not silently bypass the verification step.

Instead, replay pauses and reports:

```text
=== HUMAN INTERVENTION REQUIRED ===
Reason: LegacyBank requires manual verification.

Available commands:
  click <text>
  resume
```

The human operator can complete the required UI action in the existing browser session.

After the intervention is complete:

```text
resume
```

returns control to the automation.

This preserves browser/session state instead of restarting the workflow.

---

# Runtime Scenarios

The LegacyBank demo application includes multiple runtime states so the automation can be exercised beyond a single happy path.

| Member ID | Scenario |
|---|---|
| `12345` | Normal successful member lookup |
| `33333` | Manual verification / human intervention |
| `77777` | Permission denied / hard failure |
| `88888` | Temporary recoverable busy state |
| Unknown ID | Legitimate member-not-found business outcome |

These scenarios demonstrate the difference between:

- successful execution,
- recoverable runtime conditions,
- hard failures,
- legitimate business outcomes,
- human-intervention requirements.

---

# Retry and Error Handling

Capability steps include explicit retry configuration.

Example:

```json
{
  "retry": {
    "max_attempts": 2,
    "wait_seconds": 1.0
  }
}
```

The replay engine can retry recoverable operations rather than treating every unexpected runtime state as an immediate terminal failure.

Checkpoints are also used to verify expected UI state.

For example:

```json
{
  "checkpoint": {
    "type": "text_present",
    "expected": "Available Balance"
  }
}
```

This helps prevent the system from assuming an action succeeded simply because a browser operation completed.

---

# Policy and Safety

Automation execution is constrained by a policy layer.

The current policy guard restricts:

- allowed hosts,
- allowed action types,
- execution of risky operations.

The demo is restricted to:

```text
127.0.0.1:8000
localhost:8000
```

Supported replay actions are explicitly allowlisted.

Risk levels distinguish operations such as:

```text
safe
reversible
risky
irreversible
```

Risky or irreversible operations require human approval instead of being executed automatically.

API credentials are supplied through environment configuration and are not stored inside capability artifacts.

---

# Evidence and Auditability

Replay produces structured evidence under:

```text
evidence/
```

Evidence can include:

- JSONL execution logs,
- screenshots captured around relevant execution states.

This provides an audit trail for understanding what happened during a replay and diagnosing failures.

---

# Tests

Run the automated tests with:

```bash
python -m pytest -v
```

The test suite covers the capability model and policy behavior, including:

- artifact schema validation,
- required member input,
- required savings-balance output,
- member ID parameterization,
- success-condition validation,
- allowed localhost execution,
- external-domain blocking,
- allowed safe actions,
- unknown-action blocking,
- human approval requirements for risky actions.

At the time of submission, the core test suite passes:

```text
10 passed
```

---

# Project Structure

```text
legacy-bank-automation/
|
|-- app/
|   |-- data.py
|   `-- main.py
|
|-- automation/
|   |-- compiler.py
|   |-- discovery.py
|   |-- discovery_executor.py
|   |-- discovery_llm.py
|   |-- discovery_models.py
|   |-- intervention.py
|   |-- logger.py
|   |-- manual_flow.py
|   |-- models.py
|   |-- policy.py
|   |-- replay.py
|   `-- surface.py
|
|-- artifacts/
|   |-- discovered_get_savings_balance.json
|   `-- get_savings_balance.json
|
|-- evidence/
|
|-- static/
|   `-- styles.css
|
|-- templates/
|
|-- tests/
|   |-- test_models.py
|   `-- test_policy.py
|
|-- .gitignore
|-- pytest.ini
|-- README.md
`-- REPORT.md
```

## Component Responsibilities

### `automation/discovery.py`

Runs the discovery loop:

```text
observe -> LLM decision -> execute -> observe
```

and sends a successful trace to the compiler.

### `automation/discovery_llm.py`

Provides the LLM with the goal and observed UI state and requests a structured next action.

### `automation/discovery_executor.py`

Translates a discovery action into a real browser operation and records the concrete locator that succeeded.

### `automation/surface.py`

Provides the browser abstraction over Playwright, including observation and UI operations.

### `automation/compiler.py`

Transforms a successful discovery history into a validated, parameterized capability artifact.

### `automation/replay.py`

Executes a saved capability deterministically.

### `automation/policy.py`

Enforces host, action, and risk restrictions.

### `automation/intervention.py`

Supports human handoff when automation should not proceed independently.

### `automation/logger.py`

Records replay evidence for auditability and debugging.

---

# Design Report

The detailed system-design discussion is provided in:

```text
REPORT.md
```

The report covers the required design areas:

1. Architecture
2. Artifact schema
3. Determinism & error handling
4. Heterogeneity & multi-tenant
5. Escalation & handoff
6. Safety
7. Cuts

The central design decision is to separate flexible LLM-based **discovery** from reliable **deterministic replay**, allowing successful UI workflows to become reusable automation capabilities.
