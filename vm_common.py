import guestfs
import logging

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

