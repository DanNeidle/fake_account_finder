import csv
import json
import os
from tqdm import tqdm
import sys
from bs4 import BeautifulSoup

companies_house_snapshot = "BasicCompanyDataAsOneFile-2025-01-01.csv"
sic_codes_file = "sic_codes.json"

ACCOUNTS_LOOKUP_TABLE_FILE = "company_accounts_lookup.json"
CASH_ALERT_VALUE = 1e7
OTHER_ALERT_VALUE = 1e8



def print_help():
    help_text = """
Usage: python 1_find_companies.py <SIC_CODES>

<SIC_CODES> can be a single SIC code or multiple SIC codes separated by '-'.

Examples:
    python 1_find_companies.py 64110
    python 1_find_companies.py 64110-64910-64999
    

Some interesting SIC codes:

    "64191": "Banks",
    "64110": "Central banking",
    "64192": "Building societies",
    "64301": "Activities of investment trusts",
    "64302": "Activities of unit trusts",
    "64303": "Activities of venture and development capital companies",
    "64304": "Activities of open-ended investment companies",
    "64305": "Activities of property unit trusts",
    "64306": "Activities of real estate investment trusts",
    "64910": "Financial leasing",
    "64921": "Credit granting by non-deposit taking finance houses and other specialist consumer credit grantors",
    "64922": "Activities of mortgage finance companies",
    "64929": "Other credit granting n.e.c.",
    "64991": "Security dealing on own account",
    "64992": "Factoring",
    "64999": "Financial intermediation not elsewhere classified",
    "65110": "Life insurance",
    "65120": "Non-life insurance",
    "65201": "Life reinsurance",
    "65202": "Non-life reinsurance",
    "65300": "Pension funding",
    "66120": "Security and commodity contracts dealing activities",
    "66220": "Activities of insurance agents and brokers",
    "66300": "Fund management activities",
    
"""
    print(help_text)



def extract_assets(ixbrl_file):
    with open(ixbrl_file, mode="r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")

    # Dictionary to store extracted financial data
    financial_data = {}

    # Find all ix:nonFraction tags
    ix_elements = soup.find_all("ix:nonfraction")

    # Iterate through elements to find CurrentAssets and NetAssets
    for element in ix_elements:
        tag_name = element.get("name").replace("ns5:", "")
        value = element.text.strip()
        
        if tag_name:
            financial_data[tag_name] = value
            
    return financial_data


def find_large_companies(companies, lookup_table):
    
    suspect_companies = []
    
    for company in tqdm(companies, desc="Filtering for large balance sheets"):

        company_name = company.get("CompanyName", "").strip()
        company_number = company.get("CompanyNumber", "").strip()
        regulatory_status = company.get("regulatory_status", [])
        
        # we're only interested in unregulated companies
        if regulatory_status:
            # print(f"{company_name}: regulated")
            continue
        
        ixbrl_file_path = lookup_table.get(company_number)
        
        if not ixbrl_file_path:
            # print(f"{company_name}: accounts not found")
            continue    

        financial_data = extract_assets(ixbrl_file_path)

        cash_value = 0
        suspect_data = []
        
        for key, value in financial_data.items():
            human_key = key.split(":")[1] if ":" in key else key
            
            clean_str_value = value.replace(",", "")
            try:
                value_float = float(clean_str_value)
            except:
                continue
            
            if human_key == "CashBankOnHand":
                cash_value = value_float
            elif value_float > OTHER_ALERT_VALUE:
                
                suspect_data.append((human_key, value_float))
                
        if (cash_value > CASH_ALERT_VALUE) or suspect_data:
            suspect_companies.append({
                "CompanyName": company_name,
                "CompanyNumber": company_number,
                "SIC1": company["Data"].get("SICCode.SicText_1", ""),
                "SIC2": company["Data"].get("SICCode.SicText_2", ""),
                "SIC3": company["Data"].get("SICCode.SicText_3", ""),
                "SIC4": company["Data"].get("SICCode.SicText_4", ""),
                "Cash": cash_value,
                "SuspectData": suspect_data
            })
            
    suspect_companies.sort(key=lambda x: x["Cash"], reverse=True)
    
    print(f"\nOf which {len(suspect_companies)} have large balance sheets")
    return suspect_companies

    

def construct_sic_dictionary():
    # Check if arguments are provided
    if len(sys.argv) < 2:
        print("Error: No SIC codes provided.")
        print_help()
        sys.exit(1)
    
    # Get the SIC codes argument
    sic_arg = sys.argv[1]
    sic_codes = sic_arg.split('-')
    
    # Load SIC codes descriptions from sic_codes.json
    if not os.path.exists(sic_codes_file):
        print(f"Error: SIC codes file '{sic_codes_file}' not found.")
        sys.exit(1)
    
    with open(sic_codes_file, mode="r", encoding="utf-8") as f:
        try:
            all_sic_codes = json.load(f)
        except json.JSONDecodeError:
            print(f"Error: Failed to parse '{sic_codes_file}'. Ensure it's valid JSON.")
            sys.exit(1)
    
    # Validate SIC codes
    invalid_sics = [code for code in sic_codes if code not in all_sic_codes]
    if invalid_sics:
        print(f"Error: Invalid SIC codes: {', '.join(invalid_sics)}")
        print_help()
        sys.exit(1)
    
    # Construct relevant_sic_codes dict
    relevant_sic_codes = {code: all_sic_codes[code] for code in sic_codes}
    
    # Print the SIC codes and descriptions
    print("Running with the following SIC codes:")
    for code, desc in relevant_sic_codes.items():
        print(f"{code}: {desc}")
        
    print("")
        
    return relevant_sic_codes


def read_with_progress(file, pbar):
    """
    Generator that reads lines from a file and updates the progress bar based on bytes read.
    """
    for line in file:
        # Update the progress bar with the number of bytes in the line
        pbar.update(len(line.encode('utf-8')))
        yield line



def find_matching_companies(relevant_sic_codes):
    
    if not os.path.exists(companies_house_snapshot):
        print(f"Error: Companies House snapshot '{companies_house_snapshot}' not found. You can download from https://download.companieshouse.gov.uk/en_output.html - then update the filename in this script")
        sys.exit(1)
    
    # Convert SIC codes to a set for faster lookup
    relevant_sic_set = set(relevant_sic_codes.keys())

    # Initialize the search results as a list
    search_results = []

    # Get the total file size for progress tracking
    file_size = os.path.getsize(companies_house_snapshot)

    # Define the SIC code fields
    sic_fields = ["SICCode.SicText_1", "SICCode.SicText_2", "SICCode.SicText_3", "SICCode.SicText_4"]

    # Open the CSV file with a progress bar
    with open(companies_house_snapshot, mode="r", encoding="utf-8") as csvfile:
        # Read the first line to get the headers
        first_line = csvfile.readline()
        headers = [header.strip() for header in first_line.strip().split(',')]
        
        # Initialize DictReader with stripped headers
        reader = csv.DictReader(read_with_progress(csvfile, tqdm(total=file_size - len(first_line.encode('utf-8')),
                                                                unit='B', unit_scale=True, desc="Processing CSV")),
                                fieldnames=headers)
        
        total_searched = 0
        
        # Iterate over each row in the CSV
        for row in reader:
            
            total_searched += 1
            
            # Extract and clean SIC codes by taking the first 5 characters
            sic_codes = []
            for field in sic_fields:
                sic_entry = row.get(field, "").strip()
                if sic_entry:
                    sic_code = sic_entry[:5]  # Extract the first 5 characters
                    if sic_code.isdigit() and sic_code in relevant_sic_set:
                        sic_codes.append(sic_code)
            
            # Find matching SIC codes
            if sic_codes:
                company_number = row.get("CompanyNumber", "").strip()
                company_name = row.get("CompanyName", "").strip()
                
                # Verify that company_number is not empty
                if not company_number:
                    # If CompanyNumber is missing, skip this entry
                    continue
                
                # Store the results
                match_entry = {
                    "CompanyName": company_name,
                    "CompanyNumber": company_number,
                    "RelevantSicCodes": {code: relevant_sic_codes[code] for code in sic_codes},
                    "Data": row,  # Include full row data for context
                }
                search_results.append(match_entry)
                
                # Print the matching company details - for debugging
                # print(f"Match Found - Company: {company_name}, SIC Codes: {', '.join(sic_codes)}")
    
    return search_results, total_searched

def save_results(relevant_sic_codes, search_results):
    
    keys_string = "-".join(relevant_sic_codes.keys())
    output_file = f"companies-{keys_string}.json"

    # Write the search results to a JSON file
    with open(output_file, mode="w", encoding="utf-8") as jsonfile:
        json.dump(search_results, jsonfile, indent=4)
        
    return output_file

def report_statistics(search_results, total_searched):
    
    # Report statistics
    total_companies = len(search_results)
    category_stats = {}

    for entry in search_results:
        for code in entry["RelevantSicCodes"]:
            category_stats[code] = category_stats.get(code, 0) + 1

    print(f"\nFound companies with relevant SIC codes: {total_companies} out of {total_searched}")
    
    if len(category_stats) > 1:
        for code, count in sorted(category_stats.items()):
            print(f"{code}: {count} companies")
        


def load_accounts_lookup_table():

    with open(ACCOUNTS_LOOKUP_TABLE_FILE, mode="r", encoding="utf-8") as jsonfile:
        lookup_table = json.load(jsonfile)
        
    print(f"Loaded lookup table - {len(lookup_table)} companies' accounts")
    return lookup_table

def main():

    
    relevant_sic_codes = construct_sic_dictionary()
    
    search_results, total_searched = find_matching_companies(relevant_sic_codes)
    
    print("Result of initial search for matching SIC code companies:")
    report_statistics(search_results, total_searched)
    
    lookup_table = load_accounts_lookup_table()
    large_companies = find_large_companies(search_results, lookup_table)    
    output_file = save_results(relevant_sic_codes, large_companies)

    print(f"Saved to {output_file}")
    
if __name__ == "__main__":
    main()