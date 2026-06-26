# Actuarial Assumption Monitoring Agent

The **Actuarial Assumption Monitoring Agent** is a full-stack, enterprise-grade AI workspace designed for actuaries. It automates the complex process of detecting statistical drift in insurance portfolios, isolating root causes, calculating business impact, and generating deterministic explainable reports.

Built with Python, FastAPI, LangGraph, React, Next.js, and SQLite, the application acts as an intelligent co-pilot for actuarial investigations, prioritizing mathematical transparency, auditability, and deterministic rules over LLM hallucinations.

## Key Features

- **Automated Drift Detection:** Ingests insurance datasets, automatically calculates expected baselines vs. actuals (e.g., A/E ratios), and flags statistically significant variance using Z-Scores.
- **Explainable AI Investigation Engine:** Uses a deterministic rules engine and knowledge base (`actuarial_knowledge.json`) to trace macro-level portfolio drift down to the specific micro-segments causing the issue (e.g., Product Type -> Geographic Region).
- **Dual Confidence Metrics:** Displays independent scores for Mathematical Materiality (exposure/variance) and Logic Explainability.
- **Deep Evidence Explorer:** Click into any step of the AI's "Planner Notebook" to see the exact statistical math and rules engine logic that drove the decision.
- **Scenario Lab (What-If Analysis):** Instantly simulate structural portfolio adjustments (e.g., "Shift Expected Frequency +10%") to recalculate financial impacts without rerunning the entire investigation pipeline.
- **Historical Analytics Dashboard:** A dedicated `/analytics` view tracking all prior investigations, calculating risk distribution, and automatically flagging **Systemic Recurring Issues**.
- **Comparison Workspace:** Select any two historical investigations to calculate delta changes in root causes and business impact over time.
- **Deterministic PDF Export:** Generates branded, structured PDF reports of the investigation findings using `ReportLab`.

## Technology Stack

### Backend
- **Framework:** FastAPI
- **AI Orchestration:** LangGraph (State Graphs)
- **Data Processing:** Pandas, NumPy, Scikit-learn
- **Database:** SQLite & SQLAlchemy (for Investigation Memory)
- **Reporting:** ReportLab

### Frontend
- **Framework:** Next.js (React)
- **Styling:** Tailwind CSS, Framer Motion
- **Icons & UI:** Lucide-React, shadcn/ui components
- **Visualizations:** Recharts, Three.js (Fiber)

## Getting Started

### 1. Backend Setup

```bash
# Navigate to the backend directory
cd backend

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server
python main.py
```
The backend API will run on `http://localhost:8000`.

### 2. Frontend Setup

```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Start the Next.js development server
npm run dev
```
The frontend application will be available at `http://localhost:3000`.

## Application Architecture

- **State Machine:** The backend uses `langgraph` to construct a state machine (`InvestigationState`). The graph moves sequentially from `Drift Detection` -> `Feature Ranking` -> `Event Reconstruction` -> `Business Impact Analysis` -> `Decision Support` -> `Report Generation`.
- **Knowledge Base Integration:** Instead of relying on stochastic LLMs for critical business logic, the application uses strict, deterministic matching against `actuarial_knowledge.json`.
- **Global Command Palette:** Hit `Cmd/Ctrl + K` anywhere in the app to access global search, run new investigations, open the AI Copilot, or navigate to analytics.

## License

This project is licensed under the MIT License.
