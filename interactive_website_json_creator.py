import json
import os
import re

# File paths
JSON_INPUT_FILE = "sic_codes.json"
CSV_FOLDER = "output/"
JSON_OUTPUT_FILE = os.path.join(CSV_FOLDER, "interactive_website_sics.json")

# Load the SIC codes from the JSON file
with open(JSON_INPUT_FILE, "r", encoding="utf-8") as f:
    all_sic_codes = json.load(f)

# List to store results
exported_results = []

# Process each SIC code
for code, description in all_sic_codes.items():
    # Generate sanitized filename
    sanitized_text = re.sub(r'[\\/:*?"<>|]', '_', description.replace(" ", "_"))
    csv_filename = f"results-{code}_{sanitized_text}.csv"
    csv_filepath = os.path.join(CSV_FOLDER, csv_filename)
    
    # Count lines in CSV (excluding header)
    num_lines = 0
    if os.path.exists(csv_filepath):
        with open(csv_filepath, "r", encoding="utf-8") as csv_file:
            num_lines = sum(1 for _ in csv_file) - 1  # Subtract header
            num_lines = max(num_lines, 0)  # Ensure non-negative count
    
    # Append results
    exported_results.append((description, csv_filename.replace(".csv", ""), num_lines))

# Save results to JSON
with open(JSON_OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(exported_results, f, indent=4, ensure_ascii=False)

print(f"Processed {len(all_sic_codes)} SIC codes. Results saved to {JSON_OUTPUT_FILE}.")
