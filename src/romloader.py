import fnmatch
import os
import sys
from time import sleep

import yaml

from py2snes import usb2snes
from py2snes import usb2snesException

def show_exception_and_exit(exc_type, exc_value, tb):
    import traceback
    traceback.print_exception(exc_type, exc_value, tb)
    input("Press key to exit.")
    sys.exit(-1)

sys.excepthook = show_exception_and_exit


# load the configuration file (if it exists, otherwise use default config)
scriptpath = os.path.dirname(sys.argv[0])

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
        rompath = sys.argv[1]
    except IndexError:
        try:
            rompath = config['debug_copypath']
        except:
            raise IndexError('We need a path to the ROM file to load.')
            sys.exit(1)
    filename = os.path.basename(rompath)

    rule = matchrule(filename)
    if rule:
        if len(config['rules'][rule]['destinations']) == 1:
            path = config['rules'][rule]['destinations'][0]['path']
            try:
                romname = config['rules'][rule]['destinations'][0]['romname']
            except KeyError:
                romname = filename
        elif len(config['rules'][rule]['destinations']) == 0:
            try:
                path = config['default_destination']
            except KeyError:
                path = '/romloader'
            romname = filename
        else:
            path, romname = get_destination(rule, filename)
    else:
        try:
            path = config['default_destination']
        except KeyError:
            path = '/romloader'
        romname = filename

    for a in range(10):
        try:
            # initiate connection to the websocket server
            conn = usb2snes()

            devicelist = conn.DeviceList()

            # Attach to usb2snes, use the device configured if it is set, otherwise
            # have it find the first device.
            if "device" in config:
                print('Attaching to specified device {device}'.format(
                    device=config['device']
                ))
                com = conn.Attach(config['device'])
            elif len(devicelist) > 1:
                com = conn.Attach(get_comm_device(devicelist))
            else:
                print('Attaching to first device found.')
                com = conn.Attach()
            print('Attached to device \"{com}\"'.format(
                com=com
            ))

            conn.Name('RomLoader')
            if not rule:
                conn.MakeDir('/romloader')
            conn.List(path)
            print("copying rom to {fullpath}".format(
                fullpath=path + '/' + romname
            ))
            conn.PutFile(rompath, path + '/' + romname)
            print("verifying rom copy is complete")
            conn.List(path)
            print("booting rom")
            conn.Boot(path + '/' + romname)
            conn.close()

            sleep(5)
            break
        except KeyboardInterrupt:
            break
        except:
            print("Unexpected error:", sys.exc_info()[0])
            conn.close()
            sleep(6)
            continue


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
    dst_idx = input('What destination (enter to chose 0)? ')
    print(dst_idx)
    if dst_idx == '':
        dst_idx = 0
    path = config['rules'][rule]['destinations'][int(dst_idx)]['path']
    try:
        name = config['rules'][rule]['destinations'][int(dst_idx)]['romname']
    except KeyError:
        name = romname
    return path, name

def get_comm_device(devicelist):
    print('----------------------------')
    for idx, device in enumerate(devicelist):
        print(str(idx) + ' - ' + device)
    dst_idx = int(input('What device? '))
    return devicelist[dst_idx]

main()
