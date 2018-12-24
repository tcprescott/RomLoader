import sys
import os
import py2snes
from time import sleep

try:
    rompath=sys.argv[1]
except IndexError:
    print('We need a path to the ROM file to load.')
    sys.exit()
romname=os.path.basename(rompath)

conn = py2snes.usb2snes()
print("attaching to first sd2snes found")
conn.Attach()
conn.Name('RomLoader')
print("making /romloader directory if it doesn't exist")
conn.MakeDir('/romloader')
print("copying rom")
conn.PutFile(rompath,'/romloader/' + romname)
print("verifying rom copy is complete")
conn.List('/romloader')
print("booting rom")
conn.Boot('/romloader/' + romname)
sleep(10)
conn.close()
