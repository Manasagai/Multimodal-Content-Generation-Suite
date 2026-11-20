# test_imagen.py
"""Sanity‑check for the Imagen service.
The script validates that:
1. The environment variables (GCP_PROJECT_ID, GCP_LOCATION) are loaded.
2. The GenAI client can be instantiated.
3. The requested Imagen model is available.
4. A generation request is attempted – any API error is caught and printed.
No real image is required for the sandbox; the script will report the failure
reason clearly.
"""

import os
import sys
import traceback
from pathlib import Path

# Add project root to sys.path for imports.
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

try:
    from multimodal_suite import imagen_service
except Exception as e:
    print("❌ Failed to import imagen_service:", e)
    sys.exit(1)

print("✅ imagen_service imported successfully")

# 1. Check .env loading – just verify the variables exist (do not print the values).
proj = os.getenv("GCP_PROJECT_ID")
loc = os.getenv("GCP_LOCATION")
print("✅ GCP_PROJECT_ID loaded:" if proj else "⚠️ GCP_PROJECT_ID missing")
print("✅ GCP_LOCATION loaded:" if loc else "⚠️ GCP_LOCATION missing")

# 2. Try to get the internal client (will raise if credentials missing).
try:
    client = imagen_service._get_client()  # accessing the internal helper for the test
    print("✅ GenAI Vertex AI client created")
except Exception as exc:
    print("⚠️ Failed to create GenAI client – likely missing ADC or invalid project/region:")
    traceback.print_exc()
    sys.exit(1)

# 3. Verify the Imagen model name is known to the SDK.
model_name = "imagen-4.0-generate-001"
try:
    available = client.models.list()
    names = [m.name for m in available]
    if model_name in names:
        print(f"✅ Model '{model_name}' is available")
    else:
        print(f"⚠️ Model '{model_name}' NOT found among available models: {names}")
except Exception as exc:
    print("⚠️ Could not list models – API error:")
    traceback.print_exc()
    sys.exit(1)

# 4. Attempt a generation (expected to fail in sandbox, but we catch the error).
print("\n🧪 Attempting image generation (will fail in sandbox if no network)...")
try:
    path = imagen_service.generate_image(
        prompt="A sleek modern coffee mug on a wooden table",
        style="minimalist",
        aspect="1:1",
        model_name=model_name,
    )
    print("✅ Image generated and saved at:", path)
except Exception as exc:
    print("⚠️ Image generation failed – this is expected in the sandbox environment.")
    traceback.print_exc()
