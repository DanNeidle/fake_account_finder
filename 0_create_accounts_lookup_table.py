import os
import re
import json

"""
This script contains a lookup table for all the company accounts we download.

download zip files with monthly account filings
then unzip all into the accounts directory with:

for zipfile in *.zip; do
    unzip "$zipfile" -d accounts
done

"""

# Directory containing account files
accounts_directory = "accounts"

# Output JSON file
output_json = "company_accounts_lookup.json"

company_accounts_lookup = {}

# Initialize a set to store unique file types
file_types = set()

# Regex pattern to extract company numbers from filenames
file_pattern = re.compile(r".*_(\d+)_.*\.(\w+)$")  # Matches any file extension

# Traverse the accounts directory and its subdirectories
for root, _, files in os.walk(accounts_directory):
    for file in files:
        match = file_pattern.match(file)
        if match:
            company_number = match.group(1)
            file_extension = match.group(2)
            full_path = os.path.join(root, file)
            
            file_types.add(file_extension)
            
            company_accounts_lookup[company_number] = full_path

with open(output_json, mode="w", encoding="utf-8") as jsonfile:
    json.dump(company_accounts_lookup, jsonfile, indent=4)

print("File types found:")
print(sorted(file_types))

print(f"Company accounts lookup table saved to {output_json}")
