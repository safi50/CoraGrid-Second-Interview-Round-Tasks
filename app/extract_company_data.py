import asyncio
import logging
import os
from datetime import date
from typing import List, Optional

import httpx
from dotenv import load_dotenv

from schema import CompanyProfile

load_dotenv()

logger = logging.getLogger(__name__)

_API_URL = os.getenv("YTJ_API_URL", "https://avoindata.prh.fi/opendata-ytj-api/v3/companies")
_API_KEY = os.getenv("YTJ_API_KEY")
_HEADERS = {"Authorization": f"Bearer {_API_KEY}"} if _API_KEY else {}


async def fetch_company_data(business_id: str) -> dict:
    """Fetch raw company data from the YTJ open data API by Business ID."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url=_API_URL,
                headers=_HEADERS,
                params={"businessId": business_id},
            )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        logger.error("HTTP error fetching company data: %s - %s", e.response.status_code, e.response.text)
    except httpx.RequestError as e:
        logger.error("Request error fetching company data: %s", e)
    except Exception as e:
        logger.error("Unexpected error fetching company data: %s", e)
    return {}


def parse_company_profile(data: dict) -> Optional[CompanyProfile]:
    """Map a raw YTJ API response to a CompanyProfile model."""
    try:
        companies = data.get("companies", [])
        if not companies:
            logger.warning("No companies found in API response")
            return None

        company = companies[0]

        business_id: str = company["businessId"]["value"]

        operating_names: List[str] = [
            entry["name"]
            for entry in company.get("names", [])
            if entry.get("name")
        ]

        main_business_line_code: Optional[str] = (
            company["mainBusinessLine"].get("type")
            if company.get("mainBusinessLine")
            else None
        )

        registration_date_raw = company.get("registrationDate")
        if not registration_date_raw:
            logger.warning("registrationDate missing for business_id=%s", business_id)
            return None
        registration_date = date.fromisoformat(registration_date_raw)

        website: Optional[str] = (
            company["website"].get("url") or None
            if company.get("website")
            else None
        )

        return CompanyProfile(
            business_id=business_id,
            operating_names=operating_names,
            main_business_line_code=main_business_line_code,
            registration_date=registration_date,
            website=website,
        )
    except KeyError as e:
        logger.error("Missing expected field in company data: %s", e)
    except ValueError as e:
        logger.error("Value error parsing company data: %s", e)
    except Exception as e:
        logger.error("Unexpected error in parse_company_profile: %s", e)
    return None


async def _main() -> None:
    logging.basicConfig(level=logging.INFO)
    sample_id = "0116297-6"
    raw_data = await fetch_company_data(sample_id)
    if raw_data:
        profile = parse_company_profile(raw_data)
        if profile:
            print(profile.model_dump_json(indent=4))
        else:
            print("Failed to parse company profile.")
    else:
        print("Failed to fetch company data.")


if __name__ == "__main__":
    asyncio.run(_main())

