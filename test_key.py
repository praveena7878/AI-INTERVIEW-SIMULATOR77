import os
import sys

# Dynamic environment repair for Windows system PATH issues
if sys.platform == 'win32':
    if 'SystemRoot' not in os.environ:
        os.environ['SystemRoot'] = 'C:\\Windows'
    system32_path = 'C:\\Windows\\System32'
    windows_path = 'C:\\Windows'
    wbem_path = 'C:\\Windows\\System32\\Wbem'
    current_path = os.environ.get('PATH', '')
    paths = [p.strip() for p in current_path.split(';') if p.strip()]
    dirty = False
    if system32_path not in paths:
        paths.append(system32_path)
        dirty = True
    if windows_path not in paths:
        paths.append(windows_path)
        dirty = True
    if wbem_path not in paths:
        paths.append(wbem_path)
        dirty = True
    if dirty:
        os.environ['PATH'] = ';'.join(paths)

API_KEY = "AQ.Ab8RN6ITylaVDbye12HhMshO5yPjiFcnFLfIchXzmm50S5wyrw"

print("==============================================")
print("GEMINI API KEY DIAGNOSTIC TEST (MODELS TEST)")
print("==============================================")
print(f"Key: {API_KEY[:9]}...{API_KEY[-4:]} (Length: {len(API_KEY)})")

try:
    from google import genai
    client = genai.Client(api_key=API_KEY)
    
    print("\n--- Listing all models available for your key ---")
    try:
        models = list(client.models.list())
        for m in models:
            print(f" - {m.name}")
        if not models:
            print("No models returned.")
    except Exception as e:
        print(f"Failed to list models: {e}")

    print("\n--- Testing different model names ---")
    
    test_models = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-2.5-flash", "gemini-1.5-pro"]
    for model_name in test_models:
        try:
            print(f"Testing {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents="Say 'OK'."
            )
            print(f"  -> SUCCESS! Response: '{response.text.strip()}'")
        except Exception as e:
            print(f"  -> FAILED: {e}")

except ImportError:
    print("google-genai SDK is not installed.")
except Exception as e:
    print(f"Error initializing client: {e}")

print("==============================================")
