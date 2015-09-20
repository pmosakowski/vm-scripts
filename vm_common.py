import guestfs
import logging
import io, csv
import re
from collections import namedtuple
from enum import IntEnum

class AugOption(IntEnum):
    AUG_SAVE_BACKUP = 1
    AUG_SAVE_NEWFILE = 2
    AUG_TYPE_CHECK = 4
    AUG_NO_STDINC = 8
    AUG_SAVE_NOOP = 16
    AUG_NO_LOAD = 32

class GuestFSDisk:
    def __init__(self, disk_path, log=None):
        if log:
            self.log = log
        else:
            self.log = logging.getLogger(__name__)
            self.log.addHandler(logging.StreamHandler())
            self.log.setLevel(logging.DEBUG)

        self.disk_path = disk_path

        self.gfs = guestfs.GuestFS(python_return_dict=True)
        self.gfs.add_drive(self.disk_path)
        self.gfs.set_selinux(1)
        self.gfs.launch()

        self.__inspect_fs()
        self.__mount_fs_tree(self.mountpoints)
        self.gfs.aug_init('/',AugOption.AUG_SAVE_BACKUP)
    
    # gather information about filesystem layout
    def __inspect_fs(self):
        os_list = self.gfs.inspect_os()
        assert(len(os_list) == 1)
        self.root_fs = os_list[0]
        self.log.info('[GUEST] found root filesystem on %s', self.root_fs)

        self.mountpoints = self.gfs.inspect_get_mountpoints(self.root_fs)
        for mount,part in self.mountpoints.items():
            self.log.debug('[GUEST] found partition %s : %s', mount, part)

    def __mount_fs_tree(self, mountpoints):
        for mountpoint in sorted(mountpoints.keys()):
            partition = mountpoints[mountpoint]
            self.gfs.mount(partition, mountpoint)
            self.log.info('[GUEST] mounting partition %s : %s', mountpoint, partition)

    @property
    def users(self):
        try:
            return self.__users
        except:
            User = namedtuple('User', ['uid','gid','home'])

            etc_passwd = self.gfs.cat('/etc/passwd')
            mem_file = io.StringIO(etc_passwd)
            passwdreader = csv.reader(mem_file, delimiter=':')

            self.__users = {}

            for row in passwdreader:
                username = row[0]
                uid = int(row[2])
                gid = int(row[3])
                home = row[5]
                if uid >= 1000:
                    self.__users[username] = User(uid=uid, gid=gid, home=home)

            return self.__users

    def get_executable_path(self, executable_name):
        try:
            return self.__executable_paths[executable_name]

        except AttributeError:
            self.__executable_paths = {}
            self.__executable_paths[executable_name] = self.__find_executable(executable_name)
            return self.__executable_paths[executable_name]

        except KeyError:
            self.__executable_paths[executable_name] = self.__find_executable(executable_name)
            return self.__executable_paths[executable_name]

    def __find_executable(self, executable_name):
        name_regex = re.compile(r'^.+/{}$'.format(executable_name))

        paths = ['/bin', '/usr/bin', '/sbin', '/usr/sbin']
        files = []

        for path in paths:
            # need to prepend the search path, it is skipped in the output
            files.extend([path + x for x in self.gfs.find(path)])
        for executable_path in files:
            if name_regex.match(executable_path):
                self.log.debug('[GUEST:%s] found %i executables', self.__class__.__name__, len(files))
                return executable_path
