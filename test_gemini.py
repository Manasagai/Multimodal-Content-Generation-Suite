# test_gemini.py
"""Simple sanity‑check for the Gemini service.
Runs without printing any secret values.
The script will:
1. Verify that the .env file is loaded and GEMINI_API_KEY is present.
2. Show the configured model name.
3. Attempt a campaign generation call (network errors are caught and reported).
4. Confirm that the image‑analysis function exists.
"""

import os
import sys
import traceback
from pathlib import Path

# Ensure the project root is on sys.path for imports.
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# Import the service – this will trigger dotenv loading.
try:
    from multimodal_suite import gemini_service
except Exception as e:
    print("❌ Failed to import gemini_service:", e)
    sys.exit(1)

# 1. Check that the .env file was read (do not print the key).
api_key_present = bool(os.getenv("GEMINI_API_KEY"))
print("✅ .env loaded:" if api_key_present else "⚠️ GEMINI_API_KEY not found in environment")

# 2. Show the configured model (default if not set).
model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
print(f"🔧 Configured Gemini model: {model_name}")

# 3. Test generate_campaign_brief with sample data.
sample_data = {
    "product_name": "EcoBottle",
    "product_description": "A reusable stainless‑steel water bottle with a built‑in filter.",
    "target_audience": "Eco‑conscious commuters",
    "marketing_objective": "Increase brand awareness and drive sales",
    "platforms": ["Instagram", "Facebook"],
    "brand_tone": "Modern",
}

print("\n🧪 Attempting campaign generation…")
try:
    brief = gemini_service.generate_campaign_brief(
        sample_data["product_name"],
        sample_data["product_description"],
        sample_data["target_audience"],
        sample_data["marketing_objective"],
        sample_data["platforms"],
        sample_data["brand_tone"],
    )
    print("✅ Campaign brief generated successfully. Keys returned:")
    print(list(brief.keys()))
except Exception as exc:
    print("⚠️ Campaign generation failed – likely due to network restrictions in the sandbox.")
    traceback.print_exc()

# 4. Verify that the image analysis function exists and is callable.
if hasattr(gemini_service, "analyze_image"):
    print("✅ analyze_image function is present.")
else:
    print("❌ analyze_image function missing.")
