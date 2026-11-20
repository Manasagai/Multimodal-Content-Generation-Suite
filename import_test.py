import sys, os
sys.path.append(r'C:\Users\manasa\OneDrive\Desktop\Multimodal Content Generation Suite')
try:
    import multimodal_suite.gemini_service as gs
    print('Import succeeded')
except Exception as e:
    print('Import failed:', e)
    import traceback, json
    traceback.print_exc()
