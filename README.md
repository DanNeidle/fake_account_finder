# Companies House scripts for finding suspect companies

More in this article: https://taxpolicy.org.ukfinding_trillion_pound_fake_companies

Instructions:

---

## 1. Set Up Your Environment

1. Clone the Git repository:
    ```bash
    git clone <repository-url>
    ```

2. Navigate to the project directory:
    ```bash
    cd <repository-directory>
    ```

3. Set up a Python virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

4. Install the required Python libraries:
    ```bash
    pip install -r requirements.txt
    ```

---

## 2. Prepare the Data Directory

1. Create a directory for Companies House data:
    ```bash
    mkdir companies_house_data
    ```

---

## 3. Download Required Data

### Companies House Snapshot

1. Download the latest Companies House "snapshot," which contains key data on all companies, from the following link:
   [Download Companies House Snapshot](https://download.companieshouse.gov.uk/en_output.html)

2. Place the downloaded file in the `companies_house_data/` directory.

### Company Accounts Data

1. Download all company accounts electronically filed with Companies House last year from this link:
   [Download Company Accounts](https://download.companieshouse.gov.uk/en_monthlyaccountsdata.html)

   **Note:** This dataset is very large (~300GB) and contains approximately 3.2 million accounts. However, processing this locally is much faster and more reliable than using the Companies House API for individual accounts.

2. Extract the archive files into the `companies_house_data/` directory.

---

## 4. Obtain an FCA API Key (Optional)

If you wish to filter for regulatory status, you need an API key from the Financial Conduct Authority (FCA):

1. Visit the FCA developer portal:
   [FCA Developer Portal](https://register.fca.org.uk/Developer/ShAPI_LoginPage?startURL=%2FDeveloper%2Fs%2F)

2. Obtain an API key.

---

## 5. Configure Secrets

1. Amend the `companies_house_secrets_example` file with your details.

---

## 6. Generate Lookup Table

1. Run the script to create a lookup table that indexes all accounts:
    ```bash
    python 0_create_accounts_lookup_table.py
    ```

---

## 7. Investigate SIC Codes

### Search for Specific SIC Codes

1. Filter for a SIC code of interest. For example, to find companies with "TRUST" in their SIC:
    ```bash
    python 1_find_companies.py -sic TRUST
    ```

2. Alternatively, see a list of the most likely suspect SICs:
    ```bash
    python 1_find_companies.py -sic
    ```

### Investigate a Specific SIC Code

1. To investigate a specific SIC code (e.g., Central Bank, 64110):
    ```bash
    python 1_find_companies.py -sic 64110
    ```

    - This will output a file named `companies-64110.json` containing all companies with the SIC code and large balance sheets.

2. To search for multiple SIC codes simultaneously, separate them with hyphens:
    ```bash
    python 1_find_companies.py -sic 64110-64120
    ```

### Search by Registered Office Address

1. You can also search by a registered office address. For example:
    ```bash
    python 1_find_companies.py -address "124 city road"
    ```

---

## 8. Filter for Unregulated Entities

1. To include only unregulated entities, filter the previous output:
    ```bash
    python 2_find_unregulated_companies.py 64110
    ```

   - This will create a file named `companies-unregulated-64110.json`.

---

## 9. Export Results

1. Export the final data to HTML and CSV formats:
    ```bash
    python 3_export_results.py 64110
    ```

   - If an "unregulated" JSON file exists, it will be used; otherwise, the "company" JSON file will be used.
   - This command creates `results-64110.html` and `results-64110.csv`.

---

## Notes

- For faster and more reliable processing, use local datasets instead of APIs wherever possible.
- Always verify the integrity of the downloaded data.

---


(c) Dan Neidle of Tax Policy Associates Ltd, 2025
Licensed under the GNU General Public License, version 2
