# TomTom Zipcode: Download, Extract, Zip & Backup  Python 3.6.10  2020/12/10 Chen Li
# https://api.tomtom.com/mcapi/swagger-ui.html
'''
v1
Prepare TomTom Zipcode source data ready for feature class update (\\dshs\gis\Services\Data\content\ZIPCodes\ZIPCodeUpdateETL_tmplt\Procedure.docx)
Download/extract to D:\SourceZIP\TomTom_202012\namYYYY_mm_000
Backup to \\dshs\gis\Services\Data\content\ZIPCodes\TomTom Source\namYYYY_mm_000.zip
'''

# "C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python" -m pip install py7zr
#import py7zr

import requests, json
import subprocess
import os, os.path, shutil
from datetime import datetime

dir_bu = r'\\dshs\gis\Services\Data\content\ZIPCodes\TomTom Source'
dir_download = r'D:\SourceZIP'

url_tomtom = "https://api.tomtom.com/mcapi/families"
Authorize = "e05DEQH0dttAZ8EKqvCoFY1vOXof0SVCvJjrVwUNJYvi6Mv5JPG3pFC6RWEH4w9fCDWm3vobuj9e2Vux9khTwIwzbA109YlM5xfX" # Start KeePass > TomTom > “TomTom Map Content Portal” > Note > API Key:

headers = {"Authorization": Authorize}

exe = r'C:\Program Files\7-Zip\7z.exe'

def download():
    # https://api.tomtom.com/mcapi/swagger-ui.html#/
    # TomTom families
    data = json.loads(requests.get(url_tomtom, headers=headers).text) 
    location = data['content'][0]['location'] # https://api.tomtom.com/mcapi/families/532037

    # TomTom latest-release iterationType eq 'commercial' and deliveryType eq 'full'
    url = location + "/latest-releases?filter=iterationType%20eq%20'commercial'%20and%20deliveryType%20eq%20'full'" # https://api.tomtom.com/mcapi/families/ID/latest_releases
    data = json.loads(requests.get(url, headers=headers).text)

    for product in data['products']:
        if product['product']['name'] == 'NAM':
            version = product['releases'][0]['version']
            file_bu = dir_bu + r'\nam' + version.replace(".","_") + '.zip'
            if os.path.isfile(file_bu):
                print('Program exited. Download same version exists at %s' % file_bu)
                exit()
            location = product['releases'][0]['location'] # https://api.tomtom.com/mcapi/releases/35639499
            if not os.path.exists(dir_download):
                os.makedirs(dir_download)
            dir_download_v = dir_download + '\\TomTom_' + version.replace('.','')[:6]
            os.makedirs(dir_download_v)
        break

    # TomTom product releases of the product
    os.chdir(dir_download_v)
    url = location # + '?zone=NAM.USA.WA.UWA'
    data = json.loads(requests.get(url, headers=headers).text)

    for content in data['contents']:
        location = content['location'] # https://api.tomtom.com/mcapi/contents/35993210
        # TomTom download url
        url = location + '/download-url'
        data = json.loads(requests.get(url, headers=headers).text)
        location = data['url']
        file_name = content['name'] # https://djcz9xupugevr.cloudfront.net/24....
        r = requests.get(location, headers=headers)
        with open(file_name,'wb') as f:
            f.write(r.content)
        subprocess.call(exe + ' x ' + file_name, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    return(dir_download_v + '\\nam' + version.replace(".","_")) # unzipped dir

def deleteFiles(dir_files, file_except):
    files = os.listdir(dir_files) # D:\SourceZIP\TomTom_202012\nam2020_12_000\components\mnp\coordinates
    for file in files:
        if file != file_except:
            try:
                os.remove(dir_files + '\\' + file)
            except:
                shutil.rmtree(dir_files + '\\' + file)

def timestamp():
        ts = datetime.now()
        return ts.strftime("%Y-%m-%d" + " " + "%H:%M:%S")

msg = '%s - Download and Extract ...' % timestamp()
print(msg)
dir_extract = download() # D:\SourceZIP\TomTom_202012\nam2020_12_000
#dir_extract = r'D:\SourceZIP\TomTom_202012\nam2020_12_000'
msg = '%s - Delete files other than WA ...' % timestamp()
print(msg)
files = [[dir_extract + r'\components\mnp\coordinates','usauwa_pl.txt.gz'],
         [dir_extract + r'\components\mnp\fgdc\html', 'usa'],
         [dir_extract + r'\components\mnp\fgdc\html\usa', 'uwa'],
         [dir_extract + r'\components\mnp\fgdc\xml', 'usa'],
         [dir_extract + r'\components\mnp\fgdc\xml\usa', 'uwa'],
         [dir_extract + r'\shpd\mnp\usa', 'uwa']]
for dir_except in files:
    deleteFiles(dir_except[0],dir_except[1])

msg = '%s - Extract Shapefile ... to %s' % (timestamp(), dir_extract)
print(msg)
subprocess.call(exe + ' x ' + dir_extract + r'\shpd\mnp\usa\uwa\* -o'+dir_extract, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
shutil.rmtree(dir_extract + r'\shpd')
msg = '%s - Zip and backup ... %s > %s' % (timestamp(),dir_extract + '.zip', dir_bu)
print(msg)
subprocess.call(exe + ' a ' + dir_extract + '.zip ' + dir_extract, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL) # OK for the warning
shutil.move(dir_extract + '.zip ', dir_bu)
msg = '%s - Done.' % timestamp()
print(msg)
exit()

