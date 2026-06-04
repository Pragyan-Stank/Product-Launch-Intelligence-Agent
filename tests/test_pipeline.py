import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from graph.workflow import app

print("Successfully imported LangGraph workflow!")

try:
    print("Executing competitor analysis graph...")
    inputs = {
        "company_name": "Tesla",
        "analysis_type": "competitor"
    }
    
    result = app.invoke(inputs)
    print("\nResult Keys:", list(result.keys()))
    
    # Save output to a utf-8 text file to avoid Windows console print encoding issues
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "outputs"), exist_ok=True)
    with open("outputs/output.txt", "w", encoding="utf-8") as f:
        f.write("=== VALIDATION STATUS ===\n")
        f.write(result.get("validation_status") or "None")
        f.write("\n\n=== RAW BULLETS ===\n")
        f.write(result.get("raw_bullets") or "None")
        f.write("\n\n=== FINAL REPORT ===\n")
        f.write(result.get("final_report") or "None")
    
    print("Successfully wrote output to outputs/output.txt!")
except Exception as e:
    import traceback
    traceback.print_exc()
