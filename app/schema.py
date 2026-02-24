from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, PositiveInt


# ---------------------------------------------------------------------------
# Metrics extraction (Gemini / LLM pipeline)
# ---------------------------------------------------------------------------

class TextRequest(BaseModel):
    text: str = Field(..., description="The raw text to extract metrics from")


class Metrics(BaseModel):
    income: Optional[PositiveInt] = Field(None, description="The income of the user")
    net_income: Optional[float] = Field(None, description="The net gain/loss of the user")
    emissions: Optional[float] = Field(None, description="The Scope 1 and Scope 2 emissions in metric tons")
    water_usage: Optional[float] = Field(None, description="The water usage in liters")
    quarter: Optional[str] = Field(None, description="The quarter for which the metrics are recorded")


# ---------------------------------------------------------------------------
# Finnish Trade Register (YTJ) company profile
# ---------------------------------------------------------------------------

class CompanyProfile(BaseModel):
    business_id: str = Field(
        ..., description="Finnish Business ID (Y-tunnus), e.g. 0116297-6"
    )
    operating_names: List[str] = Field(
        ..., description="All operating names of the company (current, previous, parallel, auxiliary)"
    )
    main_business_line_code: Optional[str] = Field(
        None, min_length=1, description="Main line of business (TOL 2008 code)"
    )
    registration_date: date = Field(
        ..., description="Company registration date (yyyy-mm-dd)"
    )
    website: Optional[HttpUrl] = Field(
        None, description="Company website URL"
    )


class BusinessId(BaseModel):
    business_id: str = Field(
        ..., description="Finnish Business ID (Y-tunnus), e.g. 0116297-6"
    )