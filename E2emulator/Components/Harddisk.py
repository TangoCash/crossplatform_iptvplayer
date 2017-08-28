from myGetText import _
import os
if os.name =='nt':
    isWindows = True
else:
    isWindows = False
    
import time

from os import system, listdir, popen, makedirs, stat, path, access
# not in Android?
try: from os import statvfs
except: pass
# not in Windows?
try: from os import major, minor
except: pass

from Tools.Directories import SCOPE_HDD, resolveFilename, pathExists
from Tools.CList import CList
from SystemInfo import SystemInfo
import Task

def readFile(filename):
    file = open(filename)
    data = file.read().strip()
    file.close()
    return data


def getProcMounts():
    if isWindows == True:
        print '[Harddisk:getProcMounts] return [] for Windows'
        return []
    try:
        mounts = open('/proc/mounts')
    except IOError as ex:
        print '[Harddisk] Failed to open /proc/mounts', ex
        return []

    return [ line.strip().split(' ') for line in mounts ]


def createMovieFolder():
    movie = resolveFilename(SCOPE_HDD)
    if not pathExists(movie):
        makedirs(movie)


def isFileSystemSupported(filesystem):
    if isWindows == True:
        print '[Harddisk:isFileSystemSupported] return False for Windows'
        return False
    try:
        for fs in open('/proc/filesystems', 'r'):
            if fs.strip().endswith(filesystem):
                return True

        return False
    except Exception as ex:
        print '[Harddisk] Failed to read /proc/filesystems:', ex


def findMountPoint(path):
    """Example: findMountPoint("/media/hdd/some/file") returns "/media/hdd"""
    path = os.path.abspath(path)
    while not os.path.ismount(path):
        path = os.path.dirname(path)

    return path


DEVTYPE_UDEV = 0
DEVTYPE_DEVFS = 1

class Harddisk():

    def __init__(self, device, removable):
        self.device = device
        self.type = DEVTYPE_UDEV
        self.max_idle_time = 0
        self.idle_running = False
        self.last_access = time.time()
        self.last_stat = 0
        self.timer = None
        self.is_sleeping = False
        self.dev_path = ''
        self.disk_path = ''
        self.mount_path = None
        self.mount_device = None
        self.phys_path = path.realpath(self.sysfsPath('device'))
        if self.type == DEVTYPE_UDEV:
            self.dev_path = '/dev/' + self.device
            self.disk_path = self.dev_path
        elif self.type == DEVTYPE_DEVFS:
            tmp = readFile(self.sysfsPath('dev')).split(':')
            s_major = int(tmp[0])
            s_minor = int(tmp[1])
            for disc in listdir(os.path.join('dev','discs')):
                dev_path = path.realpath(os.path.join('dev','discs',disc))
                disk_path = dev_path + '/disc'
                try:
                    rdev = stat(disk_path).st_rdev
                except OSError:
                    continue

                if s_major == major(rdev) and s_minor == minor(rdev):
                    self.dev_path = dev_path
                    self.disk_path = disk_path
                    break

        print 'new Harddisk', self.device, '->', self.dev_path, '->', self.disk_path
        if not removable:
            self.startIdle()
        return

    def __lt__(self, ob):
        return self.device < ob.device

    def partitionPath(self, n):
        if self.type == DEVTYPE_UDEV:
            return self.dev_path + n
        if self.type == DEVTYPE_DEVFS:
            return self.dev_path + '/part' + n

    def sysfsPath(self, filename):
        return path.realpath('/sys/block/' + self.device + '/' + filename)

    def stop(self):
        if self.timer:
            self.timer.stop()
            self.timer.callback.remove(self.runIdle)

    def bus(self):
        if self.type == DEVTYPE_UDEV:
            ide_cf = False
        elif self.type == DEVTYPE_DEVFS:
            ide_cf = self.device[:2] == 'hd' and 'host0' not in self.dev_path
        internal = 'pci' in self.phys_path
        if ide_cf:
            ret = 'External (CF)'
        elif internal:
            ret = 'Internal'
        else:
            ret = 'External'
        return ret

    def diskSize(self):
        line = readFile(self.sysfsPath('size'))
        try:
            cap = int(line)
        except:
            return 0

        return cap / 1000 * 512 / 1000

    def capacity(self):
        cap = self.diskSize()
        if cap == 0:
            return ''
        if cap < 1000:
            return '%03d MB' % cap
        return '%d.%03d GB' % (cap / 1000, cap % 1000)

    def model(self):
        if isWindows == True:
            print '[Harddisk:model] return NA for Windows'
            return 'NA'
        try:
            if self.device[:2] == 'hd':
                return readFile('/proc/ide/' + self.device + '/model')
            if self.device[:2] == 'sd':
                vendor = readFile(self.sysfsPath('device/vendor'))
                model = readFile(self.sysfsPath('device/model'))
                return vendor + '(' + model + ')'
            raise Exception, 'no hdX or sdX'
        except Exception as e:
            print '[Harddisk] Failed to get model:', e
            return '-?-'

    def free(self):
        dev = self.findMount()
        if dev:
            stat = statvfs(dev)
            return stat.f_bfree / 1000 * (stat.f_bsize / 1000)
        return -1

    def numPartitions(self):
        numPart = -1
        if self.type == DEVTYPE_UDEV:
            try:
                devdir = listdir('/dev')
            except OSError:
                return -1

            for filename in devdir:
                if filename.startswith(self.device):
                    numPart += 1

        elif self.type == DEVTYPE_DEVFS:
            try:
                idedir = listdir(self.dev_path)
            except OSError:
                return -1

            for filename in idedir:
                if filename.startswith('disc'):
                    numPart += 1
                if filename.startswith('part'):
                    numPart += 1

        return numPart

    def mountDevice(self):
        for parts in getProcMounts():
            if path.realpath(parts[0]).startswith(self.dev_path):
                self.mount_device = parts[0]
                self.mount_path = parts[1]
                return parts[1]

    def findMount(self):
        if self.mount_path is None:
            return self.mountDevice()
        else:
            return self.mount_path

    def unmount(self):
        dev = self.mountDevice()
        if dev is None:
            return 0
        else:
            cmd = 'umount ' + dev
            print '[Harddisk]', cmd
            res = system(cmd)
            return res >> 8

    def createPartition(self):
        size = self.diskSize()
        if size > 128000:
            print '[HD] Detected >128GB disk, using 4k alignment'
            cmd = 'printf "8,\n;0,0\n;0,0\n;0,0\ny\n" | sfdisk -f -uS ' + self.disk_path
        else:
            cmd = 'printf "0,\n;\n;\n;\ny\n" | sfdisk -f -uS ' + self.disk_path
        res = system(cmd)
        return res >> 8

    def mkfs(self):
        size = self.diskSize()
        cmd = 'mkfs.ext4 -L records'
        if size > 250000:
            cmd += ' -T largefile -O sparse_super -N 262144'
        elif size > 16384:
            cmd += ' -T largefile -O sparse_super'
        elif size > 2048:
            cmd += ' -T largefile -N ' + str(size * 32)
        cmd += ' -m0 -O dir_index ' + self.partitionPath('1')
        print '[Harddisk] ', cmd
        res = system(cmd)
        return res >> 8

    def mount(self):
        cmd = 'mount ' + self.partitionPath('1') + ' /hdd'
        print '[Harddisk] ', cmd
        res = system(cmd)
        return res >> 8

    def mount_(self):
        if self.mount_device is None:
            dev = self.partitionPath('1')
        else:
            dev = self.mount_device
        try:
            fstab = open('/etc/fstab')
            lines = fstab.readlines()
        except IOError:
            return -1

        fstab.close()
        for line in lines:
            parts = line.strip().split(' ')
            fspath = path.realpath(parts[0])
            if path.realpath(fspath) == dev:
                print '[Harddisk] mounting:', fspath
                cmd = 'mount -t ext3 ' + fspath
                res = system(cmd)
                return res >> 8

        res = -1
        if self.type == DEVTYPE_UDEV:
            res = system('sfdisk -R ' + self.disk_path)
            from time import sleep
            sleep(3)
        return res >> 8

    def createMovieFolder(self):
        if not pathExists(resolveFilename(SCOPE_HDD)):
            try:
                makedirs(resolveFilename(SCOPE_HDD))
            except OSError:
                return -1

        return 0

    def fsck(self):
        self.unmount()
        cmd = 'fsck.ext4 -f -p ' + self.partitionPath('1')
        print '[Harddisk] ', cmd
        res = system(cmd)
        self.mount()
        return res >> 8

    def killPartitionTable(self):
        zero = 512 * '\x00'
        h = open(self.dev_path, 'wb')
        for i in range(9):
            h.write(zero)

        h.close()

    def killPartition(self, n):
        zero = 512 * '\x00'
        part = self.partitionPath(n)
        h = open(part, 'wb')
        for i in range(3):
            h.write(zero)

        h.close()

    def rereadpartitiontable(self):
        cmd = 'sfdisk -R ' + self.disk_path
        res = system(cmd)

    def createInitializeJob(self):
        job = Task.Job(_('Initializing storage device...'))
        task = UnmountTask(job, self)
        task = Task.PythonTask(job, _('Kill partition table'))
        task.work = self.killPartitionTable
        task.weighting = 1
        task = Task.LoggingTask(job, _('Reread partition table'))
        task.weighting = 1
        task.setTool('sfdisk')
        task.args.append('-R')
        task.args.append(self.disk_path)
        task = Task.LoggingTask(job, _('Wait for partition'))
        task.setTool('sleep')
        task.args.append('1')
        task.weighting = 1
        size = self.diskSize()
        print '[HD] size: %s MB' % size
        task = Task.LoggingTask(job, _('Create Partition'))
        task.weighting = 5
        task.setTool('sfdisk')
        task.args.append('-f')
        task.args.append('-uS')
        task.args.append(self.disk_path)
        if size > 128000:
            print '[HD] Detected >128GB disk, using 4k alignment'
            task.initial_input = '8,\n;0,0\n;0,0\n;0,0\ny\n'
        else:
            task.initial_input = '0,\n;\n;\n;\ny\n'
        task = Task.LoggingTask(job, _('Wait for partition'))
        task.setTool('sleep')
        task.args.append('1')
        task.weighting = 1
        task = MkfsTask(job, _('Create Filesystem'))
        if isFileSystemSupported('ext4'):
            task.setTool('mkfs.ext4')
        else:
            task.setTool('mkfs.ext3')
        if size > 250000:
            task.args += ['-T',
             'largefile',
             '-O',
             'sparse_super',
             '-N',
             '262144']
        elif size > 16384:
            task.args += ['-T',
             'largefile',
             '-O',
             'sparse_super']
        elif size > 2048:
            task.args += ['-T',
             'largefile',
             '-N',
             str(size * 32)]
        task.args += ['-L',
         'records',
         '-m0',
         '-O',
         'dir_index',
         self.partitionPath('1')]
        task = Task.LoggingTask(job, _('Wait for partition'))
        task.setTool('sleep')
        task.args.append('1')
        task.weighting = 1
        task = Task.LoggingTask(job, _('Mount partition'))
        task.setTool('mount')
        task.args.append(self.partitionPath('1'))
        task.args.append('/hdd')
        task.weighting = 1
        task = Task.LoggingTask(job, _('Wait for partition'))
        task.setTool('sleep')
        task.args.append('1')
        task.weighting = 1
        task = Task.PythonTask(job, _('Create movie directory'))
        task.weighting = 1
        task.work = createMovieFolder
        return job

    errorList = [_('Everything is fine'),
     _('Creating partition failed'),
     _('Mkfs failed'),
     _('Mount failed'),
     _('Create movie folder failed'),
     _('Fsck failed'),
     _('Please Reboot'),
     _('Filesystem contains uncorrectable errors'),
     _('Unmount failed')]

    def initialize(self):
        self.unmount()
        self.killPartitionTable()
        self.rereadpartitiontable()
        time.sleep(2)
        if self.createPartition() != 0:
            return -1
        if self.mkfs() != 0:
            return -2
        if self.mount() != 0:
            return -3
        if self.createMovieFolder() != 0:
            return -4
        return 0

    def check(self):
        if self.fsck() != 0:
            return -5
        return 0

    def createCheckJob(self):
        job = Task.Job(_('Checking Filesystem...'))
        if self.findMount():
            UnmountTask(job, self)
            dev = self.mount_device
        else:
            dev = self.partitionPath('1')
        task = Task.LoggingTask(job, 'fsck')
        task.setTool('fsck.ext3')
        task.args.append('-f')
        task.args.append('-p')
        task.args.append(dev)
        MountTask(job, self)
        task = Task.ConditionTask(job, _('Wait for mount'))
        task.check = self.mountDevice
        return job

    def createExt4ConversionJob(self):
        if not isFileSystemSupported('ext4'):
            raise Exception, _('You system does not support ext4')
        job = Task.Job(_('Convert ext3 to ext4...'))
        if not path.exists('/sbin/tune2fs'):
            task = Task.LoggingTask(job, 'update packages')
            task.setTool('opkg')
            task.args.append('update')
            task = Task.LoggingTask(job, 'Install e2fsprogs-tune2fs')
            task.setTool('opkg')
            task.args.append('install')
            task.args.append('e2fsprogs-tune2fs')
        if self.findMount():
            UnmountTask(job, self)
            dev = self.mount_device
        else:
            dev = self.partitionPath('1')
        task = Task.LoggingTask(job, 'fsck')
        task.setTool('fsck.ext3')
        task.args.append('-p')
        task.args.append(dev)
        task = Task.LoggingTask(job, 'tune2fs')
        task.setTool('tune2fs')
        task.args.append('-O')
        task.args.append('extents,uninit_bg,dir_index')
        task.args.append('-o')
        task.args.append('journal_data_writeback')
        task.args.append(dev)
        task = Task.LoggingTask(job, 'fsck')
        task.setTool('fsck.ext4')
        task.postconditions = []
        task.args.append('-f')
        task.args.append('-p')
        task.args.append('-D')
        task.args.append(dev)
        MountTask(job, self)
        task = Task.ConditionTask(job, _('Wait for mount'))
        task.check = self.mountDevice
        return job

    def getDeviceDir(self):
        return self.dev_path

    def getDeviceName(self):
        return self.disk_path

    def readStats(self):
        try:
            l = open('/sys/block/%s/stat' % self.device).read()
        except IOError:
            return (-1, -1)

        data = l.split(None, 5)
        return (int(data[0]), int(data[4]))

    def startIdle(self):
        pass

    def runIdle(self):
        if not self.max_idle_time:
            return
        t = time.time()
        idle_time = t - self.last_access
        stats = self.readStats()
        l = sum(stats)
        if l != self.last_stat and l >= 0:
            self.last_stat = l
            self.last_access = t
            idle_time = 0
            self.is_sleeping = False
        if idle_time >= self.max_idle_time and not self.is_sleeping:
            self.setSleep()
            self.is_sleeping = True

    def setSleep(self):
        pass

    def setIdleTime(self, idle):
        self.max_idle_time = idle
        if self.idle_running:
            if not idle:
                self.timer.stop()
            else:
                self.timer.start(idle * 100, False)

    def isSleeping(self):
        return self.is_sleeping


class Partition():

    def __init__(self, mountpoint, device = None, description = '', force_mounted = False):
        self.mountpoint = mountpoint
        self.description = description
        self.force_mounted = mountpoint and force_mounted
        self.is_hotplug = force_mounted
        self.device = device

    def __str__(self):
        return 'Partition(mountpoint=%s,description=%s,device=%s)' % (self.mountpoint, self.description, self.device)

    def stat(self):
        if self.mountpoint:
            return statvfs(self.mountpoint)
        raise OSError, 'Device %s is not mounted' % self.device

    def free(self):
        try:
            s = self.stat()
            return s.f_bavail * s.f_bsize
        except OSError:
            return None

        return None

    def total(self):
        try:
            s = self.stat()
            return s.f_blocks * s.f_bsize
        except OSError:
            return None

        return None

    def tabbedDescription(self):
        if self.mountpoint.startswith('/media/net'):
            return self.description
        return self.description + '\t' + self.mountpoint

    def mounted(self, mounts = None):
        if self.force_mounted:
            return True
        else:
            if self.mountpoint:
                if mounts is None:
                    mounts = getProcMounts()
                for parts in mounts:
                    if parts[1] == self.mountpoint:
                        return True

            return False

    def filesystem(self, mounts = None):
        if self.mountpoint:
            if mounts is None:
                mounts = getProcMounts()
            for fields in mounts:
                if fields[1] == self.mountpoint:
                    return fields[2]

        return ''


DEVICEDB = {'dm8000': {'/devices/platform/brcm-ehci.0/usb1/1-1/1-1.1/1-1.1:1.0': 'Front USB Slot',
            '/devices/platform/brcm-ehci.0/usb1/1-1/1-1.2/1-1.2:1.0': 'Back, upper USB Slot',
            '/devices/platform/brcm-ehci.0/usb1/1-1/1-1.3/1-1.3:1.0': 'Back, lower USB Slot',
            '/devices/platform/brcm-ehci-1.1/usb2/2-1/2-1:1.0/host1/target1:0:0/1:0:0:0': 'DVD Drive'},
 'dm800': {'/devices/platform/brcm-ehci.0/usb1/1-2/1-2:1.0': 'Upper USB Slot',
           '/devices/platform/brcm-ehci.0/usb1/1-1/1-1:1.0': 'Lower USB Slot'},
 'dm7025': {'/devices/pci0000:00/0000:00:14.1/ide1/1.0': 'CF Card Slot',
            '/devices/pci0000:00/0000:00:14.1/ide0/0.0': 'Internal Harddisk'},
 'nbox': {'/devices/platform/stm-usb.0/stm-ehci.0/usb1/1-1/1-1.1/1-1.1:1.0/host1/target1:0:0/1:0:0:0': 'USB Slot'}}

class HarddiskManager():

    def __init__(self):
        self.hdd = []
        self.cd = ''
        self.partitions = []
        self.devices_scanned_on_init = []
        self.on_partition_list_change = CList()
        self.enumerateBlockDevices()
        p = (('/media/hdd', _('Harddisk')),
         ('/media/card', _('Card')),
         ('/media/cf', _('Compact Flash')),
         ('/media/mmc1', _('MMC Card')),
         ('/media/net', _('Network Mount')),
         ('/media/net1', _('Network Mount') + ' 1'),
         ('/media/net2', _('Network Mount') + ' 2'),
         ('/media/net3', _('Network Mount') + ' 3'),
         ('/media/ram', _('Ram Disk')),
         ('/media/usb', _('USB Stick')),
         ('/', _('Internal Flash')))
        known = set([ path.normpath(a.mountpoint) for a in self.partitions if a.mountpoint ])
        for m, d in p:
            if m not in known and path.ismount(m):
                self.partitions.append(Partition(mountpoint=m, description=d))

    def getBlockDevInfo(self, blockdev):
        devpath = '/sys/block/' + blockdev
        error = False
        removable = False
        blacklisted = False
        is_cdrom = False
        partitions = []
        try:
            removable = bool(int(readFile(devpath + '/removable')))
            dev = int(readFile(devpath + '/dev').split(':')[0])
            if dev in (7, 31, 253):
                blacklisted = True
            if blockdev[0:2] == 'sr':
                is_cdrom = True
            if blockdev[0:2] == 'hd':
                try:
                    media = readFile('/proc/ide/%s/media' % blockdev)
                    if 'cdrom' in media:
                        is_cdrom = True
                except IOError:
                    error = True

            if not is_cdrom:
                for partition in listdir(devpath):
                    if partition[0:len(blockdev)] != blockdev:
                        continue
                    partitions.append(partition)

            else:
                self.cd = blockdev
        except IOError:
            error = True

        medium_found = True
        try:
            open('/dev/' + blockdev).close()
        except IOError as err:
            if err.errno == 159:
                medium_found = False

        return (error,
         blacklisted,
         removable,
         is_cdrom,
         partitions,
         medium_found)

    def enumerateBlockDevices(self):
        if isWindows == True:
            print '[Harddisk:enumerateBlockDevices] no action for Windows'
            return
        print '[Harddisk] enumerating block devices...'
        try:
            for blockdev in listdir('/sys/block'):
                error, blacklisted, removable, is_cdrom, partitions, medium_found = self.addHotplugPartition(blockdev)
                if not error and not blacklisted and medium_found:
                    for part in partitions:
                        self.addHotplugPartition(part)

                    self.devices_scanned_on_init.append((blockdev,
                    removable,
                    is_cdrom,
                    medium_found))
        except:
            pass
        
        
	def addHotplugAudiocd(self, device, physdev = None):		# device is the device name, without /dev
		# physdev is the physical device path, which we (might) use to determine the userfriendly name
		if not physdev:
			dev, part = self.splitDeviceName(device)
			try:
				physdev = os.path.realpath('/sys/block/' + dev + '/device')[4:]
			except OSError:
				physdev = dev
				print "couldn't determine blockdev physdev for device", device
		error, blacklisted, removable, is_cdrom, partitions, medium_found = self.getBlockDevInfo(device)
		if not blacklisted and medium_found:
			description = self.getUserfriendlyDeviceName(device, physdev)
			p = Partition(mountpoint = "/media/audiocd", description = description, force_mounted = True, device = device)
			self.partitions.append(p)
			self.on_partition_list_change("add", p)
			SystemInfo["Harddisk"] = False
		return error, blacklisted, removable, is_cdrom, partitions, medium_found

    def getAutofsMountpoint(self, device):
        return os.path.join('autofs', device)

    def getMountpoint(self, device):
        dev = os.path.join('dev', device)
        for item in getProcMounts():
            if item[0] == dev:
                return item[1]

        mount = self.getAutofsMountpoint(device)
        if mount:
            return mount
        else:
            return None

    def addHotplugPartition(self, device, physdev = None):
        if not physdev:
            dev, part = self.splitDeviceName(device)
            try:
                physdev = path.realpath('/sys/block/' + dev + '/device')[4:]
            except OSError:
                physdev = dev
                print "couldn't determine blockdev physdev for device", device

        error, blacklisted, removable, is_cdrom, partitions, medium_found = self.getBlockDevInfo(device)
        if not blacklisted and medium_found:
            description = self.getUserfriendlyDeviceName(device, physdev)
            if description.startswith('External Storage'):
                return (False,
                 False,
                 False,
                 False,
                 [],
                 False)
            p = Partition(mountpoint=self.getMountpoint(device), description=description, force_mounted=True, device=device)
            self.partitions.append(p)
            if p.mountpoint:
                self.on_partition_list_change('add', p)
            l = len(device)
            if l and not device[l - 1].isdigit():
                self.hdd.append(Harddisk(device, removable))
                self.hdd.sort()
                SystemInfo['Harddisk'] = True
        return (error,
         blacklisted,
         removable,
         is_cdrom,
         partitions,
         medium_found)

    def removeHotplugPartition(self, device):
        for x in self.partitions[:]:
            if x.device == device:
                self.partitions.remove(x)
                if x.mountpoint:
                    self.on_partition_list_change('remove', x)

        l = len(device)
        if l and not device[l - 1].isdigit():
            for hdd in self.hdd:
                if hdd.device == device:
                    hdd.stop()
                    self.hdd.remove(hdd)
                    break

            SystemInfo['Harddisk'] = len(self.hdd) > 0

    def HDDCount(self):
        return len(self.hdd)

    def HDDList(self):
        list = []
        for hd in self.hdd:
            hdd = hd.model() + ' - ' + hd.bus()
            cap = hd.capacity()
            if cap != '':
                hdd += ' (' + cap + ')'
            list.append((hdd, hd))

        return list

    def getCD(self):
        return self.cd

    def getMountedPartitions(self, onlyhotplug = False, mounts = None):
        if mounts is None:
            mounts = getProcMounts()
        parts = [ x for x in self.partitions if (x.is_hotplug or not onlyhotplug) and x.mounted(mounts) ]
        devs = set([ x.device for x in parts ])
        for devname in devs.copy():
            if not devname:
                continue
            dev, part = self.splitDeviceName(devname)
            if part and dev in devs:
                devs.remove(dev)

        return [ x for x in parts if not x.device or x.device in devs ]

    def splitDeviceName(self, devname):
        dev = devname[:3]
        part = devname[3:]
        for p in part:
            if not p.isdigit():
                return (devname, 0)

        return (dev, part and int(part) or 0)

    def getUserfriendlyDeviceName(self, dev, phys):
        dev, part = self.splitDeviceName(dev)
        description = 'External Storage %s' % dev
        try:
            if os.path.exists('/sys' + phys + '/model'):
                description = readFile('/sys' + phys + '/model')
        except IOError as s:
            pass # j00zek: disable spamprint "couldn't read model: ", s

        from Tools.HardwareInfo import HardwareInfo
        for physdevprefix, pdescription in DEVICEDB.get(HardwareInfo().device_name, {}).items():
            if phys.startswith(physdevprefix):
                description = pdescription

        if part and part != 1:
            description += ' (Partition %d)' % part
        return description

    def addMountedPartition(self, device, desc):
        for x in self.partitions:
            if x.mountpoint == device:
                return

        self.partitions.append(Partition(mountpoint=device, description=desc))

    def removeMountedPartition(self, mountpoint):
        for x in self.partitions[:]:
            if x.mountpoint == mountpoint:
                self.partitions.remove(x)
                self.on_partition_list_change('remove', x)

    def setDVDSpeed(self, device, speed = 0):
        if isWindows == True:
            print '[Harddisk:setDVDSpeed] no action for Windows'
            return
        ioctl_flag = int(21282)
        if not device.startswith('/'):
            device = '/dev/' + device
        try:
            from fcntl import ioctl
            cd = open(device)
            ioctl(cd.fileno(), ioctl_flag, speed)
            cd.close()
        except Exception as ex:
            print '[Harddisk] Failed to set %s speed to %s' % (device, speed), ex


class UnmountTask(Task.LoggingTask):

    def __init__(self, job, hdd):
        Task.LoggingTask.__init__(self, job, _('Unmount'))
        self.hdd = hdd

    def prepare(self):
        try:
            dev = self.hdd.disk_path.split('/')[-1]
            open('/dev/nomount.%s' % dev, 'wb').close()
        except Exception as e:
            print 'ERROR: Failed to create /dev/nomount file:', e

        dev = self.hdd.mountDevice()
        if dev:
            self.setCmdline('umount -f ' + dev)
            self.postconditions.append(Task.ReturncodePostcondition())


class MountTask(Task.LoggingTask):

    def __init__(self, job, hdd):
        Task.LoggingTask.__init__(self, job, _('Mount'))
        self.hdd = hdd

    def prepare(self):
        try:
            dev = self.hdd.disk_path.split('/')[-1]
            os.unlink('/dev/nomount.%s' % dev)
        except Exception as e:
            print 'ERROR: Failed to remove /dev/nomount file:', e

        if self.hdd.mount_device is None:
            dev = self.hdd.partitionPath('1')
        else:
            dev = self.hdd.mount_device
        fstab = open('/etc/fstab')
        lines = fstab.readlines()
        fstab.close()
        for line in lines:
            parts = line.strip().split(' ')
            fspath = path.realpath(parts[0])
            if path.realpath(fspath) == dev:
                self.setCmdline('mount -t ext3 ' + fspath)
                self.postconditions.append(Task.ReturncodePostcondition())
                return

        if self.hdd.type == DEVTYPE_UDEV:
            self.setCmdline('sleep 2; sfdisk -R ' + self.hdd.disk_path)
            self.postconditions.append(Task.ReturncodePostcondition())
        return


class MkfsTask(Task.LoggingTask):

    def prepare(self):
        self.fsck_state = None
        return

    def processOutput(self, data):
        print '[Mkfs]', data
        if 'Writing inode tables:' in data:
            self.fsck_state = 'inode'
        elif 'Creating journal' in data:
            self.fsck_state = 'journal'
            self.setProgress(80)
        elif 'Writing superblocks ' in data:
            self.setProgress(95)
        elif self.fsck_state == 'inode':
            if '/' in data:
                try:
                    d = data.strip(' \x08\r\n').split('/', 1)
                    if '\x08' in d[1]:
                        d[1] = d[1].split('\x08', 1)[0]
                    self.setProgress(80 * int(d[0]) / int(d[1]))
                except Exception as e:
                    print '[Mkfs] E:', e

                return
        self.log.append(data)


harddiskmanager = HarddiskManager()

def internalHDDNotSleeping():
    if harddiskmanager.HDDCount():
	for hdd in harddiskmanager.HDDList():
	    if ("pci" in hdd[1].phys_path or "ahci" in hdd[1].phys_path) and hdd[1].max_idle_time and not hdd[1].isSleeping():
		return True
    return False

SystemInfo['ext4'] = isFileSystemSupported('ext4')
