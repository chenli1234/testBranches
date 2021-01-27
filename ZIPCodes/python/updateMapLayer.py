# TomTom Zipcode: Get/Insert/Modify layers for Name/Definition_Query referencing new release
# Python 3.6.10  2020/12/23 Chen Li
'''
1. Get new release by folder name under download folder dir_download = r'D:\SourceZIP' # folder of current downloaed release containing nam2020_12_00 like.
2. Get/Insert/Modify layers to new release date by updating layer Name/Definition_Query
'''
import arcpy
import re
import os, datetime

dir_download = r'D:\SourceZIP' # folder of current downloaed release containing nam2020_12_00 like.
fileLyr = r'D:\Project\GDL\ZIPCodes\aprx\ZIP Codes Archive.lyrx' # ArcGIS Pro layer file
lyrNameGrpRoot = 'ZIP Codes Archive'
lyrNameGrp_start = 'ZIP Codes, ' # ZIP Codes, (March 2020, © 2006-2020 TomTom)
lyrNameGrp_end = r', © 2006-20\d\d TomTom' # (ZIP Codes, March 2020), © 2006-2020 TomTom
lyrNameGrp_pattern = '^'+lyrNameGrp_start+r'\D+ 20\d\d'+lyrNameGrp_end+'$' # ZIP Codes, March 2020, © 2006-2020 TomTom (^: start with; $: end with)

# get current relase version: TomTom_202009
dir_release = os.listdir(dir_download)
dir_release.sort(reverse=True,key=str.lower)
for d in dir_release:
    if re.match('TomTom_20\d{4}',d): # TomTom_20####
        ym = d[7:] # 202009
        break
releaseS = ym[:4]+'.'+ym[4:] # 2020.09
releaseL = datetime.datetime.strptime(ym[4:], "%m").strftime('%B') + ' ' + ym[:4] # September 2020

# get first layer group: ZIP Codes, December 2020, © 2006-2020 TomTom
lyrFile = arcpy.mp.LayerFile(fileLyr)
for lyr in lyrFile.listLayers():
    if re.match(lyrNameGrp_pattern, lyr.name):
        lyrGrpZip = lyr
        print(lyr.name)
        break
    
# get month year: September 2020
releaseL_old = re.findall(lyrNameGrp_start+r'(\D+ 20\d\d)' + lyrNameGrp_end, lyrGrpZip.name)[0]

lyrFile.insertLayer(lyrGrpZip,lyrGrpZip,'AFTER')
lyrGrpZip.name = re.sub('^'+lyrNameGrp_start+r'\D+ 20\d\d', lyrNameGrp_start + releaseL, lyrGrpZip.name) # rename to new data: December 2020
for lyr in lyrGrpZip.listLayers():
    lyr.name = lyr.name.replace(releaseL_old, releaseL)
    if lyr.isFeatureLayer:
        cim_lyr = lyr.getDefinition('V2')
        exp = cim_lyr.featureTable.definitionFilterChoices[0].definitionExpression
        expNew = re.sub(r"LIKE '%20\d{2}.\d{2}%'", "LIKE '%" + releaseS + "%'", exp)
        cim_lyr.featureTable.definitionFilterChoices[0].definitionExpression = expNew # bug, need both line for replace old query, not add 
        cim_lyr.featureTable.definitionExpression = expNew # "LIKE '%2020.12%"
        lyr.setDefinition(cim_lyr)
lyrFile.saveACopy(r'D:\Project\GDL\ZIPCodes\aprx\ZIP Codes Archive Added Layer.lyrx')

    #if lyr.supports("datasource"):
        #print(lyr.name)

# add/update layers for Name and Definition Query to current ZipCode release