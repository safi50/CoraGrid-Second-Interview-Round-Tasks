import logging
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from schema import Metrics

logger = logging.getLogger(__name__)

load_dotenv()



async def structure_output(text: str) -> dict | None:
    """Extract structured metrics from raw text using the Gemini model."""
    logger.debug("structure_output called with text (%d chars): %s", len(text), text[:120])
    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        prompt = f"""
                You are an information extraction engine. Extract data from the provided text and return ONLY valid JSON that conforms EXACTLY to this schema:

                    {{
                    "income": number,                 // required, > 0
                    "net_income": number,             // required (can be negative)
                    "emissions": number | null,       // optional, >= 0 if present
                    "water_usage": number | null,     // optional, >= 0 if present
                    "quarter": string | null          // required in schema: if not explicitly stated, return null
                    }}

                Hard rules:
                - Use ONLY information explicitly stated in the text. Do NOT guess or infer.
                - If a value is missing, unclear, or not explicitly stated, return null.
                - Never use example numbers from this prompt. Examples are illustrative only and MUST NOT be copied into output.
                - Output JSON only: no commentary, no extra keys, no code fences.

                Number parsing:
                - Convert compact/human numbers to raw numbers:
                - "12.5M" -> 12500000
                - "450k" -> 450000
                - "1.2 million" -> 1200000
                - Treat currency words/symbols as noise unless part of the number.
                - All numeric outputs must be JSON numbers (not strings).

                Field-specific extraction rules:
                1) income:
                - Extract the numeric amount describing total income (e.g., "Total income hit 12.5M euros").
                - If multiple income numbers exist, pick the one most directly tied to "income" or "total income".

                2) net_income:
                - Extract the numeric amount describing net gain/loss (e.g., "net gain of only 1.2M").
                - If the text says "net loss", output a negative number.
                - If multiple net-related values exist, choose the one explicitly labeled net income/gain/loss.

                3) emissions:
                - Look for "Scope 1", "Scope 2", "Scope 1 and 2", "Scope 1 & 2", "Scope I/II", and CO2e phrasing.
                - Also accept wording like "emissions to X metric tons", "tCO2e", "tons of CO2 equivalent".
                - Output the numeric value in metric tons (do not convert units unless the text provides a clear conversion).
                - If emissions are mentioned without a number, return null.

                4) water_usage:
                - Extract numeric water usage if explicitly stated.
                - If the text says it is not finalized or only gives expectations/comparisons (e.g., "expected to be lower than Q3"), return null.

                5) quarter:
                - Extract the quarter string EXACTLY as written.
                - Accept formats like "Q4", "Q4 2024", "quarter ended Q4", etc.
                - If the year is not present, keep only what appears (e.g., "Q4").
                - If no quarter label is present, return null.

                Now extract the fields from this text:
                {text}
        """

        logger.debug("Sending request to model: %s", os.getenv("GEMINI_MODEL"))
        response = await client.aio.models.generate_content(
            model=os.getenv("GEMINI_MODEL"),
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=Metrics.model_json_schema()
            )
        )
        logger.debug("Raw model response: %s", response.text)

        try:
            validated = Metrics.model_validate_json(response.text)
            return validated.model_dump()
        except Exception as e:
            logger.warning("Validation failed on first attempt: %s — requesting correction", e)
            corrected_response = await client.aio.models.generate_content(
                model=os.getenv("GEMINI_MODEL"),
                contents=f"Previous response: {response.text}\n\nThe response does not conform to the expected schema. Please correct it and return valid JSON that matches the schema exactly. In case of any missing values, use null. Do not include any commentary or extra fields, and ensure all numeric values are numbers, not strings.",
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_json_schema=Metrics.model_json_schema()
                )
            )
            logger.debug("Corrected model response: %s", corrected_response.text)
            try:
                validated = Metrics.model_validate_json(corrected_response.text)
                return validated.model_dump()
            except Exception as e2:
                logger.error("Validation failed on corrected response: %s", e2)
                raise

    except Exception as e:
        logger.error("Fatal error in structure_output: %s", e)
        return None



