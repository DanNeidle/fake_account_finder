# Fake Accounts Finder

(c) Dan Neidle of Tax Policy Associates Ltd, 2025

Licensed under the GNU General Public License, version 2

This script is intended to find potentially fraudulent accounts filed on Companies House. It uses a very simple methodology to do this - see our article at https://taxpolicy.org.uk/2025/01/31/the-trillion-pound-fake-missed-by-companies-house/

The consequence is that the script will:
- only identify a particular kind of fraudulent company accounts. Failing to flag a company's accounts as suspicious in NO WAY means the accounts are kosher.
- shortlist accounts that are worthy of investigation. The actual accounts should *always* be reviewed before reaching any conclusion. In some cases (£100m+ cash balances in a "dormant" company that has no other balance sheet entries) one can be reasonably confident the accounts are fraudulent. In other cases, one cannot be, and further investigation would be required.

It is therefore wise to be *very* cautious about drawing any conclusions about a company when using this script. It could be legally hazardous to publicly accuse a copmany of fraud wihout extremely good reason (and, sometimes, it can be legally hazardous even if you have extremely good reasons).

These instructions are primarily for Linux. They should work on macOS, and can be adapted for Windows (see the notes below). You will need some familiarity with the command line to proceed.

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

5. Make the script executable:
   ```bash
    chmod +x find_companies
    ```

---

## 2. Download Required Data

### Companies House Data

Important: You’ll need a significant amount of free disk space (around 500 GB) to download, unzip, and handle the full Companies House accounts data. After setup, when you've deleted the original zip files, it should settle at about 330 GB.

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

## 3. Obtain an FCA API Key (Optional)

If you wish to filter for regulatory status, you need a (free) API key from the Financial Conduct Authority (FCA):

1. Visit the FCA developer portal:
   [FCA Developer Portal](https://register.fca.org.uk/Developer/ShAPI_LoginPage?startURL=%2FDeveloper%2Fs%2F)

2. Follow the instructions and obtain an API key.

If you don’t need to filter out regulated entities (e.g., you only want to see all companies meeting your other criteria), you can skip this step.

---

## 4. Configure settings

1. Rename the `companies_house_settings_example.py` to `companies_house_settings.py`.
   ```bash
   mv companies_house_settings_example.py companies_house_settings.py
   ```

2. Edit the file as follows:

   - `companies_house_snapshot_file` should be the same filename as the CSV file you downloaded from Companies House
   - Complete `fca_user` and `fca_api_key`, if you want to screen for unregulated companies and have obtained an api key. Otherwise just leave as blanks (but don't delete)
   - `scp_destinations` is a list of destinations to SCP the output HTML and CSV files when the script completes. For me that's convenient. Leave the list blank and it will be ignored.
   - CASH_ALERT_VALUE and OTHER_ALERT_VALUE: thresholds for “large balances.” Defaults are 10 million and 100 million.

---

## 5. Build indexes

Before running searches, you must build two indexes that mean the searches very quickly:

1. Check the script is working:
    ```bash
    ./find_companiew
    ```

    If you see help information, you’re good to proceed.

2. Create a lookup table that links the 300GB of account files to the relevant company number:
    ```bash
    ./find_companiew -buildlookup
    ```

    This scans the companies_house_data/ directory and creates a JSON file listing each company’s iXBRL file path.

2. Create the index for sic/address searches:
    ```bash
    ./find_companies -buildindex
    ```

    This reads the big CSV snapshot and creates a SQLite database for quick lookups by SIC code or address.

---

## 6. Example usage

Below are typical ways to run the script once everything is set up.

### Searching for SIC codes

To list the most likely suspect SIC codes:
    ```bash
    ./find_companies -sichelp
    ```

Alternatively, for a list of all SIC codes:
    ```bash
    ./find_companies -sichelp all
    ```

More usefully, to search for a SIC code containing a keyword, like "bank"
    ```bash
    ./find_companies -sichelp bank
    ```

This will output:

    ```output
    SIC codes matching 'bank':
    
    64110: Central banking
    64191: Banks
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

This will take a fairly long time (40 minutes on my PC), because it is parsing the 3 million account files individually:
```bash
./find_companies -all
```

You can combine with -dormant to only return dormant companies.

## 7. Output files
After a search, the script saves results to:

- output/results-<descriptor>.html (nicely formatted DataTables view)
- output/results-<descriptor>.csv (raw data for your own analysis)

If you configured scp_destinations in companies_house_settings.py, these files will also be uploaded automatically.

## 8. Notes for Windows
I have no Windows experience but I believe the script will work, with a few changes in setup:
- Use del *.zip instead of rm *.zip.
- Activate your virtual environment with venv\Scripts\activate.
- Some commands (like chmod +x) are not necessary or work differently on Windows. You may need to run the script via python find_companies ... instead of ./find_companies

## 9. Final thoughts

Make sure you have adequate disk space and a reasonably powerful and stable machine — parsing millions of account files is demanding.

If you want to do more advanced filtering or custom analytics, feel free to adapt the script’s logic or post-process the output CSV. It would be easy to adapt the script to, e.g. look at several years' of accounts (simultaneously or optionally), of course at the price of using more disk storage and likely slowing things down.

Unfortunately, I can't support anyone installing or using the script, but I'd be fascinated to see what uses people have for it. Do please drop ne a line - dan ATSIGN taxpolicy.org.uk
