import os, logging, pathlib, datetime
import urllib.parse, urllib.request
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None
if load_dotenv:
    load_dotenv(dotenv_path=pathlib.Path(__file__).resolve().parents[1] / ".env")
logger = logging.getLogger(__name__)
from multimodal_suite.local_engine import use_gemini
from google import genai
from google.genai import types

ALLOWED_ASPECTS = ("1:1", "4:5", "9:16", "16:9")
_IMAGEN_MODEL = "imagen-4.0-generate-001"
_GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image"
_imagen_client = None

def _out_dir():
    d = pathlib.Path(__file__).resolve().parents[1] / "generated"
    d.mkdir(parents=True, exist_ok=True)
    return d

def _save(data):
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    path = _out_dir() / ("visual_" + stamp + ".png")
    path.write_bytes(data)
    return str(path)

def _gemini_bytes(prompt, aspect):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY is missing from .env")
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=_GEMINI_IMAGE_MODEL,
        contents=prompt + ". Compose the image for a " + aspect + " aspect ratio.",
        config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
    )
    for candidate in response.candidates or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", None) or []:
            inline = getattr(part, "inline_data", None)
            if inline and getattr(inline, "data", None):
                return inline.data
    raise RuntimeError("Gemini image model returned no image.")

def _imagen_bytes(prompt, aspect, model_name):
    global _imagen_client
    if _imagen_client is None:
        project = os.getenv("GCP_PROJECT_ID")
        location = os.getenv("GCP_LOCATION")
        if not project or not location:
            raise EnvironmentError("GCP_PROJECT_ID or GCP_LOCATION is missing from .env")
        _imagen_client = genai.Client(vertexai=True, project=project, location=location)
    response = _imagen_client.models.generate_images(
        model=model_name, prompt=prompt,
        config=types.GenerateImagesConfig(aspect_ratio=aspect, number_of_images=1),
    )
    generated = getattr(response, "generated_images", None) or []
    if not generated:
        raise RuntimeError("Imagen returned no image.")
    first = generated[0]
    reason = getattr(first, "rai_filtered_reason", None)
    if reason:
        raise RuntimeError("Blocked by safety filter (" + str(reason) + "). Reword the prompt.")
    data = getattr(getattr(first, "image", None), "image_bytes", None)
    if not data:
        raise RuntimeError("Imagen response had no image data.")
    return data

_SIZES = {"1:1": (1024, 1024), "4:5": (1024, 1280), "9:16": (720, 1280), "16:9": (1280, 720)}

def _pollinations_bytes(prompt, aspect):
    w, h = _SIZES[aspect]
    url = ("https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt)
           + "?width=" + str(w) + "&height=" + str(h) + "&nologo=true&model=flux")
    req = urllib.request.Request(url, headers={"User-Agent": "MCGS-Studio/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()
    if not data or len(data) < 1000:
        raise RuntimeError("Free image service returned no usable image.")
    return data

def generate_image(prompt, style=None, aspect="1:1", model_name=_IMAGEN_MODEL):
    if not prompt or not prompt.strip():
        raise ValueError("Please describe the visual you want.")
    if aspect not in ALLOWED_ASPECTS:
        raise ValueError("Unsupported aspect ratio '" + str(aspect) + "'.")
    full_prompt = prompt.strip()
    if style:
        full_prompt = full_prompt + " Visual style: " + style + "."
    if not use_gemini():
        from multimodal_suite.local_engine import local_render_image
        return _save(local_render_image(full_prompt, aspect))
    try:
        data = _gemini_bytes(full_prompt, aspect)
        logger.info("Image generated via Gemini")
        return _save(data)
    except Exception as gemini_exc:
        logger.warning("Gemini image model failed, trying Imagen: %s", gemini_exc)
        try:
            data = _imagen_bytes(full_prompt, aspect, model_name)
            logger.info("Image generated via Imagen")
            return _save(data)
        except Exception as imagen_exc:
            logger.warning("Imagen failed, trying Pollinations fallback: %s", imagen_exc)
            try:
                data = _pollinations_bytes(full_prompt, aspect)
                logger.info("Image generated via Pollinations")
                return _save(data)
            except Exception as poll_exc:
                logger.error(
                    "All image generation sources failed: Gemini: %s | Imagen: %s | Pollinations: %s",
                    gemini_exc, imagen_exc, poll_exc,
                )
                raise RuntimeError(
                    "Image generation failed on all sources. Gemini and Imagen need billing on the Google Cloud project; the free fallback is currently unavailable."
                ) from poll_exc

__all__ = ["generate_image", "ALLOWED_ASPECTS"]
