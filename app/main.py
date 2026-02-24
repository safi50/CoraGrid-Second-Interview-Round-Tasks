import logging

from fastapi import FastAPI, HTTPException

from extract_company_data import fetch_company_data, parse_company_profile
from structure_output import structure_output
from schema import CompanyProfile, Metrics, TextRequest

logger = logging.getLogger(__name__)

app = FastAPI(title="Company Profile API")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/company", response_model=CompanyProfile)
async def get_company_profile(business_id: str):
    raw_data = await fetch_company_data(business_id)
    if not raw_data:
        raise HTTPException(status_code=404, detail="Failed to retrieve company data")

    profile = parse_company_profile(raw_data)
    if not profile:
        raise HTTPException(status_code=422, detail="Failed to parse company profile from data")

    return profile.model_dump()


@app.post("/extract", response_model=Metrics)
async def extract(request: TextRequest):
    result = await structure_output(request.text)
    if not result:
        raise HTTPException(status_code=422, detail="Failed to extract metrics from provided text")

    return result

