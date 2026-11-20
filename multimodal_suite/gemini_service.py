# multimodal_suite/gemini_service.py
"""Gemini AI service wrapper using the official Google Gen AI SDK.
Provides:
* :func:`generate_campaign_brief` – creates structured marketing copy.
* :func:`analyze_image` – evaluates an uploaded image with Gemini Vision.

The implementation uses ``google`` package (``genai`` and ``genai.types``) and reads the API key from a ``.env`` file.
All responses are returned as validated Python ``dict`` objects.
"""

import os
import json
import logging
import time
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, BinaryIO
from multimodal_suite.local_engine import use_gemini

# ---------------------------------------------------------------------------
# Load environment variables from .env if python‑dotenv is available.
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

if load_dotenv:
    project_root = Path(__file__).resolve().parents[1]
    env_path = project_root / ".env"
    load_dotenv(dotenv_path=env_path)

# ---------------------------------------------------------------------------
# Logging configuration (simple console logger).
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(asctime)s – %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

import ssl

import ssl
# ---------------------------------------------------------------------------
# Import the new Google Gen AI SDK lazily.
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Import the new Google Gen AI SDK lazily.
# ---------------------------------------------------------------------------
try:
    from google import genai
    from google.genai import types, errors
except ImportError as exc:
    logger.error("Required Google Gen AI SDK not found: %s", exc)
    raise ImportError(
        "Please install the official 'google-genai' package (pip install google-genai)"
    ) from exc
# ---------------------------------------------------------------------------
# Constants and client configuration
# ---------------------------------------------------------------------------
_API_KEY_ENV = "GEMINI_API_KEY"
_MODEL_ENV = "GEMINI_MODEL"
_DEFAULT_MODEL = "gemini-3.8-flash"
_HTTP_TIMEOUT = 120000  # 120 seconds

# ---------------------------------------------------------------------------
# Client handling – singleton.
# ---------------------------------------------------------------------------
_client: Optional[genai.Client] = None

def _configure_client() -> genai.Client:
    """Create (or return) a ``genai.Client`` using the API key.
    Configured with a 30‑second HTTP timeout.
    Raises ``EnvironmentError`` if the key is missing.
    """
    global _client
    if _client is not None:
        return _client

    api_key = os.getenv(_API_KEY_ENV)
    if not api_key:
        raise EnvironmentError(
            "Gemini API key not found. Set the environment variable GEMINI_API_KEY or add it to a .env file."
        )
    # Set HTTP timeout via HttpOptions
    http_options = types.HttpOptions(timeout=_HTTP_TIMEOUT)
    _client = genai.Client(api_key=api_key, http_options=http_options)
    logger.info(
        "Gemini client initialised with model %s and timeout %dms",
        os.getenv(_MODEL_ENV, _DEFAULT_MODEL),
        _HTTP_TIMEOUT,
    )
    return _client
# ---------------------------------------------------------------------------
_API_KEY_ENV = "GEMINI_API_KEY"
_MODEL_ENV = "GEMINI_MODEL"
_DEFAULT_MODEL = "gemini-3.8-flash"
_MAX_RETRIES = 1



def _model_name(model_name: Optional[str] = None) -> str:
    """Resolve the model name to use.
    Preference order: argument > GEMINI_MODEL env > default.
    """
    return model_name or os.getenv(_MODEL_ENV, _DEFAULT_MODEL)

# ---------------------------------------------------------------------------
# Retry helper for transient Gemini errors (503, 429, etc.).
# ---------------------------------------------------------------------------
def _is_transient_error(exc):
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    if code in (429, 500, 502, 503, 504):
        return True
    text = str(exc)
    return "DEADLINE_EXCEEDED" in text or "UNAVAILABLE" in text or "RESOURCE_EXHAUSTED" in text and False

def _call_with_retry(func, *args, **kwargs):
    """Execute ``func`` with exponential back‑off for transient errors.
    Retries up to ``_MAX_RETRIES`` times. If all attempts fail, raises a
    ``RuntimeError`` with a user‑friendly message.
    """
    delay = 1
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            if not _is_transient_error(exc) or attempt == _MAX_RETRIES:
                logger.exception(
                    "Gemini call failed on attempt %d (permanent or max retries reached)", attempt
                )
                raise RuntimeError("Gemini call failed after retries: " + str(exc)[:300]) from exc
            logger.warning(
                "Transient Gemini error (attempt %d/%d): %s – retrying in %d sec",
                attempt,
                _MAX_RETRIES,
                exc,
                delay,
            )
            time.sleep(min(delay, 5))
            delay *= 2
    raise RuntimeError("Unexpected exit from Gemini retry loop")

# ---------------------------------------------------------------------------
# Helper to extract JSON from Gemini response text.
# ---------------------------------------------------------------------------
def _extract_json(text: str) -> Dict[str, Any]:
    """Find the first '{' in *text* and parse the subsequent JSON.
    Raises ``ValueError`` if parsing fails.
    """
    try:
        start = text.index('{')
        return json.loads(text[start:])
    except (ValueError, json.JSONDecodeError) as exc:
        raise ValueError("Unable to parse JSON from Gemini response.") from exc

# ---------------------------------------------------------------------------
# Campaign generation – returns a validated dict.
# ---------------------------------------------------------------------------
_REQUIRED_CAMPAIGN_FIELDS = [
    "headline",
    "tagline",
    "product_description",
    "captions",
    "hashtags",
    "ctas",
    "visual_concept",
]

def generate_campaign_brief(
    product_name: str,
    product_description: str,
    target_audience: str,
    marketing_objective: str,
    platforms: List[str],
    brand_tone: str,
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate a structured marketing campaign using Gemini.
    Returns a dictionary containing the fields defined in ``_REQUIRED_CAMPAIGN_FIELDS``.
    """
    if not use_gemini():
        from multimodal_suite.local_engine import local_campaign_brief
        return local_campaign_brief(product_name, product_description, target_audience, marketing_objective, platforms, brand_tone)

    if not all([product_name, product_description, target_audience, marketing_objective, platforms, brand_tone]):
        raise ValueError("All campaign parameters must be non‑empty.")

    prompt = (
        "You are a senior marketing copywriter. Produce a concise JSON object for a marketing campaign. "
        "The JSON must contain the following keys: headline, tagline, product_description, captions (list of three strings), "
        "hashtags (list of strings), ctas (list of three strings), visual_concept (short description). "
        "Do not include any extra text before or after the JSON.\n\n"
        f"Product name: {product_name}\n"
        f"Product description: {product_description}\n"
        f"Target audience: {target_audience}\n"
        f"Marketing objective: {marketing_objective}\n"
        f"Platforms: {', '.join(platforms)}\n"
        f"Brand tone: {brand_tone}\n"
    )

    model = _model_name(model_name)
    client = _configure_client()
    response = None
    last_error = None
    for candidate_model in [model, "gemini-3.8-flash", "gemini-3.5-flash"]:
        try:
            response = _call_with_retry(
                client.models.generate_content,
                model=candidate_model,
                contents=prompt,
            )
            break
        except Exception as exc:
            last_error = exc
            text = str(exc)
            if "503" in text or "UNAVAILABLE" in text or "429" in text or "RESOURCE_EXHAUSTED" in text or "404" in text or "NOT_FOUND" in text:
                logger.warning("Model %s unavailable, trying next model", candidate_model)
                continue
            raise
    if response is None:
        raise RuntimeError("All Gemini models are busy or unavailable right now. Please wait a few minutes and try again. Last error: " + str(last_error)[:200])

    if not response or not getattr(response, "text", None):
        raise RuntimeError("Gemini returned an empty response for campaign generation.")
    data = _extract_json(response.text)
    missing = [k for k in _REQUIRED_CAMPAIGN_FIELDS if k not in data]
    if missing:
        raise ValueError(f"Gemini response missing required fields: {missing}")
    for key in ("captions", "hashtags", "ctas"):
        if not isinstance(data[key], list) or not all(isinstance(i, str) for i in data[key]):
            raise ValueError(f"'{key}' must be a list of strings.")
    logger.info("Successfully generated campaign brief for %s", product_name)
    return data

# ---------------------------------------------------------------------------
# Image analysis – returns a structured dict.
# ---------------------------------------------------------------------------
_IMAGE_ANALYSIS_FIELDS = [
    "composition",
    "color_combination",
    "product_visibility",
    "marketing_effectiveness",
    "brand_consistency",
    "improvement_suggestions",
]

def _prepare_image_input(image):
    """Accept a file path or an open binary file and return a Gemini image part."""
    if isinstance(image, str):
        with open(image, "rb") as f:
            content = f.read()
    else:
        content = image.read()
    mime = "image/jpeg" if content[:3] == b"\xff\xd8\xff" else "image/png"
    return types.Part.from_bytes(data=content, mime_type=mime)

def analyze_image(image: BinaryIO | str, model_name: Optional[str] = None) -> Dict[str, Any]:
    """Analyze an image using Gemini Vision and return a structured analysis dict.
    ``image`` can be a path string or an opened binary file.
    """
    if not use_gemini():
        import tempfile
        from multimodal_suite.local_engine import local_image_analysis
        if isinstance(image, str):
            path = image
        else:
            data = image if isinstance(image, bytes) else image.read()
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            tmp.write(data)
            tmp.close()
            path = tmp.name
        return local_image_analysis(path)

    if not image:
        raise ValueError("No image supplied for analysis.")
    img_input = _prepare_image_input(image)
    prompt = (
        "You are a marketing visual analyst. Examine the supplied image and output a JSON object with the following keys: "
        "composition, color_combination, product_visibility, marketing_effectiveness, brand_consistency, improvement_suggestions. "
        "Provide concise bullet‑style strings for each field. Do not wrap the JSON in any extra text."
    )
    model = _model_name(model_name)
    client = _configure_client()
    response = None
    last_error = None
    for candidate_model in ["gemini-3.8-flash", "gemini-3.5-flash"]:
        try:
            response = _call_with_retry(
                client.models.generate_content,
                model=candidate_model,
                contents=[img_input, prompt],
            )
            break
        except Exception as exc:
            last_error = exc
            text = str(exc)
            if "503" in text or "UNAVAILABLE" in text or "429" in text or "RESOURCE_EXHAUSTED" in text:
                logger.warning("Model %s busy, trying next model", candidate_model)
                continue
            raise
    if response is None:
        raise RuntimeError("All Gemini models are busy right now. Please wait a few minutes and try again. Last error: " + str(last_error)[:200])
    if not response or not getattr(response, "text", None):
        raise RuntimeError("Gemini returned an empty response for image analysis.")
    analysis = _extract_json(response.text)
    missing = [k for k in _IMAGE_ANALYSIS_FIELDS if k not in analysis]
    if missing:
        raise ValueError(f"Image analysis response missing fields: {missing}")
    logger.info("Image analysis completed successfully.")
    return analysis

# Exported symbols for ``from . import gemini_service`` convenience.
__all__ = ["generate_campaign_brief", "analyze_image"]
