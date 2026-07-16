import sys

def replace_in_file(file_path):
    with open(file_path, 'r') as f:
        content = f.read()

    # 1. Imports
    if "from logger import get_logger, get_execution_context" not in content:
        import_str = """
from logger import get_logger, get_execution_context
import time
import os

logger = get_logger()
"""
        content = content.replace('from sqlalchemy.orm import Session\nfrom fastapi import Depends\n', 'from sqlalchemy.orm import Session\nfrom fastapi import Depends\n' + import_str)
    
    # 2. Startup Validation & Lifespan
    if "@app.on_event(\"startup\")" not in content:
        startup_str = """
@app.on_event("startup")
async def startup_event():
    logger.info("Initializing Assumption Monitoring Agent...", extra={"engine": "System"})
    
    # Verify environment
    if not os.getenv("GEMINI_API_KEY"):
        logger.warning("GEMINI_API_KEY is not set. AI Planning will fail.", extra={"severity": "High"})
        
    # Verify directories
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        logger.info(f"Created data directory at {DATA_DIR}", extra={"engine": "System"})
        
    # Verify DB
    try:
        from database import engine, Base
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully", extra={"engine": "Database"})
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", extra={"severity": "Critical", "engine": "Database"})
        sys.exit(1)
"""
        content = content.replace('app = FastAPI(title="Assumption Monitoring Agent API")', 'app = FastAPI(title="Assumption Monitoring Agent API")\n' + startup_str)

    # 3. Print replacements
    content = content.replace('print(f"Error saving to DB: {e}")', 'logger.error(f"Error saving to DB: {e}", extra={"engine": "Database", "severity": "High"})')
    
    # 4. Endpoints (/health, /ready, /version)
    health_replacement = """
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

@app.get("/api/ready")
async def readiness_check():
    # Check DB
    db_ok = True
    try:
        from database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
    except:
        db_ok = False
        
    return {
        "status": "ready" if db_ok else "unready",
        "database": "connected" if db_ok else "disconnected",
        "planner": "configured" if os.getenv("GEMINI_API_KEY") else "missing_api_key",
        "engine": "available"
    }

@app.get("/api/version")
async def version_check():
    return {"version": "1.0.0", "status": "production-grade"}
"""
    content = content.replace('@app.get("/api/health")\nasync def health_check():\n    return {"status": "ok"}\n', health_replacement)

    # 5. Adding logging to an endpoint example
    content = content.replace('def run_agent(request: Request):\n    try:', 'def run_agent(request: Request):\n    ctx = get_execution_context()\n    try:')
    content = content.replace('set_dataset_name(dataset_name)', 'set_dataset_name(dataset_name)\n        logger.info("Running AI investigation", extra={"execution_id": ctx["execution_id"], "dataset": dataset_name, "engine": "Agent"})')

    with open(file_path, 'w') as f:
        f.write(content)

replace_in_file('backend/main.py')
