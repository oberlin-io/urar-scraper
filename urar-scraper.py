import requests
from bs4 import BeautifulSoup as soup
import re
import lists # City and zip code lists in directory
import webbrowser
from selenium import webdriver
from datetime import datetime


effective_date = raw_input("Effective date of appraisal (mm/dd/yyyy): ")
# Add input verification

# Set dictionary to collect all data strings
data_dict = {}


### AUDITOR BASE TAB ###

testing = False
if testing:
    with open("raw-html/base.html", "r") as f:
        base = f.read()
    print("Retrieving auditor base data...")

else:
    parcel = raw_input("Stark County parcel number: ")
    print("\nRetrieving auditor base data...")
    aud_url = "http://ddti.starkcountyohio.gov/Data.aspx?ParcelID="
    aud_url += parcel

    cookies = dict(Disclaimer="accept")
    headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Mobile Safari/537.36"}
    r = requests.get(aud_url, cookies = cookies, headers = headers)
    base = r.text


base = soup(base, "html.parser")

# Grab div base data blob
data = base.find("div", {"class":"base"})

address = data.find("span", {"id": "ContentPlaceHolder1_Base_fvDataProfile_AddressLabel"})
address = str(address.contents)
address = (address[3:-2]).title()


zips = lists.zipCodes
zips_count = len(zips)
for i in range(len(zips)):
    if zips[i] in address:
        zip = zips[i]
        index = address.find(zip)
        address = address[:index - 1]
        break

    else:
        zips_count -= 1

if zips_count <= 0:  # Case in which no zip match found
    data_dict["Zip Code"] = "Null"
    # Add: Or run search in other fields in base

else:
    data_dict["Zip Code"] = zip

# Remove Oh (state)
oh = " Oh$" # Shouldn't match "Ohio St."
if re.search(oh, address):
    oh = re.search(oh, address).group()
    address = address.replace(oh, "")


cities = lists.cities
city_count = len(cities)
for i in range(len(cities)):
    if cities[i] in address:
        city = cities[i]
        index = address.find(city)
        address = address[:index - 1]
        break

    else:
        city_count -= 1

if city_count <= 0:  # Case in which no city match found
    data_dict["City"] = "Null"
    # Add: Or run search in other fields in base

else:
    data_dict["City"] = city


# Ordinal abbreviation correction
ord_nums = "[0-9]+[A-Z][a-z]"
search = re.search(ord_nums,address)
if search:
    match = search.group(0)
    ord_abbr = match[-2:]
    ordinals = [
        ["St","st"],
        ["Nd","nd"],
        ["Rd","rd"],
        ["Th","th"],
        ]
    for i in range(len(ordinals)):
        if ord_abbr == ordinals[i][0]:
            address = address.replace(ordinals[i][0],ordinals[i][1])


# Compass direction correction
dir = [
    ["Ne", "NE"],
    ["Se", "SE"],
    ["Sw", "SW"],
    ["Nw", "NW"],
]
for i in range(len(dir)):
    for j in range(len(dir[i])):
        if j == 0:
            if dir[i][j] in address:
                address = address.replace(dir[i][j],dir[i][j + 1])

data_dict["Property Address"] = address


owner = base.find("span", {"id": "ContentPlaceHolder1_Base_fvDataProfile_OwnerLabel"})
owner = str(owner.contents)
owner = (owner[3:-2]).title()

# Add: if period in owner: replace period with ''
# Add: if 'and' in owner: replace 'and' with '&'

if "LLC" not in owner:
    owner = owner.replace(" ",", ",1) # Comma after last name
    # Add: Predict if second person has last name, insert comma
    # Add: II, III case corrections

    data_dict["Owner of Public Record"] = owner

# LLC correction
llc = ["Llc", "LLC"]
for i in range(len(llc)):
    if i == 0:
        if llc[i] in owner:
            owner = owner.replace(llc[i],llc[i + 1])


legal_desc = base.find("span", {"id": "ContentPlaceHolder1_Base_fvDataLegal_LegalDescriptionLabel"})
legal_desc = str(legal_desc.contents)
legal_desc = (legal_desc[3:-2]).title()

# Compass direction correction
for i in range(len(dir)):
    for j in range(len(dir[i])):
        if j == 0:
            if dir[i][j] in legal_desc:
                legal_desc = legal_desc.replace(dir[i][j],dir[i][j + 1])

# Add: All'T correction

tax_code = base.find("span", {"id": "ContentPlaceHolder1_Base_fvDataGeographic_TaxCodeLabel"})
tax_code = str(tax_code.contents)
tax_code = (tax_code[8:-2]).title()

# CSD and LSD correction
if "Csd" in tax_code:
    tax_code = tax_code.replace("Csd","CSD")
if "Lsd" in tax_code:
    tax_code = tax_code.replace("Lsd", "LSD")

data_dict["Legal Description"] = legal_desc + tax_code


parcel_ = base.find("span", {"id": "ContentPlaceHolder1_Base_fvDataProfile_ParcelLabel"})
parcel_ = str(parcel_.contents)
parcel_ = (parcel_[3:-2])

data_dict["Assessor's Parcel #"] = parcel_


print("Auditor base data retrieved.")


### AUDITOR LAND TAB ###
print("\nRetrieving auditor land data...")
driver = webdriver.Chrome(executable_path="C:/root/chromedriver.exe")
driver.get(aud_url)
driver.find_element_by_id("ContentPlaceHolder1_btnDisclaimerAccept").click()

driver.find_element_by_link_text("Land").click()
land_table = driver.find_element_by_id("ContentPlaceHolder1_Land_gvDataLand")
land_table = land_table.get_attribute("innerHTML")
land_table = soup(land_table, "html.parser")
table_rows = land_table.findAll("tr")

table = []
for r in range(len(table_rows)):
    if r == 0:
        row = table_rows[r].findAll("th")
        new_row = []
        for t in row:
            new_row.append(str(t.contents)[3:-2])
        table.append(new_row)
    else:
        row = table_rows[r].findAll("td")
        new_row = []
        for t in row:
            new_row.append(str(t.contents)[3:-2])
        table.append(new_row)

# Add: Logic for multiple dims rows or no Frontage but multiple acreage
# Add: Module for acreage, add, to feet



index = table[0].index("Frontage")
frontage = table[1][index]
depth = table[1][index+1]
area = table[1][index+2] # Are the auditor land table cols always in same order?

data_dict["Dimensions: Frontage"] = frontage
data_dict["Dimensions: Depth"] = depth
data_dict["Area"] = area
print("Auditor land data retrieved.")






###  AUDITOR SALES TAB ###

print("\nRetrieving auditor sales data...")
driver.find_element_by_link_text("Sales").click()
sales_table = driver.find_element_by_id("ContentPlaceHolder1_Sales_gvDataSales")
sales_table = sales_table.get_attribute("innerHTML")
sales_table = soup(sales_table, "html.parser")
table_rows = sales_table.findAll("tr")

table = []
for r in range(len(table_rows)):
    if r == 0:
        row = table_rows[r].findAll("th")
        new_row = []
        for t in row:
            new_row.append(str(t.contents)[3:-2])
        table.append(new_row)
    else:
        row = table_rows[r].findAll("td")
        new_row = []
        for t in row:
            new_row.append(str(t.contents)[3:-2])
        table.append(new_row)

if len(table[0]) == 0: # No sales data
    print("No auditor sales data found.")
    # Add: if no sale in last 3 years: append 'No transfers'

else:

    trans_table = []


    for row in range(len(table)):
        trans_table.append([table[row][1],table[row][7]])
        # Add: Convert format so always mm/dd/yyyy for URAR form specs


    eff_date = datetime.strptime(effective_date, "%m/%d/%Y")

    # Add: date format for sales

    prior_sales_or_transfers = []
    for row in range(len(trans_table)):
        if row != 0:
            trans_date = datetime.strptime(trans_table[row][0], "%m/%d/%Y")
            trans_age = abs((eff_date - trans_date).days)
            if trans_age <= 1095.75: #1095.75 avg days in 3 years
                prior_sales_or_transfers.append(trans_table[row])

    data_dict["My research did / did not reveal any prior sales or transfers of the subject property for the three years prior to the effective date of this appraisal."] = prior_sales_or_transfers
    print("Auditor sales data retrieved and calculated against effective date.")


### FEMA Flood Data ###
# Maybe access through REST service: https://hazards.fema.gov/femaportal/wps/portal/NFHLWMS
# NFHL (effective data only):
# https://hazards.fema.gov/gis/nfhl/rest/services/public/NFHL/MapServer


### AUDITOR SAT IMAGE LOAD ###
sat_url = "http://ddti.starkcountyohio.gov/UserControls/Default.mapx?ToDo=FindParcel&SearchString=" + parcel_ + "&Height=720&Width=900"
# Add: Keys to remove parcel numbers
print("\nOpening satellite map image.")
webbrowser.open(sat_url)


### OUTPUT: DICT TO CSV ###
output = "URAR Scraper  |  oberl.info\n"
for field in lists.urar_fields:
    if field in data_dict:
        if type(data_dict[field]) == list:
            # Bug: With no sales data, output shows "\xa0"
            for i in data_dict[field]:
                for j in i:
                    output += "\"" + str(j) + "\"\n"
        else:
            output += "\"" + str(data_dict[field]) + "\"\n"

with open("output.csv", "w") as f:
    f.write(output)
print("\noutput.csv updated.")


###
done = raw_input("\nDone")
