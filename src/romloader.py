import sys
import os
import py2snes
import yaml
import fnmatch
from time import sleep

### load the configuration file (if it exists, otherwise use default config)
scriptpath=os.path.dirname(sys.argv[0])

try:
    with open(scriptpath + "\\romloader.yaml") as configfile:
        try:
            config = yaml.load(configfile)
        except yaml.YAMLError as e:
            print(e)
            sys.exit(1)
except FileNotFoundError:
    try:
        with open("romloader.yaml") as configfile:
            try:
                config = yaml.load(configfile)
            except yaml.YAMLError as e:
                print(e)
                sys.exit(1)
    except FileNotFoundError:
        config = {"default_destination": '/romloader'}

def main():
    try:
        rompath=sys.argv[1]
    except IndexError:
        print('We need a path to the ROM file to load.')
        sys.exit(1)
    filename=os.path.basename(rompath)

    ### initiate connection to the websocket server
    conn = py2snes.usb2snes()

    ### Attach to usb2snes, use the device configured if it is set, otherwise have it find the first device.
    if "device" in config:
        print('Attaching to specified device {device}'.format(
            device=config['device']
        ))
        com = conn.Attach(config['device'])
    else:
        print('Attaching to first device found.')
        com = conn.Attach()
    print('Attached to device \"{com}\"'.format(
        com = com
    ))

    conn.Name('RomLoader')

    rule = matchrule(filename)
    if rule:
        if len(config['rules'][rule]['destinations']) == 1:
            path = config['rules'][rule]['destinations'][0]['path']
            try:
                romname = config['rules'][rule]['destinations'][0]['romname']
            except KeyError:
                romname = filename
        elif len(config['rules'][rule]['destinations']) == 0:
            path = config['default_destination']
            romname = filename
        else:
            path, romname = get_destination(rule, filename)
    else:
        path = config['default_destination']
        romname = filename
    print("making {path} directory if it doesn't exist".format(
        path=path
    ))
    conn.MakeDir('/romloader')
    conn.List(path)
    print("copying rom to {fullpath}".format(
        fullpath=path + '/' + romname
    ))
    conn.PutFile(rompath,path + '/' + romname)
    print("verifying rom copy is complete")
    conn.List(path)
    print("booting rom")
    conn.Boot(path + '/' + romname)
    conn.close()

def matchrule(name):
    if "rules" in config:
        for rule in config['rules']:
            if fnmatch.fnmatch(name, config['rules'][rule]['name_pattern']):
                return rule
    else:
        return None

def get_destination(rule, romname):
    print('----------------------------')
    for idx, dest in enumerate(config['rules'][rule]['destinations']):
        print(str(idx) + ' - ' + dest['name'])
    destination_index = input('What destination (enter to chose 0)? ')
    print(destination_index)
    if destination_index == '':
        destination_index = 0
    path = config['rules'][rule]['destinations'][int(destination_index)]['path']
    try:
        name = config['rules'][rule]['destinations'][int(destination_index)]['romname']
    except KeyError:
        name = romname
    return path, name

    sleep(15)

main()