# TomTom Zipcode: Append new ZIP Code release to Geodatabase
# Python 3.6.10  2021/01/07 Chen Li
'''
1. Get new release by folder name under download folder dir_download = r'D:\SourceZIP' # folder of current downloaed release containing nam2020_12_00 like.
2. Join to polygon shapefile usauwa___________pd.shp from table usauwa___________pdnm.dbf for attribute Name
3. Join to point shapefile usauwa___________pl.shp from table usauwa___________plnm.dbf for attribute Name
4. Append to GDB ZIP_Area and ZIP_Point
5. Calculate release_version, publish_date, arcieve_date, and other fields 
'''

import arcpy
import re
import os, datetime

folder_download = r'D:\SourceZIP' # folder of current downloaed release containing nam2020_12_00 like.
shp_pd = 'usauwa___________pd.shp'
shp_pl = 'usauwa___________pl.shp'
dbf_pdnm = 'usauwa___________pdnm.dbf'
dbf_plnm = 'usauwa___________plnm.dbf'

EGDB = r'\\dshs\gis\Services\Data\content\ZIPCodes\dbconx\DSHSGIS gisdata on GDLPublicDev.sde'
pd_egdb = EGDB+'\\aTestZipAreaChenLi'
pl_egdb = EGDB+'\\aTestZipPointChenLi'
#pd_egdb = EGDB+'\\ZIP_area_new'
#pl_egdb = EGDB+'\\ZIP_point_new'

fgdb_tmp = 'fgdb_tmp.gdb' # temp fgdb for data projection output (in_meory not supported) and other data preparing

arcpy.env.overwriteOutput = True

msg = '%s Start ...' % datetime.datetime.now()
print(msg)
# get current relase Zip code shapefile folder and files
folders_release = os.listdir(folder_download)
folders_release.sort(reverse=True,key=str.lower) # latest folder to top of the list
for folder in folders_release:
    if re.match('TomTom_20\d{4}',folder): # TomTom_20#### D:\SourceZIP\TomTom_202012
        d_path = folder_download+'\\'+folder
        folder_shpfile = d_path+'\\'+os.listdir(d_path)[0] # D:\SourceZIP\TomTom_202012\nam2020_12_000
        break
# release version and check if new release already in database
version = folder_shpfile.split('\\')[-1:][0].replace('_','.').replace('nam', 'TomTom MultiNet Post NAM ')  # D:\SourceZIP\TomTom_202012\nam2020_12_000 > TomTom MultiNet Post NAM 2020.12.000
with arcpy.da.SearchCursor(pd_egdb, "OBJECTID", "ReleaseVersion = '"+ version +"'") as cursor:
   for row in cursor:
      print("<Warning, process stopped> %s already updated to %s from %s" %(version, pd_egdb, folder_shpfile))
      exit()
      break
      
# source zip area/point, and tables for zip names
fc_pd = os.path.join(folder_shpfile,shp_pd)
fc_pl = os.path.join(folder_shpfile,shp_pl)
tb_pdnm = os.path.join(folder_shpfile,dbf_pdnm)
tb_plnm = os.path.join(folder_shpfile,dbf_plnm)


# create temp fgdb for data preparing

arcpy.env.workspace = os.path.join(folder_shpfile,fgdb_tmp)

if not arcpy.Exists(arcpy.env.workspace): 
    arcpy.CreateFileGDB_management(folder_shpfile,fgdb_tmp)


# project to NAD 1983 HARN StatePlane Washington South FIPS 4602 (US Feet)
msg = '%s Project source shapefile %s to fgdb %s with datum transformation WGS_1984_(ITRF00)_To_NAD_1983_HARN ...' % (datetime.datetime.now(), fc_pd, arcpy.env.workspace)
print(msg)
arcpy.Project_management(fc_pd, 'pd', arcpy.SpatialReference(2927), 'WGS_1984_(ITRF00)_To_NAD_1983_HARN')
msg = '%s Project source shapefile %s to fgdb %s with datum transformation WGS_1984_(ITRF00)_To_NAD_1983_HARN ...' % (datetime.datetime.now(), fc_pl, arcpy.env.workspace)
print(msg)
arcpy.Project_management(fc_pl, 'pl', arcpy.SpatialReference(2927), 'WGS_1984_(ITRF00)_To_NAD_1983_HARN')

# add/calculate fields for 'ReleaseVersion', 'FeatureType', 'AreaSqMi', 'GDLPublishDate'
msg = '%s calculate pd ReleaseVersion, FeatureType, AreaSqMi, GDLPublishDate ...' % datetime.datetime.now()
print(msg)
arcpy.CalculateField_management('pd','ReleaseVersion',"'"+version+"'")
arcpy.CalculateField_management('pd','FeatureType',"'Postal Code'")
date_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') 
arcpy.CalculateField_management('pd','GDLPublishDate',"'"+date_now+"'")
arcpy.CalculateField_management('pd','AreaSqMi',"!SHAPE_Area! / 27880000")
arcpy.CalculateField_management('pd','ZIP',"!POSTCODE!") # rename field for match/Append to EGDB with no FieldMaps
arcpy.CalculateField_management('pd','SourceID',"!ID!") # rename field for match/Append to EGDB without FieldMaps

# copy name tables with records of 'ON' type only
arcpy.TableToTable_conversion(tb_pdnm, arcpy.env.workspace, 'pdnm', "NAMETYP = 'ON'")
##arcpy.TableToTable_conversion(tb_plnm, arcpy.env.workspace, 'plnm', "NAMETYP = 'ON'")

# join to Zipcode Postal_Area from table Postal_Area_Name for Name attribute
msg = '%s join attribute pd with pdnm and calculate POName ...' % datetime.datetime.now()
print(msg)
fc_joined_area = arcpy.AddJoin_management('pd', 'ID', 'pdnm', 'ID') # 1 to many, likely joined to 'ON' with smal OBJECTID, not 'PY, PN'
arcpy.CalculateField_management(fc_joined_area,'POName',"!pdnm.NAME!")
arcpy.RemoveJoin_management(fc_joined_area)
# Zipcode Area append new release to geodatabase
msg = '%s append new release Zip area to %s ...' % (datetime.datetime.now(), pd_egdb)
print(msg)
arcpy.Append_management('pd', pd_egdb, 'NO_TEST') 

# join to Zipcode Place point and calculate from table Place_Name for Enclude Zipcode of postal district and Enclude Zipcode Name
##fc_joined_point = arcpy.AddJoin_management('pl', 'TRPELID', 'plnm', 'ID')
msg = '%s spatial join zip point with Zip area for enclosing Zip Area code ...' % (datetime.datetime.now())
print(msg)
arcpy.SpatialJoin_analysis('pl', 'pd', 'pl_sj')

# Zipcode Point append new release to geodatabase
msg = '%s truncate and append new release Zip point to %s ...' % (datetime.datetime.now(), pl_egdb)
print(msg)
fldMatch = (['pl_sj','POSTCODE','ZIP'],
            ['pl_sj','POSTLEN','ZIPLength'],
            ['pl_sj','POSTCODE_1','EncZIP'],
            ['pl_sj','POName','EncPOName'],
            ['pl_sj','POSTTYP','Featuretype'],
            ['pl_sj','REleaseVersion','ReleaseVersion'],
            ['pl_sj','ID','SourceID'],
            ['pl_sj','GDLPublishDate','GDLPublishDate']) # [table append from, field from, field to]
fms = arcpy.FieldMappings()
for f in fldMatch:
    fm = arcpy.FieldMap()
    fm.addInputField(f[0],f[1]) # table, field
    fmOutFld = fm.outputField
    fmOutFld.name = f[2]
    fm.outputField = fmOutFld
    fms.addFieldMap(fm)
arcpy.TruncateTable_management(pl_egdb)
arcpy.Append_management('pl_sj', pl_egdb, 'NO_TEST', fms) 

# calculate archive_date for previous release EGDB, that is null and not current release
pd_pre = arcpy.SelectLayerByAttribute_management(pd_egdb,'NEW_SELECTION', "GDLArchiveDate IS NULL And ReleaseVersion <> '" + version + "'")
arcpy.CalculateField_management(pd_pre,'GDLArchiveDate',"'"+date_now+"'")
#pl_pre = arcpy.SelectLayerByAttribute_management(pl_egdb,'NEW_SELECTION', "GDLArchiveDate IS NULL And ReleaseVersion <> '" + version + "'")
#arcpy.CalculateField_management(pl_pre,'GDLArchiveDate',"'"+date_now+"'")

# 
msg = '%s DONE. TomTom ZIP new release %s updated to %s & %s.' % (datetime.datetime.now(), version, pd_egdb, pl_egdb)
print(msg)
print()
# append to gdb\

# to do: Domain for zip point featuretype; create test dataTestZipPointChenLidshs\gisdata   NewDay21##eGDBOwner!
