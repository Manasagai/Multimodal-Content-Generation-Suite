import json, sys
from google.genai import errors
print(json.dumps([name for name in dir(errors) if not name.startswith('_')]))
