from fastapi import FastAPI, Query, HTTPException
from backend.core.gatherer import run_osint_analysis
from backend.core.models import DigitalFootprintReport

app = FastAPI(
    title="OSINT-PRO Python Core Engine",
    description="Exposes the asynchronous OSINT gatherer logic. Designed to be proxied by the Go Gateway on port 8080."
)

@app.get("/analyze", response_model=DigitalFootprintReport)
async def analyze_target(target: str = Query(..., description="The domain or username to analyze.")):
    """
    Triggers the multi-source OSINT analysis for a given target.
    """
    if not target or len(target) < 3:
        raise HTTPException(status_code=400, detail="Target must be at least 3 characters long.")
    
    try:
        report = await run_osint_analysis(target)
        return report
    except Exception as e:
        
        print(f"Internal Python Engine Error: {e}")
        raise HTTPException(status_code=500, detail="Internal analysis engine error.")