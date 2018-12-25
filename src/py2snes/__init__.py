__version__ = '0.2.0'

import websocket
import json
from pathlib import Path

class usb2snesException(Exception):
    pass

class usb2snes():
    def __init__(self):
        self.conn = websocket.create_connection("ws://localhost:8080")
        self.attached = False
        
    def close(self):
        self.conn.close()

    def DeviceList(self):
        cmd = {
            'Opcode': 'DeviceList',
            'Space': 'SNES',
            'Flags': None,
            'Operands': None
        }
        self.conn.send(json.dumps(cmd))
        result = self.conn.recv()
        return json.loads(result)['Results']

    def Attach(self, com=None):
        if self.attached:
            raise usb2snesException("Already attached to \"{com}\".".format(
                com=self.attached
            ))
        devicelist = self.DeviceList()
        if com==None:
            com=devicelist[0]
        if com in devicelist:
            cmd = {
                'Opcode': 'Attach',
                'Space': 'SNES',
                'Flags': None,
                'Operands': [com]
            }
            self.conn.send(json.dumps(cmd))
            self.attached = com
            return com
        else:
            self.attached = False
            raise usb2snesException("Unable to find sd2snes device {com}.  Make sure your sd2snes is powered on and usb2snes firmware installed.".format(
                com=com
            ))

    def Name(self, name):
        if not self.attached:
            raise usb2snesException("Not attached to usb2snes.  Try executing Attach first.")
        cmd = {
            'Opcode': 'Name',
            'Space': 'SNES',
            'Flags': None,
            'Operands': [name]
        }
        self.conn.send(json.dumps(cmd))

    def Info(self):
        if not self.attached:
            raise usb2snesException("Not attached to usb2snes.  Try executing Attach first.")
        cmd = {
            'Opcode': 'Info',
            'Space': 'SNES',
            'Flags': None,
            'Operands': None
        }
        self.conn.send(json.dumps(cmd))
        result = self.conn.recv()
        resultlist = json.loads(result)['Results']
        resultdict = {
            "firmwareversion": self._listitem(resultlist,0),
            "versionstring": self._listitem(resultlist,1),
            "romrunning": self._listitem(resultlist,2),
            "flag1": self._listitem(resultlist,3),
            "flag2": self._listitem(resultlist,4),
        }
        return resultdict

    def Boot(self, romname):
        if not self.attached:
            raise usb2snesException("Not attached to usb2snes.  Try executing Attach first.")
        cmd = {
            'Opcode': 'Boot',
            'Space': 'SNES',
            'Flags': None,
            'Operands': [romname]
        }
        self.conn.send(json.dumps(cmd))

    def Menu(self):
        if not self.attached:
            raise usb2snesException("Not attached to usb2snes.  Try executing Attach first.")
        cmd = {
            'Opcode': 'Menu',
            'Space': 'SNES',
            'Flags': None,
            'Operands': None
        }
        self.conn.send(json.dumps(cmd))

    def Reset(self):
        if not self.attached:
            raise usb2snesException("Not attached to usb2snes.  Try executing Attach first.")
        cmd = {
            'Opcode': 'Reset',
            'Space': 'SNES',
            'Flags': None,
            'Operands': None
        }
        self.conn.send(json.dumps(cmd))

    def GetAddress(self,offset,size):
        '''untested'''
        if not self.attached:
            raise usb2snesException("Not attached to usb2snes.  Try executing Attach first.")
        cmd = {
            'Opcode': 'GetAddress',
            'Space': 'SNES',
            'Flags': None,
            'Operands': [offset,size]
        }
        self.conn.send(json.dumps(cmd))
        result = self.conn.recv()
        return json.loads(result)['Results']

    def PutAddress(self,offset,data):
        '''untested'''
        if not self.attached:
            raise usb2snesException("Not attached to usb2snes.  Try executing Attach first.")
        data_array = list(data)
        size = '{0:x}'.format(int(len(data_array)))
        cmd = {
            'Opcode': 'PutAddress',
            'Space': 'SNES',
            'Flags': None,
            'Operands': [offset,size]
        }
        self.conn.send(json.dumps(cmd))
        self.conn.send(data_array, websocket.ABNF.OPCODE_BINARY)

    def PutFile(self,srcpath,dstpath):
        if not self.attached:
            raise usb2snesException("Not attached to usb2snes.  Try executing Attach first.")

        fh = open(srcpath,"rb")
        file = fh.read()
        filearray = list(file)
        #size operand needs to be base16 (hex) integer
        size = '{0:x}'.format(int(len(filearray)))
        cmd = {
            'Opcode': 'PutFile',
            'Space': 'SNES',
            'Flags': None,
            'Operands': [dstpath, size]
        }
        self.conn.send(json.dumps(cmd))
        for chunk in self._chunk(filearray,4096):
            self.conn.send(chunk, websocket.ABNF.OPCODE_BINARY)
        fh.close()

    # def GetFile(self,filepath):
    #     """Not yet fully implemented"""
    #     if self.attached:
    #         cmd = {
    #             'Opcode': 'GetFile',
    #             'Space': 'SNES',
    #             'Flags': None,
    #             'Operands': [filepath]
    #         }
    #         self.conn.send(json.dumps(cmd))
    #         result = self.conn.recv()
    #         binAnswer = self.conn.recv_data()
    #         fh = open('rom/testget.sfc','wb')
    #         fh.write(binAnswer[1])
    #         fh.close()
    #         return json.loads(result)['Results']
    #     else:
    #         raise usb2snesException("GetFile: not attached to usb2snes.  Try executing Attach first.")

    def List(self,dirpath):
        if not self.attached:
            raise usb2snesException("Not attached to usb2snes.  Try executing Attach first.")
        elif not dirpath.startswith('/') and not dirpath in ['','/']:
            raise usb2snesException("Path \"{path}\" should start with \"/\"".format(
                path=dirpath
            ))
        elif dirpath.endswith('/') and not dirpath in ['','/']:
            raise usb2snesException("Path \"{path}\" should not end with \"/\"".format(
                path=dirpath
            ))

        if not dirpath in ['','/']:
            path = dirpath.lower().split('/')
            for idx, node in enumerate(path):
                if node == '':
                    continue
                else:
                    parent = '/'.join(path[:idx])
                    parentlist = self._list(parent)
                    
                    if any(d['filename'].lower() == node for d in parentlist):
                        continue
                    else:
                        raise FileNotFoundError("directory {path} does not exist on usb2snes.".format(
                            path=dirpath
                        ))
            return self._list(dirpath)
        else:
            return self._list(dirpath)

    def MakeDir(self,dirpath):
        if not self.attached:
            raise usb2snesException("Not attached to usb2snes.  Try executing Attach first.")
        if dirpath in ['','/']:
            raise usb2snesException('MakeDir: dirpath cannot be blank or \"/\"')

        path = dirpath.split('/')
        parent = '/'.join(path[:-1])
        parentdir = self.List(parent)
        try:
            self.List(dirpath)
        except FileNotFoundError as e:
            self._makedir(dirpath)

    # def Remove(self,filepath):
    #     if self.attached:
    #         if not filepath in ['','/']:
    #             # self._makedir(dirpath)
    #             path = filepath.split('/')
    #             parent = '/'.join(path[:-1])
    #             parentdir = self.List(parent)
    #             if parentdir:
    #                 # print(self.List(dirpath))
    #                 if not self.List(filepath):
    #                     self._makedir(filepath)
    #                 return True
    #             else:
    #                 raise usb2snesException('MakeDir: cannot create {filepath} because parent directory {parent} does not exist.'.format(
    #                     dirpath=filepath,
    #                     parent=parent
    #                 ))
    #         else:
    #             raise usb2snesException('Remove: filepath cannot be blank or /')
    #     else:
    #         raise usb2snesException("Remove: not attached to usb2snes.  Try executing Attach first.")



    def _list(self, dirpath):
        cmd = {
            'Opcode': 'List',
            'Space': 'SNES',
            'Flags': None,
            'Operands': [dirpath]
        }
        self.conn.send(json.dumps(cmd))
        result = self.conn.recv()
        it = iter(json.loads(result)['Results'])
        resultlist = []
        for item in it:
            filetype = item
            filename = next(it)
            resultdict = {
                "type": filetype,
                "filename": filename
            }
            if not filename in ['.','..']:
                resultlist.append(resultdict)
        return resultlist
        

    def _makedir(self, dirpath):
        cmd = {
            'Opcode': 'MakeDir',
            'Space': 'SNES',
            'Flags': None,
            'Operands': [dirpath]
        }
        self.conn.send(json.dumps(cmd))

    def _remove(self, filepath):
        cmd = {
            'Opcode': 'Remove',
            'Space': 'SNES',
            'Flags': None,
            'Operands': [filepath]
        }
        self.conn.send(json.dumps(cmd))

    def _fileexists(self, filepath):
        pass

    def _chunk(self, iterator, count):
        itr = iter(iterator)
        while True:
            yield tuple([next(itr) for i in range(count)])

    def _listitem(self, list, index):
        try:
            return list[index]
        except IndexError:
            return None