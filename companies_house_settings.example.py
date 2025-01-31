# once completed, this file should be renamed companies_house_settings

# key constants
# when filtering for large companies, we discard companies unless either cash > CASH_ALERT_VALUE or another balance sheet item > OTHER_ALERT_VALUE
CASH_ALERT_VALUE = 1e7
OTHER_ALERT_VALUE = 1e8

# this is the most recent snapshot, the top right link on this page: https://download.companieshouse.gov.uk/en_output.html
companies_house_snapshot_file = "BasicCompanyDataAsOneFile-2025-01-01.csv"


# optional if you want to use the regulatory status filter script
# obtain api key from https://register.fca.org.uk/Developer/ShAPI_LoginPage?startURL=%2FDeveloper%2Fs%2F
fca_user = ""
fca_api_key = ""

# this is if you want the results to be uploaded to a server. It's just a list of destinations. You'll need to have ssh keys set up.

# example:
# scp_destinations = ["dan@my-server:/home/dan/target_directory", "dan@my-wordpress-server:/home/dan/target_directory"]
scp_destinations = []