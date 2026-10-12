# Multi-Agent Dispute Resolution (Ryde / Digital Native Track)

A prototype multi-agent system for resolving ride-hailing disputes between riders and drivers. The workflow reports a dispute, notifies the other party, gathers evidence, and submits both cases to an impartial Judge Agent.

- Solid arrows: workflow progression
- Dashed teal arrows: evidence / policy retrieval

## Workflow Architecture

```
1. Dispute filed
   Rider or driver submits claim + trip reference
   Example: overcharge

        ↓

2. Case controller (proposed)
   Open case from first report
   Notify the other party
   Collect both case reports

        ↓

3. Rider Advocate        3. Driver Advocate
   • Gather all relevant evidence   • Gather all relevant evidence
   • Build and submit rider case   • Build and submit driver case
   • Cite company policy            • Cite company policy

        ↘                ↙

4. Judge Agent
   • Review both cases
   • Weigh the evidence
   • Apply company policy
   • Rule + score confidence
   • Explain the reasoning

        ↓

5. Share outcome
   • Publish the ruling
   • Recommended action: refund / compensation / no action
   • Notify rider and driver
```

**Case packet exchanged between agents:**
- First report activates one advocate.
- The other party is notified to activate their advocate.
- Both gather evidence and submit cases to the Judge.
- Notifications and exchanges are shown in the log / UI.

> **Note:** The case controller is proposed; only the three core agents (Rider Advocate, Driver Advocate, Judge Agent) are required.

## Shared Evidence & Policy Layer

Both advocates and the Judge pull from a shared layer of text and structured data. For the MVP, mock data and APIs are used where real sources are unavailable.

| Category | Contents |
|----------|----------|
| **GPS & telemetry** | Actual vs. optimal route, stops, duration, timestamps |
| **Chat logs** | Agreements and disagreements, sentiment, threats |
| **Payment & fares** | Fare breakdown, surge pricing, promo code usage |
| **Behavior profiles** | Past disputes, rating patterns, account age |
| **Company policy** | Rules used by both advocates and the impartial Judge |

The current repository stores the shared company policy in `database/ryde_trips.db` (`dispute_policy` and `policy_sources` tables) alongside the mock trip data (`rider_trips` and `driver_trips` tables).

## Optional Overwatch Workflow

```
Judge confidence below threshold
        ↓
Human reviews full case
        ↓
Publish reviewed outcome
        ↓
Overrides update precedent KB
```

**Additional optional agents:**
- **Evidence Collection Agent** — with image analysis
- **Fraud Agent** — escalates findings to the Judge
- **Policy & Precedent Agent** — assists the Judge with rule interpretation
- **SLA & Routing Manager** — case prioritization

## Demo Scope

- Primary focus: route deviation + no-show / cancellation charge disputes
- MVP output: a recommended action (refund, compensation, or no action)
- Payment execution is an implementation choice left to downstream systems

## Backend — Multi-Agent System

The backend implements the three core agents from the architecture, plus a case controller orchestrator. Agents communicate through an in-process **MCP (Model Context Protocol) message bus**.

### Agent Roles

| Agent | Role |
|-------|------|
| **Rider Advocate** | Gathers evidence supporting the rider, builds the rider's case, cites company policy, submits to the Judge |
| **Driver Advocate** | Gathers evidence supporting the driver, builds the driver's case, cites company policy, submits to the Judge |
| **Judge Agent** | Reviews both cases, weighs the evidence, applies company policy, issues a ruling with confidence score and reasoning |
| **Case Controller** | Orchestrates the workflow: opens the case, notifies the other party, assigns advocates, collects the ruling, publishes the outcome |

### MCP Communication

All inter-agent communication flows through the MCP bus as typed messages:

```
Case Controller
  ├─ CASE_OPENED (broadcast) ──────► all agents
  ├─ PARTY_NOTIFIED (broadcast) ───► all agents
  ├─ CASE_ASSIGNED ──► Rider Advocate
  ├─ CASE_ASSIGNED ──► Driver Advocate
  │
  Rider Advocate                      Driver Advocate
  ├─ evidence collection               ├─ evidence collection
  ├─ policy retrieval                  ├─ policy retrieval
  └─ CASE_SUBMITTED ──► Judge          └─ CASE_SUBMITTED ──► Judge
                                          │
                          Judge Agent ◄──┘
                          ├─ weigh evidence
                          ├─ apply policy
                          ├─ determine ruling
                          ├─ assess confidence
                          └─ RULING_ISSUED ──► Case Controller
                                                   │
                                                   └─ CASE_CLOSED (broadcast)
```

### Shared Evidence & Policy Layer

All agents read from `database/ryde_trips.db` via the shared data layer:

| Category | Source |
|----------|--------|
| **GPS & telemetry** | Trip route, pickup, destination, timestamps |
| **Chat logs** | `chat_history` column — parsed for sentiment signals |
| **Payment & fares** | `amount_sgd`, `status` |
| **Behavior profiles** | Aggregated trip history per rider/driver |
| **Company policy** | `dispute_policy` + `policy_sources` tables (16 rules, 10 sources) |

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/dispute` | File a dispute → runs full agent workflow → returns ruling + transcript |
| `POST` | `/api/dispute/quick` | Quick dispute with query params |
| `GET` | `/api/agents` | List registered agents and their roles |
| `GET` | `/api/trips/rider` | List all rider trips |
| `GET` | `/api/trips/driver` | List all driver trips |
| `GET` | `/api/trips/{trip_id}` | Get a specific trip |
| `GET` | `/api/policy` | List all dispute policy rules with sources |
| `GET` | `/api/health` | Health check |

### Backend Development

```bash
cd backend
pip install -r requirements.txt

# Run the API server
python main.py
# or: uvicorn main:app --reload --port 8000
```

### Example: Filing a Dispute

```bash
curl -X POST http://localhost:8000/api/dispute \
  -H "Content-Type: application/json" \
  -d '{
    "trip_id": "20261011-180500-000001",
    "filed_by": "rider",
    "issue_category": "Fare / pricing dispute",
    "complaint_text": "I was charged S$31.40 but the quote was S$27.00."
  }'
```

Response includes:
- `ruling.action` — `refund`, `compensation`, `no_action`, or `review`
- `ruling.in_favor_of` — `rider`, `driver`, `neither`, or `pending`
- `ruling.adjustment_sgd` — recommended monetary adjustment
- `ruling.confidence` — 0.0 to 1.0
- `ruling.needs_human_review` — `true` if confidence < 0.85 or adjustment > S$50
- `ruling.reasoning` — step-by-step explanation
- `ruling.policy_rules_applied` — list of policy rule IDs (PUB/SIM)
- `mcp_transcript` — full message log of all inter-agent communication

### Overwatch Workflow

When the Judge's confidence falls below 0.85 or the recommended adjustment exceeds S$50, the case is flagged for human review:

```
Judge confidence < 0.85  ──►  needs_human_review = true
Adjustment > S$50        ──►  needs_human_review = true
```

Safety incidents (e.g. "Safety / misconduct dispute") are always escalated per policy rule SIM05.

## Repository Structure

```
.
├── backend/                           # FastAPI multi-agent backend
│   ├── main.py                        # API endpoints (dispute, trips, policy)
│   ├── mcp_bus.py                     # MCP message bus for inter-agent comms
│   ├── data_layer.py                  # Shared evidence & policy data access
│   ├── base_agent.py                  # Base agent class
│   ├── rider_advocate.py              # Rider Advocate agent
│   ├── driver_advocate.py             # Driver Advocate agent
│   ├── judge_agent.py                 # Judge Agent
│   ├── case_controller.py             # Case orchestrator
│   └── requirements.txt
├── frontend/                          # React + Vite UI
│   ├── src/
│   │   ├── App.jsx                    # Activity / trip list + Help Center
│   │   ├── trips-data.json            # Exported SQLite data used by the UI
│   │   └── ...
│   └── dist/                          # Production build
├── database/
│   ├── ryde_trips.db                  # SQLite database (rider, driver, policy)
│   └── ryde-dispute-policy-reference.docx
└── .github/workflows/
    └── deploy.yml                     # GitHub Pages deployment
```

## Live Demo

The frontend is deployed on GitHub Pages:

**[https://sprindy.github.io/multi-agents-dispute-resolution/](https://sprindy.github.io/multi-agents-dispute-resolution/)**

Use the **rider / driver toggle** to switch between the two trip lists. Tap a trip card to see details, then tap **Report an issue** to open the Help Center. The issue categories change based on the current role.

## Development

```bash
# Install dependencies and run locally
cd frontend
npm install
npm run dev

# Build for production
npm run build
```

## Sources

- Architecture inspired by the Ryde / Digital Native Track workflow.
- Company policy references are paraphrased from official Ryde help pages and augmented with simulated demo logic; see `database/ryde-dispute-policy-reference.docx` and the `policy_sources` table in `database/ryde_trips.db`.
