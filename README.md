# RomLoader for sd2snes

Lets you easily load a ROM onto your sd2snes by using usb2snes!  Great for Rando runners, and especially great for MSU-1 users.

## Building it yourself

You'll need a working Python 3.6 environment.  I've only tested this with Python 3.6.

1. Install pyinstaller so you can build the exe, which is a packaged python distribution (no dependancy on python) - `pip install pyinstaller`
2. Install the required packages, hopefully requirements.txt is complete - `pip install -r requirements.txt`
3. Build the project - `pyinstaller --onefile src/romloader.py`

Usable executable should be in the build directory.

## Usage

Put romloader.exe in a place that is likely not to change.  Copy romloader.yaml to the same directory as your romloader.exe if you want to customize the behavior.  Have Windows open the .sfc or .smc file with romloader.exe!

You'll need usb2snes firmware and the usb2snes software running on your PC.  You can find it at https://github.com/RedGuyyyy/sd2snes/releases/tag/usb2snes_v9

## Configuration

By default, without a config file, it'll use /romloader for all files.

You can customize the behavior though with a romloader.yaml file in the same directory.

`device` is the usb2snes device you want romloader to use, leave this out to have it use the first one it finds (recommended)

`default_destination` is the directory where ROMs will be put on your SD card if no rules are matched.  If you change this, make sure the directory exists on your SD card.

`rules` this is the meat and potatoes.  You can create rules for each of your games here.

### rules section

The `rules` section has an arbitrary name, and then under that a `name_pattern` key which is an string to wildcard match to the filename.

Each rule has a `destinations` key which is a yaml list of various destinations for your matched file.  The first item in the list will be the default.
If `romname` is not found as a key within the list, it will copy the name of the file as-is to the SD card.  If only one destination for the rule is specified, it will use that automatically.  If more than one destination is specified, it will prompt you.

Example of the prompt:

```
Attaching to first device found.
Attached to device "SD2SNES COM3"
----------------------------
0 - default
1 - aLttPArranged
2 - aLttPDeMastered
3 - EpicAnniversaryOST
4 - SuperMarioRPG
5 - Zelda3FMProject
6 - ZeldaMetal
7 - ZeldaReOrchestrated
What destination (enter to chose 0)?
```


### example config file
```yaml
### device option can be commented out to have this tool use the first sd2snes device it finds, which in most cases is fine.
### If you have multiple sd2snes units connected, you'll need to specify the one you want to use.

# device: "COM3"

### default directory to put the ROM if no rules are matched.
### Make sure this directory exists on your SD card (will try to create it if /romloader)
default_destination: "/romloader"

### a set of rules to use to put certain ROMs in certain locations, such as your randomizer ROMs, useful for MSU1 users
rules:
  alttpr:
    name_pattern: "ALttP - VT_*" # look for an input ROM that matches this name
    destinations:
      - name: default
        path: "/LinkToThePast/Transferred"
      - name: aLttPArranged
        path: "/LinkToThePast/MSU1/aLttPArranged"
        romname: alttp_msu.sfc
      - name: aLttPDeMastered
        path: "/LinkToThePast/MSU1/aLttPDeMastered"
        romname: loz3-demaster.sfc
      - name: EpicAnniversaryOST
        path: "/LinkToThePast/MSU1/EpicAnniversaryOST"
        romname: loz3-dx.sfc
      - name: SuperMarioRPG
        path: "/LinkToThePast/MSU1/SuperMarioRPG"
        romname: alttp_msu.sfc
      - name: Zelda3FMProject
        path: "/LinkToThePast/MSU1/Zelda3FMProject"
        romname: track.sfc
      - name: ZeldaMetal
        path: "/LinkToThePast/MSU1/ZeldaMetal"
        romname: track.sfc
      - name: ZeldaReOrchestrated
        path: "/LinkToThePast/MSU1/ZeldaReOrchestrated"
        romname: alttp_msu.sfc
  smz3:
    name_pattern: "SMALttP - sm-*"
    destinations:
      - name: default
        path: "/SMZ3/roms"
  smw:
    name_pattern: "smw-*"
    destinations:
      - name: default
        path: "/SuperMarioWorld/Rando"
  supermetroiditem:
    name_pattern: "Item Randomizer *"
    destinations:
      - name: default
        path: "/SuperMetroid/Rando"
  supermetroidvaria:
    name_pattern: "VARIA_Randomizer_*"
    destinations:
      - name: default
        path: "/SuperMetroid/Rando"
```

## Troubleshooting

**Problem**: RomLoader hangs without any input

**Solution**:
1. try restaring usb2snes.exe
2. power off and back on your sd2snes
3. load a game that doesn't use MSU-1 or a special chip via the sd2snes menu

Basically RomLoader is having trouble interacting with the usb2snes.


**Problem**: MSU-1 music doesn't play as expected.

**Solution**: In my testing, I've noticed that sometimes the music won't load
correctly if another game is currently running, especially other MSU-1 or
special chip games.  Try resetting to the sd2snes menu first before loading
your game.


**Problem**: MSU-1 music freezes and plays a really loud sound while RomLoader is
copying the ROM to the SD card.

**Solution**: This is a current limitation of MSU-1 and usb2snes.  If this is
annoying (especially if streaming), go to the sd2snes menu first before loading
a ROM.