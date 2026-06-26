import os
import pandas as pd
from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Query, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
from uuid import uuid4
import io

from tools.validator import validate_data
from tools.frequency_calculator import calculate_frequency
from tools.drift_detector import StatisticalAnalyticsEngine
from tools.feature_ranker import rank_features
from tools.investigation import recursive_investigate
from database import get_db, InvestigationRun
from sqlalchemy.orm import Session
from fastapi import Depends

app = FastAPI(title="Assumption Monitoring Agent API")

# Add CORS middleware to allow Next.js frontend to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
ACTIVE_DATASET_NAME = 'insurance_experience.csv'

def get_active_data_path():
    return os.path.join(DATA_DIR, ACTIVE_DATASET_NAME)

@app.get("/api/datasets")
async def list_datasets():
    try:
        files = [f for f in os.listdir(DATA_DIR) if f.endswith('.csv')]
        return {"datasets": files, "active": ACTIVE_DATASET_NAME}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_dataset(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    file_path = os.path.join(DATA_DIR, file.filename)
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        global ACTIVE_DATASET_NAME
        ACTIVE_DATASET_NAME = file.filename
        return {"status": "success", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dataset/switch")
async def switch_dataset(request: Request):
    global ACTIVE_DATASET_NAME
    data = await request.json()
    filename = data.get('filename')
    
    if not filename or not os.path.exists(os.path.join(DATA_DIR, filename)):
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    ACTIVE_DATASET_NAME = filename
    return {"status": "success", "active": ACTIVE_DATASET_NAME}

def load_data() -> pd.DataFrame:
    path = get_active_data_path()
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Dataset not found. Please generate the data first.")
    return pd.read_csv(path)

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

@app.get("/api/validate")
async def validate_dataset():
    df = load_data()
    return validate_data(df)

@app.get("/api/frequency")
async def get_frequency():
    df = load_data()
    return calculate_frequency(df)

@app.get("/api/drift")
async def get_drift():
    df = load_data()
    if 'Year' in df.columns:
        latest_year = df['Year'].max()
        df_latest = df[df['Year'] == latest_year]
    else:
        df_latest = df
        
    engine = StatisticalAnalyticsEngine()
    metrics = engine.calculate_metrics(df_latest)
    return metrics

@app.get("/api/investigate")
async def investigate_drift():
    df = load_data()
    if 'Year' in df.columns:
        latest_year = df['Year'].max()
        df_latest = df[df['Year'] == latest_year]
    else:
        df_latest = df
        
    engine = StatisticalAnalyticsEngine()
    metrics = engine.calculate_metrics(df_latest)
    
    if not metrics.get("requires_investigation", False):
        return {"status": "No significant drift detected", "drift_metrics": metrics}
        
    tree = recursive_investigate(df_latest, max_depth=3)
    return {"status": "Investigation complete", "drift_metrics": metrics, "tree": tree}

@app.post("/api/agent/run")
async def run_agent(request: Request):
    try:
        data = await request.json()
        api_key = data.get("api_key", "")
        dataset_name = data.get("dataset", ACTIVE_DATASET_NAME)
        
        # Determine the file path for the requested dataset
        import os
        base_path = os.path.join(os.path.dirname(__file__), "data")
        df_path = os.path.join(base_path, dataset_name)
        if not os.path.exists(df_path):
            df_path = os.path.join(base_path, "insurance_experience.csv")
            dataset_name = "insurance_experience.csv"
        
        from agent.planner import create_agent_graph
        graph = create_agent_graph()
        initial_state = {
            "investigation_id": f"INV-{uuid4().hex[:8].upper()}",
            "api_key": api_key,
            "df_path": df_path,
            "dataset_metadata": {"filename": dataset_name},
            "drift_metrics": {},
            "historical_baseline": {},
            "investigation_tree": {},
            "planner_notebook": [],
            "event_reconstruction": "",
            "business_impact": {},
            "decision_options": [],
            "scenario_overrides": {},
            "chat_history": [],
            "final_report": "",
            "investigation_status": "start",
            "messages": []
        }
        
        # Invoke the graph
        result = graph.invoke(initial_state)
        
        # Extract the messages to return a clean status
        logs = [msg.content for msg in result.get("messages", [])]
        
        # Log the run for audit purposes
        from agent.decision_logger import log_investigation_run
        log_investigation_run(result)
        
        # Save to SQLite database
        from database import SessionLocal
        db = SessionLocal()
        try:
            db_run = InvestigationRun(
                id=result.get("investigation_id"),
                dataset_metadata=result.get("dataset_metadata", {}),
                investigation_state=result,
                planner_notebook=result.get("planner_notebook", []),
                investigation_tree=result.get("investigation_tree", {}),
                business_impact=result.get("business_impact", {}),
                decision_support=result.get("decision_options", []),
                final_report=result.get("final_report", "")
            )
            db.add(db_run)
            db.commit()
        except Exception as e:
            print(f"Error saving to DB: {e}")
        finally:
            db.close()
            
        return {
            "status": "success",
            "investigation_id": result.get("investigation_id"),
            "drift_metrics": result.get("drift_metrics", {}),
            "tree": result.get("investigation_tree", {}),
            "business_impact": result.get("business_impact", {}),
            "decision_options": result.get("decision_options", []),
            "planner_notebook": result.get("planner_notebook", []),
            "event_reconstruction": result.get("event_reconstruction", ""),
            "primary_root_cause": result.get("primary_root_cause", ""),
            "explainability_report": result.get("explainability_report", {}),
            "chat_history": result.get("chat_history", []),
            "report": result.get("final_report", ""),
            "logs": logs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    try:
        data = await request.json()
        state = data.get("state", {})
        message = data.get("message", "")
        
        from agent.copilot import chat_with_copilot
        result = chat_with_copilot(state, message)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/investigations")
async def get_investigations(db: Session = Depends(get_db)):
    try:
        runs = db.query(InvestigationRun).order_by(InvestigationRun.timestamp.desc()).all()
        return {
            "investigations": [
                {
                    "id": run.id,
                    "timestamp": run.timestamp,
                    "dataset": run.dataset_metadata.get("filename", "Unknown") if run.dataset_metadata else "Unknown",
                    "risk_level": run.business_impact.get("risk_level", "Unknown") if run.business_impact else "Unknown",
                    "root_cause": run.primary_root_cause or (run.business_impact.get("most_impacted_portfolio", "Unknown") if run.business_impact else "Unknown")
                } for run in runs
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/investigation/{inv_id}")
async def get_investigation_by_id(inv_id: str, db: Session = Depends(get_db)):
    run = db.query(InvestigationRun).filter(InvestigationRun.id == inv_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    # We return the full state dict saved during the run so the frontend can restore it exactly
    return run.investigation_state

@app.get("/api/search")
async def search_investigations(q: str = Query(""), db: Session = Depends(get_db)):
    """Search historical investigations by ID or Root Cause."""
    if not q:
        return {"results": []}
        
    query_str = f"%{q.lower()}%"
    
    # SQLite LIKE is case-insensitive for ASCII
    results = db.query(InvestigationRun).filter(
        (InvestigationRun.id.ilike(query_str)) |
        (InvestigationRun.primary_root_cause.ilike(query_str))
    ).order_by(InvestigationRun.timestamp.desc()).limit(10).all()
    
    matches = []
    for r in results:
        impact = r.business_impact or {}
        matches.append({
            "id": r.id,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            "primary_root_cause": r.primary_root_cause,
            "risk_level": impact.get("risk_level", "Unknown"),
            "dataset": r.dataset_metadata.get("name", "Unknown") if r.dataset_metadata else "Unknown"
        })
        
    return {"results": matches}

@app.get("/api/analytics")
async def get_analytics(db: Session = Depends(get_db)):
    """Aggregate historical investigation data for the analytics dashboard."""
    runs = db.query(InvestigationRun).all()
    
    total_investigations = len(runs)
    total_claims_impacted = 0
    risk_breakdown = {"High": 0, "Medium": 0, "Low": 0, "Unknown": 0}
    root_cause_counts = {}
    
    for r in runs:
        impact = r.business_impact or {}
        
        # Claims Impact
        total_claims_impacted += impact.get("additional_claims", 0)
        
        # Risk Breakdown
        risk = impact.get("risk_level", "Unknown")
        if risk in risk_breakdown:
            risk_breakdown[risk] += 1
        else:
            risk_breakdown["Unknown"] += 1
            
        # Root Cause Breakdown
        rc = r.primary_root_cause or "Unknown"
        if rc not in root_cause_counts:
            root_cause_counts[rc] = 0
        root_cause_counts[rc] += 1
        
    # Sort root causes by frequency
    sorted_rc = [{"name": k, "count": v} for k, v in sorted(root_cause_counts.items(), key=lambda item: item[1], reverse=True)]
    
    recurring_issues = []
    for rc in sorted_rc:
        if rc["count"] > 3 and rc["name"] != "Unknown":
            recurring_issues.append({
                "root_cause": rc["name"],
                "frequency": rc["count"],
                "warning": "This issue has occurred more than 3 times and indicates systemic drift."
            })
        
    return {
        "total_investigations": total_investigations,
        "total_claims_impacted": total_claims_impacted,
        "risk_breakdown": risk_breakdown,
        "root_causes": sorted_rc,
        "recurring_issues": recurring_issues
    }

@app.post("/api/scenario/analyze")
async def analyze_scenario(request: Request):
    try:
        data = await request.json()
        state = data.get("state", {})
        overrides = data.get("overrides", {})
        
        # Load active dataset
        df = load_data()
        if 'Year' in df.columns:
            latest_year = df['Year'].max()
            df = df[df['Year'] == latest_year]
            
        # Apply filters
        for k, v in overrides.get("filters", {}).items():
            if k in df.columns and v:
                df = df[df[k] == v]
                
        # Apply expected frequency multiplier
        freq_mult = overrides.get("expected_frequency_multiplier", 1.0)
        df['Expected_Frequency'] = df['Expected_Frequency'] * freq_mult
        
        # Recalculate impact by injecting into state and running impact node logic
        from agent.business_impact_agent import business_impact_node
        
        # Temporarily save the modified df to a temp path so the node can read it
        import tempfile
        import uuid
        temp_path = os.path.join(tempfile.gettempdir(), f"temp_{uuid.uuid4().hex}.csv")
        df.to_csv(temp_path, index=False)
        
        state["df_path"] = temp_path
        
        new_state = business_impact_node(state)
        
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        return {
            "status": "success",
            "business_impact": new_state.get("business_impact", {})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/report/pdf")
async def generate_pdf_report(request: Request):
    try:
        data = await request.json()
        state = data.get("state", {})
        
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        styles = getSampleStyleSheet()
        
        # Add custom style
        styles.add(ParagraphStyle(name='CustomTitle', parent=styles['Heading1'], fontSize=24, spaceAfter=20, textColor=colors.HexColor('#222222')))
        styles.add(ParagraphStyle(name='CustomH2', parent=styles['Heading2'], fontSize=16, spaceAfter=12, textColor=colors.HexColor('#222222')))
        styles.add(ParagraphStyle(name='CustomNormal', parent=styles['Normal'], fontSize=11, spaceAfter=8, textColor=colors.HexColor('#3f3f3f')))
        
        Story = []
        
        # Metadata
        inv_id = state.get("investigation_id", "Unknown")
        Story.append(Paragraph(f"Investigation Report: {inv_id}", styles['CustomTitle']))
        Story.append(Paragraph(f"Dataset: {ACTIVE_DATASET_NAME}", styles['CustomNormal']))
        Story.append(Spacer(1, 24))
        
        # Executive Summary
        impact = state.get("business_impact", {})
        Story.append(Paragraph("Executive Summary", styles['CustomH2']))
        Story.append(Paragraph(f"Risk Level: {impact.get('risk_level', 'Unknown')}", styles['CustomNormal']))
        Story.append(Paragraph(f"Primary Driver: {impact.get('most_impacted_portfolio', 'Unknown')}", styles['CustomNormal']))
        Story.append(Paragraph(f"Unexpected Claims: +{impact.get('additional_claims', 0)}", styles['CustomNormal']))
        Story.append(Spacer(1, 24))
        
        # Event Inference
        Story.append(Paragraph("AI Event Inference", styles['CustomH2']))
        Story.append(Paragraph(state.get("event_reconstruction", "No inference available."), styles['CustomNormal']))
        Story.append(Spacer(1, 24))
        
        # Decision Options
        Story.append(Paragraph("Decision Support", styles['CustomH2']))
        options = state.get("decision_options", [])
        for opt in options:
            Story.append(Paragraph(f"Action: {opt.get('possible_action')} (Priority: {opt.get('suggested_priority')})", styles['CustomNormal']))
            Story.append(Paragraph(f"Benefits: {opt.get('benefits')}", styles['CustomNormal']))
            Story.append(Paragraph(f"Risks: {opt.get('risks')}", styles['CustomNormal']))
            Story.append(Spacer(1, 12))
            
        doc.build(Story)
        buffer.seek(0)
        
        return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=Investigation_Report_{inv_id}.pdf"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
