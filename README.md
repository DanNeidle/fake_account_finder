# script for finding companies with false accounts on Companies House

These instructions are for Linux. They should work on Mac. They, and the script, may need some adaptation to work on Windows.
You will need some experience with the command line.

---

## 1. Set Up Your Environment

1. Clone the Git repository:
    ```bash
    git clone https://github.com/DanNeidle/fake_account_finder.git
    ```

2. Navigate to the project directory:
    ```bash
    cd fake_account_finder
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

## 2. Download Required Data

### Companies House Data

1. Create a directory for Companies House data and for output data:
    ```bash
    mkdir companies_house_data
    mkdir output
    ```

2. Download the latest Companies House "snapshot," which contains key data on all companies, from the following link:
   [Download Companies House Snapshot](https://download.companieshouse.gov.uk/en_output.html)

3. Download all company accounts electronically filed with Companies House last year from this link:
   [Download Company Accounts](https://download.companieshouse.gov.uk/en_monthlyaccountsdata.html)  

   **Note:** This dataset is very large (~300GB) and contains approximately 3.2 million accounts. However, processing this locally is *much* faster and more reliable than using the Companies House API for individual accounts.

4. Extract the archive files into the `companies_house_data/` directory.
    ```bash
    for zip_file in *.zip; do
        unzip "$zip_file" -d companies_house_data
    done
    ```
    
5. Check that the files are there - you should see about 300GB
   ```bash
   du -h companies_house_data
   ```

6. If all is good, delete the zip files
   ```bash
   del *.zip
   ```

---

## 4. Obtain an FCA API Key (Optional)

If you wish to filter for regulatory status, you need a (free) API key from the Financial Conduct Authority (FCA):

1. Visit the FCA developer portal:
   [FCA Developer Portal](https://register.fca.org.uk/Developer/ShAPI_LoginPage?startURL=%2FDeveloper%2Fs%2F)

2. Follow the instructions and obtain an API key.

---

## 5. Configure settings

1. Rename the `companies_house_settings_example.py` to `companies_house_settings.py`.
   ```bash
   mv companies_house_settings_example.py companies_house_settings.py
   ```

2. Edit the file as follows:

   `companies_house_snapshot_file` should be the same filename as the CSV file you downloaded from Companies House
   Complete `fca_user` and `fca_api_key`, if you want to screen for unregulated companies and have obtained an api key. Otherwise just leave the defaults
   `scp_destinations` is a list of destinations to SCP the output HTML and CSV files when the script completes. For me that's convenient. Leave the list blank and it will be ignored.

---

## 6. Build indexes

1. Check the script is working:
    ```bash
    ./find_companiew
    ```

    You should see a help page.

2. Create a lookup table that indexes all the account files:
    ```bash
    ./find_companiew -buildlookup
    ```

2. Create the index for sic/address searches:
    ```bash
    ./find_companies -buildindex
    ```

---

## 7. Example usage

### Lookup SIC Codes

To list the most likely suspect SIC codes:
    ```bash
    ./find_companies -sichelp
    ```

Alternatively, for a list of all SIC codes:
    ```bash
    ./find_companies -sichelp all
    ```

More usefully, to search e.g. for the SIC codes for banks
    ```bash
    ./find_companies -sichelp bank
    ```

### Example SIC code searches
    
To find all companies with a bank SIC code with cash holdings of £10m+ or other balance sheet entries of £100m+:
```bash
./find_companies -sic 64191
```

If all goes well, you should see something like:
```output
Searching 5,637,210 companies for SIC codes 64191: Banks
Found 1,145 companies with matching SIC.

Filtering for large balance sheets: 100%|██████████████████████████████████████████████████████████████████████| 1145/1145 [00:00<00:00, 3025.04it/s]
Found 18 companies with large balance sheets
```

This will save the results to a CSV file in the output directory, together with a nicely formatted HTML table.

Some of those entities will be regulated; it makes sense to screen them out (as fraudsters are unlikely to be FCA-regulated). This will be a little slower, because we have to query the FCA register API:
```bash
./find_companies -sic 64191 -reg
```

Alternatively, to limit the search to companies filing as dormant, with cash holdings of £10m+ (but ignoring companies with other large balance sheet entries):
```bash
./find_companies -sic 64191 -cashonly -dormantonly
```

Or if you want to return all companies, without filtering for balance sheet:
```bash
./find_companies -sic 64191 -nofilter
``` 

To search for multiple SIC codes simultaneously, separate them with hyphens:
```bash
./find_companies -sic 64110-64120
```

### Search by Registered Office Address

You can, alternatively, search by a registered office address. Make sure to include quotes. For example:
```bash
./find_companies -address "124 city road"
```

As with SIC searches, you can combine with -cashonly, -dormant-only, -nofilter, or -reg. 

### Search every UK company for large cash balances

This will take a fairly long time (40 minutes on my PC):
```bash
./find_companies -all
```

You can combine with -dormant to only return dormant companies.



(c) Dan Neidle of Tax Policy Associates Ltd, 2025
Licensed under the GNU General Public License, version 2
