import requests
import time
import json
import sys
import os
import re

from companies_house_secrets import fca_user, fca_api_key

sic_codes_file = "sic_codes.json"

def read_command_line_args():
    if len(sys.argv) < 2:
        print("Error: No SIC codes provided.")
        print_help()
        sys.exit(1)
        
    input_file = f"companies-{sys.argv[1]}.json"
    
    if not os.path.exists(input_file):
        print(f"Error: input file {input_file} does not exist. Run the first script to create it..")
        sys.exit(1)
        
    sic_codes = sys.argv[1].split('-')
    
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
        
    return input_file


def print_help():
    help_text = """
Usage: python 2_find_unregulated_companies.py <SIC_CODES>

<SIC_CODES> can be a single SIC code or multiple SIC codes separated by '-'.

Examples:
    python 2_find_unregulated_companies.py 64110
    python 2_find_unregulated_companies.py 64110-64910-64999
    
"""
    print(help_text)




def search_firms(firm_name, search_type="firm", max_retries=3, backoff_factor=2):
    """
    Searches the FCA Register for firms matching the given search term.

    Args:
        firm_name (str): The name of the firm to search for.
        search_type (str): The type of entity to search for (default is 'firm').
        max_retries (int): Maximum number of retries for transient errors.
        backoff_factor (int): Factor by which the wait time increases after each retry.

    Returns:
        list: A list of matching firms or an empty list if none found or on persistent error.

    Prints:
        Status messages indicating progress and errors.
    """
    url = "https://register.fca.org.uk/services/V0.1/Search"

    # Query parameters
    params = {
        "q": firm_name,
        "type": search_type
    }

    # Headers
    headers = {
        "x-auth-email": fca_user,
        "x-auth-key": fca_api_key,
        "Content-Type": "application/json"
    }

    retry_count = 0
    wait_time = 1  # Initial wait time in seconds

    while retry_count <= max_retries:
        try:
            print(f"Searching for firm: '{firm_name}' (Attempt {retry_count + 1}/{max_retries + 1})")
            response = requests.get(url, params=params, headers=headers, timeout=10)

            if response.status_code == 200:
                # Successful response
                result = response.json()
                data = result.get('Data')
                if isinstance(data, list):
                    print(f"Found {len(data)} record(s) for '{firm_name}'.")
                    return data
                else:
                    print(f"No data found for '{firm_name}'.")
                    return []
            elif response.status_code == 429:
                # Rate limit exceeded
                print("Warning: Rate limit exceeded. Waiting for 65 seconds before retrying...")
                time.sleep(65)
            elif 500 <= response.status_code < 600:
                # Server-side error, retry after waiting
                print(f"Server error (HTTP {response.status_code}) encountered for '{firm_name}'. Retrying after {wait_time} seconds...")
                time.sleep(wait_time)
                retry_count += 1
                wait_time *= backoff_factor
            else:
                # Other client-side errors, do not retry
                print(f"Error: Received HTTP {response.status_code} for '{firm_name}'. Skipping this company.")
                return []
        except requests.exceptions.Timeout:
            # Handle timeout separately if needed
            print(f"Timeout occurred while searching for '{firm_name}'. Retrying after {wait_time} seconds...")
            time.sleep(wait_time)
            retry_count += 1
            wait_time *= backoff_factor
        except requests.exceptions.RequestException as e:
            # For other request-related errors, decide whether to retry or skip
            print(f"Request exception for '{firm_name}': {e}. Retrying after {wait_time} seconds...")
            time.sleep(wait_time)
            retry_count += 1
            wait_time *= backoff_factor

    # After max retries, assume the issue is with the company name or persistent server error
    print(f"⚠️  Failed to retrieve data for '{firm_name}' after {max_retries} attempts. Skipping this company.")
    return []

def load_company_dict(input_file):
    
    # Initialize the companies list
    companies = []

    # Load the JSON data from the input file
    try:
        with open(input_file, 'r', encoding='utf-8') as infile:
            companies = json.load(infile)
        print(f"Loaded {len(companies)} companies from '{input_file}'.")
    except FileNotFoundError:
        print(f"Error: The file '{input_file}' was not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from the file '{input_file}': {e}")
        sys.exit(1)
        
    return companies

def add_reg_status(companies):
    

    # Process each company in the list
    for index, company in enumerate(companies, start=1):
        # Extract company details
        company_name = company.get("CompanyName", "").strip()
        company_number = company.get("CompanyNumber", "").strip()

        # Validate essential fields
        if not company_name or not company_number:
            print(f"[{index}/{len(companies)}] ⚠️  Warning: Missing CompanyName or CompanyNumber. Skipping.")
            continue

        print(f"[{index}/{len(companies)}] 🔍 Processing: {company_name} ({company_number})")

        # Call the search_firms function to get regulatory status
        regulatory_status = search_firms(company_name)

        # Add the regulatory_status to the company's dictionary
        company["regulatory_status"] = regulatory_status

        # Print the company details
        print(f"{company_name} ({company_number}): {regulatory_status}\n")
        
    return companies

def save_companies_with_reg_info(companies, output_file):

    # Save the updated companies list to the output file
    try:
        with open(output_file, 'w', encoding='utf-8') as outfile:
            json.dump(companies, outfile, indent=4)
        print(f"Updated data has been saved to '{output_file}'.")
    except IOError as e:
        print(f"Error writing to file '{output_file}': {e}")
        

def normalize_name(name):
    """
    Normalize the company name by:
    - Removing text within parentheses.
    - Replacing "Limited" with "Ltd".
    - Removing trailing periods in "Ltd.".
    - Converting to lowercase.
    - Stripping leading/trailing whitespace.
    """
    # Remove text within parentheses and any surrounding whitespace
    name = re.sub(r'\s*\(.*?\)\s*', ' ', name)
    
    # Replace "Limited" with "Ltd"
    name = re.sub(r'\bLimited\b', 'Ltd', name, flags=re.IGNORECASE)
    
    # Remove trailing periods in "Ltd."
    name = re.sub(r'\bLtd\.\b', 'Ltd', name, flags=re.IGNORECASE)
    
    # Convert to lowercase and strip whitespace
    name = name.lower().strip()
    
    return name
        
# this is necessary because the FCA matching is very generous and we need to be much more strict
def prune_regulatory_info_in_company_list(companies):
    
    for company in companies:
        company_name = company.get("CompanyName", "").strip()
        company_number = company.get("CompanyNumber", "").strip()
        regulatory_status = company.get("regulatory_status", [])
        
        if not company_name or not company_number:
            print(f"Warning: Missing CompanyName or CompanyNumber for company: {company}")
            continue
        
        # Normalize the company name
        normalized_company_name = normalize_name(company_name)
        
        # Initialize a list to hold pruned regulatory_status entries
        pruned_regulatory_status = []
        
        for entry in regulatory_status:
            entry_name = entry.get("Name", "").strip()
            normalized_entry_name = normalize_name(entry_name)
            
            if normalized_entry_name == normalized_company_name:
                pruned_regulatory_status.append(entry)
                
            else:
                print(f"{company_name}: deleting {entry_name}")
        
        # Update the company's regulatory_status with the pruned list
        company["regulatory_status"] = pruned_regulatory_status
        
    
    return companies
        
def main():
        
    input_file = read_command_line_args()
    output_file = input_file.replace("companies-", "companies-unregulated-")
    companies = load_company_dict(input_file)
    
    companies_with_reg_status = add_reg_status(companies)
    pruned_list_of_companies_with_reg_status = prune_regulatory_info_in_company_list(companies_with_reg_status)
    
    
    save_companies_with_reg_info(pruned_list_of_companies_with_reg_status, output_file)


if __name__ == "__main__":
    main()