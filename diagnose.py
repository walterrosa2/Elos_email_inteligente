import inspect
from app.review.dashboard import render_dashboard

print("--- SOURCE OF RENDER_DASHBOARD (First 20 lines) ---")
source = inspect.getsource(render_dashboard)
print("\n".join(source.splitlines()[:20]))

print("\n--- CHECKING STREAMLIT_APP.PY ---")
with open('streamlit_app.py', 'r', encoding='utf-8') as f:
    content = f.read()
    if 'Gestão de Contratos' in content:
        print("OK: 'Gestão de Contratos' exists in file.")
    else:
        print("ERROR: 'Gestão de Contratos' NOT in file.")

    if 'render_global_settings_ui' in content:
        print("OK: 'render_global_settings_ui' exists in file.")
    else:
        print("ERROR: 'render_global_settings_ui' NOT in file.")
