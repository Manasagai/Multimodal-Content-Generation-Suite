from multimodal_suite.gemini_service import generate_campaign_brief, analyze_image
from multimodal_suite.imagen_service import generate_image

brief = generate_campaign_brief("BerryBurst", "A mixed berry drink.", "18-35", "grow sales", ["Instagram"], "Friendly")
print("BRIEF KEYS", sorted(brief.keys()))
path = generate_image('purple bottle "BerryBurst" with white label', "Modern", "1:1")
print("IMAGE", path)
print("ANALYSIS KEYS", sorted(analyze_image(path).keys()))
print("ALL OK")
