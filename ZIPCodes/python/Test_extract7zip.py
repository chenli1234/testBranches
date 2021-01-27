
# "C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python" -m pip install py7zr

import py7zr
import subprocess

with py7zr.SevenZipFile('test.7z.001', mode='r') as z:
    z.extractall(path=r"./temp")

exe = r'C:\Program Files\7-Zip\7z.exe'

subprocess.call(exe + ' x test.7z.001')