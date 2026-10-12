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

## Repository Structure

```
.
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
