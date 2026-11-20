"""Local dependency/configuration check. Does not make API calls or print secrets."""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
checks = []
def check(label, fn):
    try:
        fn()
        checks.append((label, True, "OK"))
    except Exception as exc:
        checks.append((label, False, str(exc)))

check("Streamlit", lambda: __import__("streamlit"))
check("Google Gen AI SDK", lambda: __import__("google.genai", fromlist=["genai"]))
check("ReportLab", lambda: __import__("reportlab"))
check("Pillow", lambda: __import__("PIL"))
check("Database module", lambda: __import__("multimodal_suite.db", fromlist=["db"]))
check("Gemini service module", lambda: __import__("multimodal_suite.gemini_service", fromlist=["gemini_service"]))
check("Imagen service module", lambda: __import__("multimodal_suite.imagen_service", fromlist=["imagen_service"]))
check("PDF export module", lambda: __import__("multimodal_suite.export", fromlist=["export"]))
print("\nMCGS LOCAL PREFLIGHT")
for label, ok, detail in checks:
    print(f"{'PASS' if ok else 'FAIL'}  {label}: {detail}")
print("Gemini API key:", "present (value hidden)" if os.getenv("GEMINI_API_KEY") else "MISSING")
print("Gemini model:", os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
print("\nThis check does not call Google APIs.")
raise SystemExit(0 if all(x[1] for x in checks) else 1)
