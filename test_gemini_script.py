import sys, os
sys.path.append(r'C:\Users\manasa\OneDrive\Desktop\Multimodal Content Generation Suite')
from multimodal_suite.gemini_service import generate_campaign_brief

try:
    result = generate_campaign_brief(
        product_name='SuperWidget',
        product_description='A versatile widget for all your needs.',
        target_audience='Tech enthusiasts',
        marketing_objective='Increase brand awareness',
        platforms=['Twitter', 'Instagram'],
        brand_tone='Friendly'
    )
    print('Result:', result)
except Exception as e:
    print('Error:', e)
