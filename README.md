# urar-scraper
Collects web-based real estate data and formats the text for input to the Uniform Residential Appraisal Report, or the URAR form.

## Some functions to possibly work on

### Store neighborhood list with names and map numbers
nCount = len(lists.neighborhoods)
for i in lists.neighborhoods:
    if i[0] in taxC:
        dataStrings.append(i[0])
        dataStrings.append(i[1])
        break
    else:
        nCount -= 1
if nCount <= 0:
    dataStrings.append("Null")
    dataStrings.append("Null")

### Auditor Dimensions
#### Auditor if Dimensions have acres and not feet
if frontage == "":
    acres = ac0 + ac1
    sqft = acres * 43560 # ac-ft conversion
    front = raw_input("Input frontage in feet: ")
    # auto-open: https://starkcountyohio.maps.arcgis.com/apps/webappviewer/index.html?id=03f862c83bd0426588b5571afe59a407
    depth = sqft / front
    dimString = "Frontage,"+str(front)+"\nDepth,"+str(depth)+"\n"
    return dimString

