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
            self.attached = True
            return com
        else:
            self.attached = False
            raise usb2snesException("Unable to find sd2snes device {com}.  Make sure your sd2snes is powered on and usb2snes firmware installed.".format(
                com=com
            ))

    def Name(self, name):
        if self.attached:
            cmd = {
                'Opcode': 'Name',
                'Space': 'SNES',
                'Flags': None,
                'Operands': [name]
            }
            self.conn.send(json.dumps(cmd))
        else:
            raise usb2snesException("Name: not attached to usb2snes.  Try executing Attach first.")

    def Info(self):
        if self.attached:
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
        else:
            raise usb2snesException("Info: not attached to usb2snes.  Try executing Attach first.")

    def Boot(self, romname):
        if self.attached:
            cmd = {
                'Opcode': 'Boot',
                'Space': 'SNES',
                'Flags': None,
                'Operands': [romname]
            }
            self.conn.send(json.dumps(cmd))
        else:
            raise usb2snesException("Boot: not attached to usb2snes.  Try executing Attach first.")

    def Menu(self, romname):
        if self.attached:
            cmd = {
                'Opcode': 'Menu',
                'Space': 'SNES',
                'Flags': None,
                'Operands': None
            }
            self.conn.send(json.dumps(cmd))
        else:
            raise usb2snesException("Menu: not attached to usb2snes.  Try executing Attach first.")

    def Reset(self):
        if self.attached:
            cmd = {
                'Opcode': 'Reset',
                'Space': 'SNES',
                'Flags': None,
                'Operands': None
            }
            self.conn.send(json.dumps(cmd))
        else:
            raise usb2snesException("Reset: not attached to usb2snes.  Try executing Attach first.")

    def GetAddress(self,offset,size):
        '''untested'''
        if self.attached:
            cmd = {
                'Opcode': 'GetAddress',
                'Space': 'SNES',
                'Flags': None,
                'Operands': [offset,size]
            }
            self.conn.send(json.dumps(cmd))
            result = self.conn.recv()
            return json.loads(result)['Results']
        else:
            raise usb2snesException("GetAddress: not attached to usb2snes.  Try executing Attach first.")

    def PutAddress(self,offset,data):
        '''untested'''
        if self.attached:
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
        else:
            raise usb2snesException("PutAddress: not attached to usb2snes.  Try executing Attach first.")

    def PutFile(self,srcpath,dstpath):
        if self.attached:
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
            for chunk in self._chunk(filearray,1024):
                self.conn.send(chunk, websocket.ABNF.OPCODE_BINARY)
            fh.close()
        else:
            raise usb2snesException("PutFile: not attached to usb2snes.  Try executing Attach first.")

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
        if self.attached:
            if not dirpath in ['','/']:
                path = dirpath.split('/')
                for idx, node in enumerate(path):
                    if node == '':
                        continue
                    else:
                        parent = '/'.join(path[:idx])
                        parentlist = self._list(parent)
                        
                        if any(d['filename'] == node for d in parentlist):
                            continue
                        else:
                            return False
                            break
                return self._list(dirpath)
            else:
                return self._list(dirpath)
        else:
            raise usb2snesException("List: not attached to usb2snes.  Try executing Attach first.")

    def MakeDir(self,dirpath):
        if self.attached:
            if not dirpath in ['','/']:
                # self._makedir(dirpath)
                path = dirpath.split('/')
                parent = '/'.join(path[:-1])
                parentdir = self.List(parent)
                if parentdir:
                    if not self.List(dirpath):
                        self._makedir(dirpath)
                    return True
                else:
                    raise usb2snesException('MakeDir: cannot create {dirpath} because parent directory {parent} does not exist.'.format(
                        dirpath=dirpath,
                        parent=parent
                    ))
            else:
                raise usb2snesException('MakeDir: dirpath cannot be blank or /')
        else:
            raise usb2snesException("MakeDir: not attached to usb2snes.  Try executing Attach first.")

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
            resultdict = {
                "type": item,
                "filename": next(it)
            }
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