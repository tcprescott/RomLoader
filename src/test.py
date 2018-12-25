import py2snes

conn = py2snes.usb2snes()
conn.Attach()
conn.MakeDir('/pytest2')
# print(conn.List('/pytest'))
