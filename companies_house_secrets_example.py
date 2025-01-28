# once completed, this file should be renamed companies_house_secrets

# optional if you want to use the regulatory status filter script
# obtain api key from https://register.fca.org.uk/Developer/ShAPI_LoginPage?startURL=%2FDeveloper%2Fs%2F
fca_user = "me@myemail.com"
fca_api_key = "secret"

# this is if you want the results to be uploaded to a server. It's just a list of destinations. You'll need to have ssh keys setup.
scp_destinations = ["dan@my-server:/home/dan/target_directory", "dan@my-wordpress-server:/home/dan/target_directory"]