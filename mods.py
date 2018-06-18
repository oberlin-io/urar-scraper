import os
import re
import datetime as dt
from selenium import webdriver as web
from bs4 import BeautifulSoup as soup
import requests as reqs
import lists
import time



# Testing switch
import testmode
testing = testmode.testmode()



def startHTML(order):

	return '''<!DOCTYPE html>
<html>
<head>
	<meta charset='utf-8'>
	<title>%s</title>
	<link href='https://fonts.googleapis.com/css?family=Aldrich|Bungee' rel='stylesheet'>
	<style>
		body {
			background-color: #000;
			color: #fff;
			font-family: 'Aldrich', sans-serif;
			width: 90%s;
			margin: auto;
		}
		.title {
			font-family: Bungee, sans-serif;
			font-size: 40;
		}
		.inputBox {
			width: 100%s;
			background-color: #fff;
			color: #686868;
			text-align: right;
			font-size: 25px;
			border-radius: 4px;
			
		}
		input {
			width: 80%s;
			border: none;
			font-family: 'Aldrich', sans-serif;
			font-size: 25px;
			border-radius: 4px;
		}
	</style>
</head>
<body>
<div class='title'>URAR Stark Scraper</div>
<form>
''' % (order, '%', '%', '%')



def formInput(name, value):

	return '''<div class='inputBox'>
<label class='label' for='%s'>%s</label>
<input type='text' name='%s' id='%s' value='%s'>
</div><br>
''' % (name, name, name, name, value)


	
def endHTML():

	return '''</form>
</body>
</html>'''



def makeFolder(name):

	try:
		os.makedirs(name)
		print '%s folder created.' % name
		
	except WindowsError:
		if testing == False:
			pause = raw_input('''There's already a folder for %s. Check the directory.
Close this program now if you'd like to avoid possibly overwriting its contents.
Or hit enter to continue.''' % name)

		else:
			print 'Ignoring os.makedirs WindowsError for testing.'



def writeFile(path, nameExt, content, mode):

	try:
		with open(path + '/' + nameExt, mode) as f:
				f.write(content)
		print '%s updated.' % nameExt
	
	except IOError:
		pause = raw_input('The folder %s isn\'t there. Check the directory.' % path)

		
		
def getParcel(driver, order):
	'''
	Gets parcel number and directs drive to auditor page according to parcel
	'''

	# In most cases order name format is 1234abcd
	
	# Some cases the order name has a single digit suffixed, eg 1714sinc2
	# If duplicate orders ever increase into double digits, change regex
	digi_suffix = re.compile('\d')
	
	if digi_suffix.match(order[-1]):
		order = order[:-1]
		pause = raw_input('Order string after finding single digit at end and splicing: %s' % order)
	
	else:
		pause = raw_input('Last digit in order string not found; no change: %s' % order)
		pass
	
	# Capture the number, if there is one
	digis = re.compile('(\d+)')
	
	if digis.match(order):
		number = digis.match(order).group()
		street = order[digis.match(order).end():]
		street = street.replace('-','')
		url = 'http://ddti.starkcountyohio.gov/Results.aspx?SearchType=QuickSearch&Criteria1=%s+%s' % (number, street)

	else:
		url = 'http://ddti.starkcountyohio.gov/Results.aspx?SearchType=QuickSearch&Criteria1=%s' % order

	driver.get(url)
	driver.find_element_by_id('ContentPlaceHolder1_btnDisclaimerAccept').click()

	table = driver.find_element_by_class_name('searchresults')
	table = table.get_attribute('innerHTML')
	table = soup(table, 'html.parser')
	trs = table.findAll('tr')

	results = []
	for tr in trs[1:]:
		tds = tr.findAll('td')
		parcel = tds[0].find('a')
		parcel = str(parcel.contents)[3:-2]
		result = [parcel, str(tds[1].contents)[3:-2], str(tds[2].contents)[3:-2]]
		results.append(result)


	if testing == False:
		if len(results) == 1:
			print 'I found this one result:'
			print results[0]
			response = raw_input('Hit enter to use this result, or type your own damn parcel number: ')

		else:
			print 'I found these results:'
			for r in results:
				print results.index(r) + 1, ':', r
			response = raw_input('Type the number to select, or type your own parcel number: ')

		print 'Got it, thanks.'
		
	else:
		response = ''

	print 'Gathering info...'
	
	# If a parcel number was typed
	if len(response) > 2:
		parcel = response
		user = True

	# If a selection was made, eg 3 or 10.
	elif len(response) > 0:
		parcel = results[ int(response) - 1 ][0]
		user = False
		
	# Parcel number stays as it was initialized when only one result was found
	else:
		user = False

		
	if user == True:
		url = 'http://ddti.starkcountyohio.gov/Data.aspx?ParcelID=%s' % parcel
		driver.get(url)

	else:
		driver.find_element_by_link_text(parcel).click()
		
	
	return parcel
	

	
def getAddress(driver):
	
	address = driver.find_element_by_id('ContentPlaceHolder1_Base_fvDataProfile_AddressLabel')
	address = address.get_attribute('innerHTML').title()

	zips = lists.zipCodes
	zips_count = len(zips)
	for z in zips:
		if z in address:
			zip = z
			dx = address.find(zip)
			address = address[:dx - 1].title()
			break

		else:
			zips_count -= 1
	
	if zips_count <= 0: # Case in which no zip match found		
		# If tax mailing address == parcel address, grab city and zip
		tax_addy = driver.find_element_by_id('ContentPlaceHolder1_Base_fvDataMailingAddress_MailingAddressLine2Label')
		tax_addy = tax_addy.get_attribute('innerHTML').title()
		
		if tax_addy[:7] == address[:7]:
			
			city_zip = driver.find_element_by_id('ContentPlaceHolder1_Base_fvDataMailingAddress_MailingAddressLine3Label')
			city_zip = city_zip.get_attribute('innerHTML').title()
			
			zips_count = len(zips)
			for z in zips:
				if z in city_zip:
					zip = z
					break
				else:
					zips_count -= 1
			
			if zips_count <= 0:
				zip = 'Not available, sorry.'
			else:
				pass
		else:
			zip = 'Not available, sorry.'
	else:
		pass

	
	# Remove Oh (state)
	oh = ' Oh$' # Shouldn't match 'Ohio St.'
	if re.search(oh, address):
		oh = re.search(oh, address).group()
		address = address.replace(oh, '')

	# Get city
	cities = lists.cities
	city_count = len(cities)
	for c in cities:
		if c in address:
			city = c
			index = address.find(city)
			address = address[:index - 1]
			break

		else:
			city_count -= 1

	if city_count <= 0:  # Case in which no city match found
		# If tax mailing address == parcel address, grab city and zip
		tax_addy = driver.find_element_by_id('ContentPlaceHolder1_Base_fvDataMailingAddress_MailingAddressLine2Label')
		tax_addy = tax_addy.get_attribute('innerHTML').title()
		
		if tax_addy[:7] == address[:7]:
			
			city_zip = driver.find_element_by_id('ContentPlaceHolder1_Base_fvDataMailingAddress_MailingAddressLine3Label')
			city_zip = city_zip.get_attribute('innerHTML').title()
			
			city_count = len(cities)
			for c in cities:
				if c in city_zip:
					city = c
					break

				else:
					city_count -= 1
			
			if city_count <= 0:
				city = 'Not available, my dude.'
			else:
				pass
		else:
			city = 'Not available, my dude.'

	else:
		pass


	# Ordinal abbreviation correction
	ord_nums = '[0-9]+[A-Z][a-z]'
	search = re.search(ord_nums,address)
	if search:
		match = search.group(0)
		ord_abbr = match[-2:]
		ordinals = [
			['St','st'],
			['Nd','nd'],
			['Rd','rd'],
			['Th','th'],
			]
		for i in range(len(ordinals)):
			if ord_abbr == ordinals[i][0]:
				address = address.replace(ordinals[i][0],ordinals[i][1])


	# Compass direction correction
	dir = [
		['Ne', 'NE'],
		['Se', 'SE'],
		['Sw', 'SW'],
		['Nw', 'NW'],
	]
	for i in range(len(dir)):
		for j in range(len(dir[i])):
			if j == 0:
				if dir[i][j] in address:
					address = address.replace(dir[i][j],dir[i][j + 1])
	
	# Quotes won't be accepted by the final output in the html input value='string'
	if '\'' in address:
		address = address.replace('\'','&apos;')
		
	return [address, city, zip]
	
	
	
def getOwner(driver):
	
	owner = driver.find_element_by_id('ContentPlaceHolder1_Base_fvDataProfile_OwnerLabel')
	owner = owner.get_attribute('innerHTML')
	
	owner = owner.title()

	if '.' in owner:
		owner = owner.replace('.','')
		
	if '&' in owner:
		owner = owner.replace('&','')
	
	
	# Comma after last name for individuals
	if 'Llc' not in owner:
		owner = owner.replace(" ",", ",1)
		# Add: Predict if second person has last name, insert comma
		# Add: II, III case corrections
	
	# LLC correction
	else:
		owner = owner.replace('Llc','LLC')
		
	# Amper sign correction
	if 'Amp;' in owner:
		owner = owner.replace('Amp;','&')
	
	# Quotes won't be accepted by the final output in the html input value='string'
	if '\'' in owner:
		owner = owner.replace('\'','&apos;')
	
	return owner
	


def getLegal(driver):
	
	legal_desc = driver.find_element_by_id('ContentPlaceHolder1_Base_fvDataLegal_LegalDescriptionLabel')
	legal_desc = legal_desc.get_attribute('innerHTML')
	
	legal_desc = legal_desc.title()
	
	

	# Compass direction correction
	dir = [
		['Ne', 'NE'],
		['Se', 'SE'],
		['Sw', 'SW'],
		['Nw', 'NW'],
		]
	for i in range(len(dir)):
		for j in range(len(dir[i])):
			if j == 0:
				if dir[i][j] in legal_desc:
					legal_desc = legal_desc.replace(dir[i][j],dir[i][j + 1])

	# Add: All'T correction
	if 'All\'T' in legal_desc:
		legal_desc = legal_desc.replace('All\'T', 'All\'t')

		
		
	tax_code = driver.find_element_by_id('ContentPlaceHolder1_Base_fvDataGeographic_TaxCodeLabel')
	tax_code = tax_code.get_attribute('innerHTML')
	tax_code = (tax_code[5:]).title()

	# CSD and LSD correction
	if "Csd" in tax_code:
		tax_code = tax_code.replace("Csd","CSD")
	if "Lsd" in tax_code:
		tax_code = tax_code.replace("Lsd", "LSD")

	legal = legal_desc + tax_code
	
	# Quotes won't be accepted by the final output in the html input value='string'
	if '\'' in legal:
		legal = legal.replace('\'','&apos;')
		
	return legal

	
	
def getDims(driver, parcel):

	driver.find_element_by_link_text('Land').click()
	land_table = driver.find_element_by_id('ContentPlaceHolder1_Land_gvDataLand')
	land_table = land_table.get_attribute('innerHTML')
	land_table = soup(land_table, 'html.parser')
	table_rows = land_table.findAll('tr')
	
	table = []
	for r in table_rows:
		if table_rows.index(r) == 0:
			row = r.findAll('th')
			new_row = []
			for t in row:
				new_row.append(str(t.contents)[3:-2])
			table.append(new_row)
		else:
			row = r.findAll('td')
			new_row = []
			for t in row:
				# Deal with non-breaking space in Latin1
				if t.contents == [u'\xa0']:
					# Replace with empty string
					new_row.append('')
				else:
					new_row.append(str(t.contents)[3:-2])
			table.append(new_row)


	# Check if dims are acreage based or feet
	ac_dx = table[0].index('Acreage')
	front_dx = table[0].index('Frontage')
	if table[1][front_dx] == '':
		
		ac_sum = 0
		for r in table[1:]:
			ac_sum += float(r[ac_dx])
		
		#Convert to feet
		sq_ft = ac_sum * 43560.0
		
		print 'Opening parcel in Stark ArcGIS...'
		# Open ArcGIS Stark County ZOning Map
		url = 'https://starkcountyohio.maps.arcgis.com/apps/webappviewer/index.html?id=03f862c83bd0426588b5571afe59a407'
		driver.get(url)
		
		# Wait for the page to load and the pop-up to load
		time.sleep(15) 
		
		#driver.find_element_by_class_name('jimu-btn jimu-float-trailing enable-btn').click()
		driver.find_element_by_xpath("//*[text()='OK']").click()
		
		inp = driver.find_element_by_id('esri_dijit_Search_0_input')
		inp.send_keys(parcel)
		
		driver.find_element_by_class_name('searchSubmit').click()
		
		# Open measurement tool
		driver.find_element_by_xpath("//img[contains(@src,'/apps/webappviewer/widgets/Measurement/images/icon.png?wab_dv=2.8')]").click()
		
		# Select yard stick
		time.sleep(3)
		driver.find_element_by_id('dijit_form_ToggleButton_1').click()
		
		# Select unit dropdown
		time.sleep(3)
		driver.find_element_by_id('dijit_form_DropDownButton_0_label').click()
		
		# Select feet
		time.sleep(3)
		driver.find_element_by_id('dijit_MenuItem_3_text').click()
		
		# Get user's measurement of frontage
		def checkFloatInput(txt):
			inp = raw_input(txt)
			try:
				inp = float(inp)
				return inp
			except:
				checkFloatInput(txt)
		
		txt = 'Type the parcel\'s frontage in feet by using the Measurement tool: '
		frontage = checkFloatInput(txt)
		
		depth = sq_ft / frontage
		
		
		
			
	else:
		#Unit feet frontage mod
		# Is it the case that if there are more htan 1 row of frontage and depth feet then depth is always the same?
		
		# Get total sum sq ft. Get total frontage.  sq ft / frontage = depth
		
		sf_dx = table[0].index('SF Area')
		tot_sq_ft = 0
		for r in table[1:]:
			sq_ft = r[sf_dx]
			# Chop off decimal if one ever appears
			if '.' in sq_ft:
				sq_ft = sq_ft[:sq_ft.index('.')]
			sq_ft = sq_ft.replace(',','')
			sq_ft = int(sq_ft)
			tot_sq_ft += sq_ft
			
		frontage = 0
		for r in table[1:]:
			f = r[front_dx].replace(',','')
			# Chop off decimal if one ever appears
			if '.' in f:
				f = f[:f.index('.')]
			f = int(f)
			frontage += f
		
		depth = tot_sq_ft / frontage
		
		sq_ft = tot_sq_ft
			

	return [int(frontage), int(depth), int(sq_ft)]
		
	
	
def getTaxes(driver):

	driver.find_element_by_link_text('Tax').click()
	
	tax_table = driver.find_element_by_id('ContentPlaceHolder1_Tax_gvDataTaxBilling')
	tax_table = tax_table.get_attribute('innerHTML')
	tax_table = soup(tax_table, 'html.parser')
	table_rows = tax_table.findAll('tr')
	
	for r in table_rows:
		table_tds = r.findAll('td')
		
		for c in table_tds:
			if str(c.contents)[3:-2] == 'Total:':
				tax = (str(table_tds[2].contents)[3:-2])
				break
				
			else:
				pass
	
	tax = tax.replace(' ','')
	tax = tax.replace(',','')
	tax = float(tax)
	
	
	# Special Assessments. Sum and subtract from tax. Return sum, description sentence
	tax_table = driver.find_element_by_id('ContentPlaceHolder1_Tax_gvSpecials')
	tax_table = tax_table.get_attribute('innerHTML')
	tax_table = soup(tax_table, 'html.parser')
	table_rows = tax_table.findAll('tr')
	
	# Check if any spec ass data (the table will only have 1 row, saying no data)
	if len(table_rows) == 1:
		
		spec_sum = 0
		spec_desc = None
		
	else:
	
		table = []
		for r in table_rows:
			if table_rows.index(r) == 0:
				table_ths = r.findAll('th')
				row = []
				for c in table_ths:
					row.append(str(c.contents)[3:-2])
				table.append(row)
				
			else:
				table_tds = r.findAll('td')
				row = []
				for c in table_tds:
					row.append(str(c.contents)[3:-2])
				table.append(row)
		
		
		code_dx = table[0].index('Code')
		agency_dx = table[0].index('Agency')
		amt_dx = table[0].index('StandardAmount')
		
		spec_ass = [False, False]
		spec_sum = 0.0
		lights_sum = 0.0
		lights_cnt = 0.0
		for r in table:
			# Street lighting assessment. Finds the most recent one (last one mentioned in table)
			if 'LIGHTING' in r[code_dx]:
				lights = r[agency_dx] + r[code_dx][4:]
				lights = lights.title()
				spec_ass[0] = lights
				
				amt = r[amt_dx].replace('$','')
				lights_sum += float(amt)
				lights_cnt += 1
			
			# Watershed assessment. Finds the most recent one (last one mentioned in table)
			elif 'WATERSHED' in r[code_dx]:
				shed = r[code_dx][5:]
				shed = shed.title()
				spec_ass[1] = shed		
				amt = r[amt_dx].replace('$','')
				shed_amt = 6.0
			else:
				pass
		
		# Write spec. assessent description strings (one plural, other singular)
		if spec_ass.count(False) == 1:
			for a in spec_ass:
				if a != False:
					spec_desc = 'There is an assessment for %s.' % a
				else:
					pass
		else:
			spec_desc = 'There are assessments for %s and %s.' % (spec_ass[0], spec_ass[1])
		
		# Average lights assessment, get assessment sum
		if lights_cnt > 0:
			lights_avg = lights_sum / lights_cnt
			spec_sum = (lights_avg * 2) + shed_amt
		else:
			spec_sum = shed_amt
	
	tax = tax - spec_sum
	
	return [tax, spec_sum, spec_desc]
	
	
	
def getHood(driver, legal):
	# Grab school district from legal string
	hood_dx = legal.index(' - ') + 3
	hood = legal[hood_dx:]
	# Remove LSD or CSD
	hood = hood[:-4]
	
	map_ref = None
	for h in lists.hoods:
		# In cases where multiple hood names are combined into one map ref (see lists.hoods)
		if h[0] > 1:
			for i in h:
				if hood == i:
					map_ref = h[1]
		# Only one hood to one map ref #
		else:	
			if hood == h[0]:
				map_ref = h[1]
		
	if map_ref == None:
		map_ref = 'No match found for %s.' % hood
		# If there are cases in which the school district does not match to a neighborhood name in lists,
		# then should give a list of choices to user. or make note of such cases and program them in, each one

	return [hood, map_ref]

	
	