import mods as m



# Testing switch
import testmode
testing = testmode.testmode()



### Get order
print 'Save order and purchase agreement from client.'



### Make new folder for order and initiate HTML file
if testing == False:
	order = raw_input('The order file name, eg 231page, please: ') # Ex: 231page
else:
	order = '7084blue'
	print 'In testing mode, using order %s.' % order
	

content = m.startHTML(order)

content += '''<div class='inputBox'>
<label for='Tab'>Tab</label>
<input type='text' name='Tab' id='Tab' value='Hit tab, bro' autofocus>
</div><br>
'''

content += m.formInput('File #', order)

m.makeFolder(order)
m.writeFile(order, order + '.html', content, 'w')



### Set webdriver
# Move .exe file into program directory, update path below
driver = m.web.Chrome(executable_path="C:/root/chromedriver.exe")



### Search order on auditor
# !!! Need to cut street name down to first 3 char, eg in 5185 Sea Pines / 5185seap
# !!! If throws error in searching, handle exception and just ask for user input parcel number
print 'Searching order on Auditor...'
parcel = m.getParcel(driver, order)



### Get address, city, and zip
# !!! Tweak Ordinal transformation to only transform char-char-space, eg 'SE ', so avoids SEa Pines
address_parts = m.getAddress(driver)



### Get owner
owner = m.getOwner(driver)



### Get legal description and tax code
legal = m.getLegal(driver)



### Get Taxes minus Special Assessments
taxes = m.getTaxes(driver)



### Get neighborhood (School district) and its map reference #
hood = m.getHood(driver, legal)



### Dimensions and area of land
dims = m.getDims(driver, parcel)



### Today's date
today = m.dt.datetime.strftime(m.dt.datetime.today(),'%m/%d/%Y')



### Write data to HTML
content = m.formInput('Address', address_parts[0]) 
content += m.formInput('City', address_parts[1])
content += m.formInput('Zip', address_parts[2])
content += m.formInput('Owner', owner)
content += m.formInput('Legal Desc.', legal)
content += m.formInput('Parcel', parcel)

content += m.formInput('Taxes', taxes[0])

content += m.formInput('Neighborhood', hood[0])
content += m.formInput('Map Ref.', hood[1])

content += m.formInput('Special Ass.', taxes[1]) # Special assessment total

content += m.formInput('Frontage', dims[0])
content += m.formInput('Depth', dims[1])
content += m.formInput('Area', dims[2])

content += m.formInput('Ext. Factors', taxes[2]) # ie special assessment(s) description

content += m.formInput('Effective Date', today)

m.writeFile(order, order + '.html', content, 'a')



### Download the Auditor Property Card PDF
if testing == False:
	print 'Chill, just downloading the Auditor Card...'
	r = m.reqs.get('http://ddti.starkcountyohio.gov/RecordCard.aspx?ParcelID=' + parcel)

	with open(order + '/' + order + '-2-auditor.pdf', 'wb') as f:
		f.write(r.content)

	print 'Auditor card saved.'
	
else:
	pass
	
	
	
pause = raw_input('Complete. Thank you.')

