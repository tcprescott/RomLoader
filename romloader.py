import fnmatch
import os
import sys
from time import sleep

import yaml
import py2snes
import psutil

import asyncio
import socket


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
            config = yaml.safe_load(configfile)
            print("loading config file at " +
                  os.path.abspath(scriptpath + "\\romloader.yaml"))
        except yaml.YAMLError as e:
            print(e)
            sys.exit(1)
except FileNotFoundError:
    try:
        with open("romloader.yaml") as configfile:
            try:
                config = yaml.safe_load(configfile)
                print("loading config file at " +
                      os.path.abspath("romloader.yaml"))
            except yaml.YAMLError as e:
                print(e)
                sys.exit(1)
    except FileNotFoundError:
        config = {"default_destination": '/romloader'}


async def main():
    try:
        rompath = sys.argv[1]
    except IndexError:
        raise Exception('We need a path to the ROM file to load.')
        sys.exit(1)
    filename = os.path.basename(rompath)
    
    title = None

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
            path, romname, title = get_destination(rule, filename)
    else:
        try:
            path = config['default_destination']
        except KeyError:
            path = '/romloader'
        romname = filename

    if not title:
        if "default_title" in config:
            title = config['default_title']
        else:
            title = 'Not an MSU pack'

    if "title_output_file" in config:
        title_output_file = os.path.abspath(scriptpath + config['title_output_file'])
        with open(title_output_file, 'w') as file:
            file.write(title)
            print('Pack selection written to ' + title_output_file)

    # initiate connection to the websocket server
    snes = py2snes.snes()

    a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    if is_open(64213):
        address = 'ws://localhost:64213'
    elif is_open(23074):
        address = 'ws://localhost:23074'
    elif is_open(8080):
        address = 'ws://localhost:8080'
    else:
        raise Exception(
            'Unable to connect to a suitable port!  Please ensure qusb2nes is listening on 64213, 23074, or 8080!')

    await snes.connect(address=address)

    devicelist = await snes.DeviceList()

    # Attach to usb2snes, use the device configured if it is set, otherwise
    # have it find the first device.
    if "device" in config:
        print('Attaching to specified device {device}'.format(
            device=config['device']
        ))
        await snes.Attach(config['device'])
    elif len(devicelist) > 1:
        await snes.Attach(get_comm_device(devicelist))
    else:
        print('Attaching to first device found.')
        await snes.Attach(devicelist[0])
    print('Attached to device \"{com}\"'.format(
        com=snes.device
    ))

    await snes.Name('RomLoader')
    if not rule:
        await snes.MakeDir('/romloader')
    await snes.List(path)
    print("copying rom to {fullpath}".format(
        fullpath=path + '/' + romname
    ))
    await snes.PutFile(rompath, path + '/' + romname)
    print("booting rom")
    await snes.Boot(path + '/' + romname)

    await asyncio.sleep(5)


def matchrule(name):
    if "rules" in config:
        for rule in config['rules']:
            for pattern in config['rules'][rule]['name_pattern']:
                if fnmatch.fnmatch(name, pattern):
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
        title = config['rules'][rule]['destinations'][int(dst_idx)]['name']
    except KeyError:
        name = romname
        title = None
    return path, name, title


def get_comm_device(devicelist):
    print('----------------------------')
    for idx, device in enumerate(devicelist):
        print(str(idx) + ' - ' + device)
    dst_idx = int(input('What device? '))
    return devicelist[dst_idx]


def is_open(port: int):
    return port in [i.laddr.port for i in psutil.net_connections()]


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
