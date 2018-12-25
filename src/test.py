import py2snes

conn = py2snes.usb2snes()
conn.Attach()
print(conn.Info())
