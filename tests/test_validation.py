import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from tools.validate import validate_search_results

results = [
    {
        "title": "All NEW Features On 2026 Tesla Model Y",
        "url": "https://youtube.com/watch?v=12345",
        "description": "A comprehensive review of the new features of the 2026 Tesla Model Y."
    },
    {
        "title": "Tesla Q3 2012 Financial Report",
        "url": "https://tesla.com/report2012",
        "description": "Historical financial data for Tesla Q3 2012."
    },
    {
        "title": "Access Denied - Cloudflare",
        "url": "https://blocked.com",
        "description": "Please enable JavaScript to view this page. Access Denied."
    }
]

print("Running validation...")
validated, logs = validate_search_results(results, "Tesla")
print("Validation finished.")

os.makedirs(os.path.join(os.path.dirname(__file__), "..", "outputs"), exist_ok=True)
with open("outputs/validation_test_output.txt", "w", encoding="utf-8") as f:
    f.write("=== LOGS ===\n")
    f.write(logs)
    f.write("\n\n=== VALIDATED ===\n")
    f.write(str(validated))
