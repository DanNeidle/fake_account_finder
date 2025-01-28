import json
import json
from bs4 import BeautifulSoup
import csv
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os
import sys

from companies_house_secrets import scp_destinations


# obvious limitation - only catches companies that filed electronic accounts in the last year.
ACCOUNTS_LOOKUP_TABLE_FILE = "company_accounts_lookup.json"
sic_codes_file = "sic_codes.json"



# Companies House URL format
COMPANIES_HOUSE_URL = "https://find-and-update.company-information.service.gov.uk/company/{}"

# Logo details
LOGO_URL = "https://taxpolicy.org.uk/wp-content/uploads/elementor/thumbs/logo-in-banner-tight-1-quqdc4qw34zmeg68ggs0psp29qcsftxn2pptrt1h6m.png"
LOGO_LINK = "https://taxpolicy.org.uk"

def print_help():
    help_text = """
Usage: python 3_export_results.py <SIC_CODES>

<SIC_CODES> can be a single SIC code or multiple SIC codes separated by '-'.

If a regulation-<SIC_CODES> file exists then this script will use that (e.g. if you've run the second script)
if it doesn't exist, this script will use companies-<SIC_CODES> (appropriate if it's an unregulated area and you didn't need to run the second script)

Examples:
    python 3_export_results.py 64110
    python 3_export_results.py 64110-64910-64999
    
"""
    print(help_text)


def read_command_line_args():
    
    if len(sys.argv) < 2:
        print("Error: No SIC codes provided.")
        print_help()
        sys.exit(1)
        
    sic_codes = sys.argv[1].split('-')
    
    input_file = f"companies-unregulated-{sys.argv[1]}.json"
    alternative_input_file =  f"companies-{sys.argv[1]}.json"

    if os.path.exists(input_file):
        print(f"Using {input_file}")

    elif os.path.exists(alternative_input_file):
        print(f"Can't find {input_file} - using {alternative_input_file}. This is sensible if it's an unregulated area such as central banks.")
        input_file = alternative_input_file
        
    else:
        print("Error: can't find input file")
        print_help()
        exit(0)
        
    
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
    
    if len(relevant_sic_codes) == 1:
        key, value = next(iter(relevant_sic_codes.items()))
        table_title = f"{key}: {value}"
    else:
        table_title = ", ".join(relevant_sic_codes.keys())
    
    print(f"\nAnalysing and exporting output table '{table_title}'")    
        
    return input_file, table_title

def load_accounts_lookup_table():

    with open(ACCOUNTS_LOOKUP_TABLE_FILE, mode="r", encoding="utf-8") as jsonfile:
        lookup_table = json.load(jsonfile)
        
    print(f"Loaded lookup table - {len(lookup_table)} companies' accounts")
    return lookup_table



def load_json_data():
    
    try:
        with open(input_file, 'r', encoding='utf-8') as infile:
            companies = json.load(infile)
            if not isinstance(companies, list):
                print(f"Error: The file '{input_file}' does not contain a list of companies.")
                return
    except FileNotFoundError:
        print(f"Error: The file '{input_file}' was not found.")
        return
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from the file '{input_file}': {e}")
        return
    
    print(f"Loaded {len(companies)} companies from '{input_file}'.\n")
    return companies


def remove_regulated_companies(companies):
    initial_count = len(companies)
    
    # Filter for unregulated companies (no 'regulatory_status' key or an empty list as the value)
    unregulated_companies = [
        company for company in companies 
        if not company.get("regulatory_status") or len(company.get("regulatory_status", [])) == 0
    ]
    
    final_count = len(unregulated_companies)
    removed_count = initial_count - final_count
    
    # Report the filtering results
    print(f"Filtered out {removed_count} regulated companies. {final_count} unregulated companies remain.")
    
    return unregulated_companies


def create_html(suspect_companies, table_title):
    """
    Create an HTML file with a table of suspicious 'bank' companies styled according to in-house guidelines,
    including a header with color and logo.
    """
    
    export_html_table_filename = f"results-{sys.argv[1]}.html"

    # Set up Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(searchpath='.'),
        autoescape=select_autoescape(['html', 'xml'])
    )
    
    # Define a custom filter for adding commas to numbers
    def format_number(value):
        try:
            return "{:,}".format(int(value))
        except (ValueError, TypeError):
            try:
                return "{:,}".format(float(value))
            except (ValueError, TypeError):
                return value  # Return as is if not a number
    
    env.filters['format_number'] = format_number

    # Define the HTML template with header and in-house styling
    template_string = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
        <title>TABLE_TITLE</title>
        <!-- Google Fonts: Poppins -->
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
        <!-- Bootstrap CSS -->
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <!-- DataTables CSS -->
        <link rel="stylesheet" href="https://cdn.datatables.net/1.13.4/css/dataTables.bootstrap5.min.css">
        <!-- Favicon -->
        <link rel="icon" href="{{ logo_url }}" sizes="32x32" type="image/jpeg">
        <style>
            body {
                font-family: 'Poppins', sans-serif;
                color: #000000;
            }
            .container {
                margin-top: 50px;
            }
            /* Header Styling */
            .header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                background-color: #1133AF; 
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 30px;
            }
            .header h1 {
                color: #FFFFFF;
                margin: 0;
                font-weight: 600;
            }
            /* Logo Styling */
            .logo {
                height: 60px;
            }
            /* Table Header Styling */
            table.dataTable thead th {
                background-color: #1133AF;
                color: white;
            }
            /* Table Row Hover and Zebra Striping */
            table.dataTable tbody tr:nth-child(odd) {
                background-color: #f9f9f9;
            }
            table.dataTable tbody tr:hover {
                background-color: #D3D3D3 !important;
            }
            /* Links Styling */
            a {
                color: #1133AF;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
            /* DataTables Length and Filter Styling */
            .dataTables_wrapper .dataTables_length,
            .dataTables_wrapper .dataTables_filter {
                color: #000000;
            }
            /* Ensure the Cash column is right-aligned for better readability */
            td:nth-child(4), th:nth-child(4) {
                text-align: right;
            }
            /* SIC Cell Styling */
            .sic-cell span {
                display: block;
                max-width: 300px; /* Adjust as needed */
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                cursor: pointer;
            }
            /* Added CSS for wrapping long suspect items */
            .item-cell {
                max-width: 200px; /* Adjust the width as needed */
                word-wrap: break-word;
                white-space: normal;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Header with Logo -->
            <div class="header"  id="main-header">
                <h1>TABLE_TITLE</h1>
                <a href="{{ logo_link }}" target="_blank">
                    <img src="{{ logo_url }}" alt="Company Logo" class="logo">
                </a>
            </div>
            <!-- Suspect Companies Table -->
            <table id="suspectCompaniesTable" class="table table-striped table-bordered" style="width:100%">
                <thead>
                    <tr>
                        <th>Company Name</th>
                        <th>Company Number</th>
                        <th>SICs</th>
                        <th>Cash</th>
                        {% for i in range(1, max_suspects + 1) %}
                            <th>Item {{ i }}</th>
                            <th>Value {{ i }}</th>
                        {% endfor %}
                    </tr>
                </thead>
                <tbody>
                    {% for company in companies %}
                    <tr>
                        <td>{{ company.CompanyName }}</td>
                        <td>
                            <a href="{{ companies_house_url.format(company.CompanyNumber) }}" target="_blank">
                                {{ company.CompanyNumber }}
                            </a>
                        </td>
                        <td class="sic-cell">
                            {% for sic in [company.SIC1, company.SIC2, company.SIC3, company.SIC4] %}
                                {% if sic %}
                                    <span data-bs-toggle="tooltip" data-bs-placement="top" title="{{ sic }}">{{ sic[:25] }}{% if sic|length >25 %}...{% endif %}</span>
                                {% endif %}
                            {% endfor %}
                        </td>
                        <td data-sort="{{ company.Cash }}">{{ company.Cash | format_number }}</td>
                        {% for item, value in company['SuspectData'] %}
                            <td class="item-cell">{{ item }}</td>
                            <td>{{ value | format_number }}</td>
                        {% endfor %}
                        {% for _ in range(max_suspects - company['SuspectData']|length) %}
                            <td></td>
                            <td></td>
                        {% endfor %}
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <!-- jQuery -->
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <!-- Bootstrap JS Bundle -->
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <!-- DataTables JS -->
        <script src="https://cdn.datatables.net/1.13.4/js/jquery.dataTables.min.js"></script>
        <script src="https://cdn.datatables.net/1.13.4/js/dataTables.bootstrap5.min.js"></script>
        <!-- Scroller Extension JS -->
        <script src="https://cdn.datatables.net/scroller/2.1.2/js/dataTables.scroller.min.js"></script>
        <script>
            $(document).ready(function() {
                $('#suspectCompaniesTable').DataTable({
                    "scrollY": "800px",
                    "scrollX": true,
                    "scroller": true,
                    "paging": false,
                    "searching": false,
                    "order": [[3, "desc"]],  // Order by Cash column descending
                    "lengthMenu": [10, 25, 50, 100, 4021],
                    "columnDefs": [
                        { 
                            "targets": 3, 
                            "type": "num", 
                            "render": function (data, type, row) {
                                if(type === 'sort') {
                                    return data;
                                }
                                return data;
                            }
                        }
                    ],
                    "language": {
                        "search": "Filter records:",
                        "lengthMenu": "Show _MENU_ entries",
                        "info": "Showing _START_ to _END_ of _TOTAL_ companies",
                        "infoEmpty": "No companies available",
                        "infoFiltered": "(filtered from _MAX_ total companies)"
                    }
                });

                // Initialize Bootstrap tooltips
                var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
                var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
                    return new bootstrap.Tooltip(tooltipTriggerEl)
                })
            });
        
            // Function to hide the header if the page is embedded
            function checkIfEmbedded() {
                if (window.self !== window.top) {
                    // Page is embedded
                    var header = document.getElementById('main-header');
                    if (header) {
                        header.style.display = 'none';
                    }
                }
            }

            // Run the check after the DOM is fully loaded
            document.addEventListener("DOMContentLoaded", checkIfEmbedded);
        </script>
    </body>
    </html>
    """
    
    template_string = template_string.replace("TABLE_TITLE", table_title)

    # Determine the maximum number of suspect items across all companies
    max_suspects = max(len(company.get("SuspectData", [])) for company in suspect_companies) if suspect_companies else 0

    # Create a Jinja2 template from the string
    template = env.from_string(template_string)

    # Render the template with the suspect companies and max_suspects
    html_output = template.render(
        companies=suspect_companies,
        max_suspects=max_suspects,
        companies_house_url=COMPANIES_HOUSE_URL,
        logo_url=LOGO_URL,
        logo_link=LOGO_LINK
    )

    # Write the rendered HTML to the output file
    try:
        with open(export_html_table_filename, 'w', encoding="utf-8") as f:
            f.write(html_output)
        print(f"HTML table has been saved to '{export_html_table_filename}'.")
    except IOError as e:
        print(f"Error writing HTML file: {e}")
        
    return export_html_table_filename

    
    
    
def create_csv(suspect_companies):
    
    export_csv_filename = f"results-{sys.argv[1]}.csv"

    # Generate CSV file
    max_items = max(len(company["SuspectData"]) for company in suspect_companies)
    
    with open(export_csv_filename, "w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        header = ["Company Name", "Company Number", "Cash", "SIC1", "SIC2", "SIC3", "SIC4"]
        for i in range(max_items):
            header.extend([f"Item {i+1}", f"Value {i+1}"])
        writer.writerow(header)

        for company in suspect_companies:
            row = [
                company["CompanyName"],
                company["CompanyNumber"],
                company["Cash"],
                company.get("SIC1", ""),
                company.get("SIC2", ""),
                company.get("SIC3", ""),
                company.get("SIC4", "")
            ]
            for item, value in company["SuspectData"]:
                row.extend([item, value])
            for _ in range(max_items - len(company["SuspectData"])):
                row.extend(["", ""])  # Fill missing columns
            writer.writerow(row)
    print(f"CSV file saved to {export_csv_filename}")
    return export_csv_filename
    

    
###########################

input_file, table_title = read_command_line_args()  

companies = load_json_data()
unregulated_companies = remove_regulated_companies(companies)

html_filename = create_html(unregulated_companies, table_title)
csv_filename = create_csv(unregulated_companies)

print("Uploading from server to laptop and wordpress")

for destination in scp_destinations:
    os.system(f"scp {html_filename} {destination}")
    os.system(f"scp {csv_filename} {destination}")

