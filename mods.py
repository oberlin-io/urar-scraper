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

	else:
		response = ''

		
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
			

	return [frontage, depth, sq_ft]
		
		
