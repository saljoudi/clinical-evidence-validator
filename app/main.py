"""
Ontology-Driven Clinical Evidence Validator (OCEV)
Main FastAPI application
"""
import uuid
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd

from .validator.stato_loader import StatoLoader
from .validator.fhir_validator import FHIRValidator
from .validator.synthetic_data import SyntheticDataGenerator
from .validator.scorer import EvidenceScorer
from .validator.report_generator import ReportGenerator

app = FastAPI(title="OCEV", description="Ontology-Driven Clinical Evidence Validator")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

# In-memory cache for results (use Redis in production)
results_cache: Dict[str, Dict[str, Any]] = {}

# Initialize components
stato_loader = StatoLoader()
fhir_validator = FHIRValidator()
synthetic_generator = SyntheticDataGenerator()
scorer = EvidenceScorer()
report_generator = ReportGenerator()


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.post("/api/validate/csv")
async def validate_csv(
    file: UploadFile = File(...),
    evidence_type: str = Form(...)
):
    """Validate clinical evidence from CSV file"""
    try:
        # Read CSV
        df = pd.read_csv(file.file)
        
        # Generate synthetic FHIR Evidence resources
        fhir_resources = synthetic_generator.csv_to_fhir(df, evidence_type)
        
        # Validate with SHACL
        task_id = str(uuid.uuid4())
        validation_results = stato_loader.validate_with_shacl(fhir_resources)
        
        # Calculate scores
        integrity_score = scorer.calculate_integrity(validation_results)
        fairness_score = scorer.calculate_fairness(validation_results)
        fhir_score = fhir_validator.validate_fhir_resources(fhir_resources)
        
        overall_score = 0.4 * integrity_score + 0.3 * fairness_score + 0.3 * fhir_score
        
        # Store results
        results_cache[task_id] = {
            "validation_results": validation_results,
            "fhir_resources": fhir_resources,
            "scores": {
                "integrity": integrity_score,
                "fairness": fairness_score,
                "fhir_compliance": fhir_score,
                "overall": overall_score
            },
            "original_data": df.to_dict('records'),
            "evidence_type": evidence_type
        }
        
        return JSONResponse({
            "task_id": task_id,
            "scores": results_cache[task_id]["scores"],
            "summary": validation_results.get("report", "")
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/validate/fhir")
async def validate_fhir(file: UploadFile = File(...)):
    """Validate FHIR Evidence resource directly"""
    try:
        content = await file.read()
        fhir_resources = json.loads(content)
        
        if not isinstance(fhir_resources, list):
            fhir_resources = [fhir_resources]
        
        task_id = str(uuid.uuid4())
        validation_results = stato_loader.validate_with_shacl(fhir_resources)
        
        integrity_score = scorer.calculate_integrity(validation_results)
        fairness_score = scorer.calculate_fairness(validation_results)
        fhir_score = fhir_validator.validate_fhir_resources(fhir_resources)
        
        overall_score = 0.4 * integrity_score + 0.3 * fairness_score + 0.3 * fhir_score
        
        results_cache[task_id] = {
            "validation_results": validation_results,
            "fhir_resources": fhir_resources,
            "scores": {
                "integrity": integrity_score,
                "fairness": fairness_score,
                "fhir_compliance": fhir_score,
                "overall": overall_score
            },
            "evidence_type": "mixed"
        }
        
        return JSONResponse({
            "task_id": task_id,
            "scores": results_cache[task_id]["scores"],
            "summary": validation_results.get("report", "")
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate/synthetic")
async def generate_synthetic(
    n_samples: int = Form(100),
    evidence_type: str = Form("t-test"),
    seed: Optional[int] = Form(None)
):
    """Generate synthetic clinical evidence data"""
    try:
        task_id = str(uuid.uuid4())
        
        # Generate synthetic data
        df, fhir_resources = synthetic_generator.generate_dataset(
            n_samples=n_samples,
            evidence_type=evidence_type,
            seed=seed
        )
        
        # Validate
        validation_results = stato_loader.validate_with_shacl(fhir_resources)
        
        # Score
        integrity_score = scorer.calculate_integrity(validation_results)
        fairness_score = scorer.calculate_fairness(validation_results)
        fhir_score = fhir_validator.validate_fhir_resources(fhir_resources)
        
        overall_score = 0.4 * integrity_score + 0.3 * fairness_score + 0.3 * fhir_score
        
        results_cache[task_id] = {
            "validation_results": validation_results,
            "fhir_resources": fhir_resources,
            "scores": {
                "integrity": integrity_score,
                "fairness": fairness_score,
                "fhir_compliance": fhir_score,
                "overall": overall_score
            },
            "original_data": df.to_dict('records'),
            "evidence_type": evidence_type,
            "synthetic": True
        }
        
        return JSONResponse({
            "task_id": task_id,
            "scores": results_cache[task_id]["scores"],
            "data_preview": df.head().to_dict('records'),
            "summary": validation_results.get("report", "")
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/results/{task_id}")
async def get_results(task_id: str):
    """Get detailed validation results"""
    if task_id not in results_cache:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return JSONResponse(results_cache[task_id])


@app.get("/api/report/{task_id}/pdf")
async def download_pdf(task_id: str):
    """Download PDF report"""
    if task_id not in results_cache:
        raise HTTPException(status_code=404, detail="Task not found")
    
    results = results_cache[task_id]
    pdf_path = report_generator.generate_pdf(task_id, results)
    
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"evidence_validation_{task_id}.pdf"
    )


@app.get("/api/report/{task_id}/json")
async def download_json(task_id: str):
    """Download JSON report"""
    if task_id not in results_cache:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return JSONResponse(results_cache[task_id])


@app.get("/api/report/{task_id}/ttl")
async def download_ttl(task_id: str):
    """Download RDF/TTL report"""
    if task_id not in results_cache:
        raise HTTPException(status_code=404, detail="Task not found")
    
    results = results_cache[task_id]
    ttl_path = report_generator.generate_rdf(task_id, results)
    
    return FileResponse(
        ttl_path,
        media_type="text/turtle",
        filename=f"evidence_validation_{task_id}.ttl"
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "components": ["stato", "shacl", "fhir"]}