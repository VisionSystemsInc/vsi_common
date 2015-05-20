#!/usr/bin/env python

# This script will set up a chroot and enter it for you. Will create certain
# neccessary directories, and use mount --bind to connect them to the chroot
# environement. THIS IS NOT a security chroot, this is for a fully functional
# chroot. /proc, /dev, /dev/shm (or equivalent), /dev/pts, and 
# /lib/modules/$(uname -r) are connected (mount --bind) to the chroot.
#
# Upon exiting the chroot, loose mount will be removed UNLESS it is determined
# That you left a program running, in which case the mounts will be left 
# connected until next time this script is run and exited
#
# In addition, the script will create/modify users and groups to match either
# 1) user and info spcified by the parameters --user, --uid, --gid, --group
# 2) Sudo user
# 3) Defaults
#
# --simple mode skips all the user stuff, and just drops you in as root
#
# Other common features like XAUTHORITY and resolv.conf are taken care of too.
#
# Requirments:
#  Host - python (at least 2.5)
#

from __future__ import with_statement #2.5 compatibility

from os import environ as env
from os.path import join as path_join
import os
#import argparse python 2.6 compatibility
from optparse import OptionParser #2.3
from subprocess import Popen, PIPE #2.4
from distutils.dir_util import mkpath, copy_tree #?
from distutils.file_util import copy_file #?
from distutils.errors import DistutilsFileError
from glob import glob #Pre 2.5
import re #pre 1.5.2

import logging
logger = logging.getLogger(__name__)

DEFAULT_USER='user'
DEFAULT_GROUP='workgroup'
DEFAULT_UID=1000
DEFAULT_GID=1000

def call(*cmd):
  logger.info('Running command: %s', cmd)
  pid = Popen(cmd, stdout=PIPE, stderr=PIPE)
  (dout, derr) = pid.communicate()
  logger.debug('stdout: %s', dout)
  logger.debug('stderr: %s', derr)
  return (dout, derr, pid.wait())

def uidFromName(name):
  try:
    uid = call('id', '-u', name)[0]
    return int(uid.strip())
  except ValueError:
    return int(env.get('SUDO_UID', DEFAULT_UID));

def gidFromName(name):
  try:
    gid = call('id', '-g', name)[0]
    return int(gid.strip())
  except ValueError:
    return int(env.get('SUDO_GID', DEFAULT_GID));

def groupFromName(name):
  try:
    group = call('id', '-gn', name)[0].strip()
    if len(group)==0:
      raise ValueError("Empty string");
    return group.strip()
  except ValueError:
    return DEFAULT_GROUP;

def getKernelVersion():
  return call('uname', '-r')[0].strip()

def isMountPoint(dirName):
  try:
    with open('/etc/mtab', 'r') as fid:
      for mount in fid:
        if dirName in mount.decode('string_escape'):
          return True
  except:
    pass
  try:
    with open('/proc/mounts', 'r') as fid:
      for mount in fid:
        if dirName in mount.decode('string_escape'):
          return True
  except:
    pass
  return not call('mountpoint', '-q', dirName)[2]

def mount_bind(fromDir, toDir):
  if not os.path.exists(toDir):
    mkpath(toDir);
  if not isMountPoint(toDir):
    call('mount', '--bind', fromDir, toDir)

def make_readonly_mount(mountDir):
  call('mount', '-o', 'remount,ro', mountDir)

def umount(toDir, force=False):
  if isMountPoint(toDir) or force:
    call('umount', toDir);

'''def setGroup(chroot_dir, group, gid):
  with open(path_join(chroot_dir, 'etc', 'group'), 'r') as fid:
    groups = fid.readlines();

  #Find and set the existing one
  for g in range(len(groups)):
    if groups[g].startswith('%s:'%group)
      group_line = groups[g].split(':')
      group_line[2] = str(gid)
      groups[g] = ':'.join(group_line)
      with open(path_join(chroot_dir, 'etc', 'group'), 'w') as fid:
        fid.writelines(groups);
      return

  #else add a new one
  group_line = groups[-1].split(':')
  group_line[0] = group
  group_line[2] = str(gid)
  groups.append(':'.join(group_line))

  with open(path_join(chroot_dir, 'etc', 'group'), 'w') as fid:
    fid.writelines(groups);
  return'''

if __name__=='__main__':

  parser = OptionParser(usage='%s  [options] chroot_dir' % __file__)
  parser.add_option("-s", "--simple", action='store_true', default=False,
                                      help="Just simply enter chroot as root, no fancy user stuff")
  parser.add_option("-u", "--user", help="user to clone from the host")
  parser.add_option("-g", "--group", help="group to clone from the host")
  parser.add_option("--uid", help="uid to use in the chroot")
  parser.add_option("--gid", help="gid to use in the chroot")
  parser.add_option("--openclinit", help="opencl init executable. Use something like ls to disable")
  parser.add_option("--hostmodules", help="Dir for /lib/modules/{kernelversion})")
  parser.add_option("--log", dest='loglevel', default='WARNING', help="Logging level")
  parser.add_option("--ssh", help="Alternative ssh folder used for copying ssh keys from. Default is ~user/.ssh/")
  (options, args) = parser.parse_args()

  logger.setLevel(getattr(logging, options.loglevel.upper(), None))
  console = logging.StreamHandler()
  logger.addHandler(console)

  if os.getuid() != 0:
    import sys
    logger.info("You aren't root, running command under sudo")
    cmd = ['sudo', os.path.abspath(__file__), os.path.abspath(sys.argv[1])] + sys.argv[2:]
    logger.info("Elevation command: %s", cmd)
    os.execlp('sudo', *cmd)
#    raise Exception("You must be root to chroot!")

  chroot_dir = os.path.abspath(args[0])
  if not os.path.isdir(chroot_dir):
    logger.critical("Chroot dir '%s' does not exist!" % chroot_dir)
    exit(2)

  # Determine who should be the user in the chroot
  if options.simple:  #Just be root
    chroot_user = 'root'
  else:
    chroot_user = options.user
    chroot_group = options.group
    chroot_uid = options.uid
    chroot_gid = options.gid

    if chroot_user is None:
      chroot_user = env.get('SUDO_USER', DEFAULT_USER)
    if chroot_group is None:
      chroot_group = groupFromName(chroot_user);
    if chroot_uid is None:
      chroot_uid = uidFromName(chroot_user);
    if chroot_gid is None:
      chroot_gid = gidFromName(chroot_user);

  if chroot_user == 'root' or int(chroot_uid)==0: 
  #incase the specified user is rootish, reset to BE root
    chroot_user = 'root'
    chroot_group = 'root'
    chroot_uid = 0
    chroot_gid = 0
    chroot_home = '/root'
  else:
    chroot_home = path_join('/home', chroot_user)

  if not options.simple:
    # OpenCL init function
    if options.openclinit is None:
      opencl_init=path_join(os.path.abspath(os.path.dirname(__file__)), 'opencl_init')
      if not os.path.exists(opencl_init):
        call('wget', 'https://vsi-ri.com/bin/init_ocl', '--no-check-certificate', '--quiet', '-O', opencl_init)
        os.chmod(opencl_init, 0755)
    else:
      opencl_init = options.openclinit

  # Host directore storing kernel modules
  if options.hostmodules is None:
    host_modules=path_join('/lib/modules', getKernelVersion())
  else:
    host_modules = options.hostmodules
  unchroot_host_modules = path_join(chroot_dir, host_modules.strip('/'))

  #Determine the OS variant. Important for dev/shm
  if os.path.exists('/etc/redhat-release'):
    with open('/etc/redhat-release', 'r') as fid:
      os_distro = fid.read().strip()
  elif os.path.exists('/etc/os-release'):
    with open('/etc/os-release', 'r') as fid:
      for line in fid.readlines():
        if line.split('=')[0] == 'NAME':
          os_distro = line.split('=', 1)[1].strip('"\'')
          break
  else:
    raise Exception("Unknown OS. Please add to this script")
  os_distro = os_distro.lower()
  #Determine true dev/shm dir
  if os_distro.startswith('centos') or os_distro.startswith('red'):
    dev_shm = '/dev/shm'
  elif os_distro.startswith('ubuntu') or os_distro.startswith('linuxmint'):
    dev_shm = '/run/shm'
  else:
    raise Exception("Unknown OS. Please add to this script")
  unchroot_dev_shm = path_join(chroot_dir, dev_shm.strip('/'))

  #Create home dir if it doesn't exist
  if not options.simple:
    unchroot_home = path_join(chroot_dir, chroot_home.strip('/'))
    if not os.path.exists(unchroot_home):
      mkpath(unchroot_home)
      os.chown(unchroot_home, chroot_uid, chroot_gid)

    sshDir = options.ssh
    if options.ssh is None:
      sshDir = os.path.expanduser(path_join('~%s' % chroot_user, '.ssh'))
      if os.path.exists(sshDir) and os.path.isdir(sshDir):
        logger.info('Copying ssh dir %s', sshDir)
        unchroot_ssh = path_join(unchroot_home, '.ssh')
        copy_tree(sshDir, unchroot_ssh)
        os.chown(unchroot_ssh, chroot_uid, chroot_gid)
        for f in glob(path_join(unchroot_ssh, '*')):
          os.chown(f, chroot_uid, chroot_gid)

  #Reset the home dir ownership, in case it did exist
  if chroot_user != 'root' and not options.simple:
    current_ownership = call('stat', '-c' '%u:%g', unchroot_home)[0].strip()
    if current_ownership != '%d:%d' % (chroot_uid, chroot_gid) and not current_ownership.startswith('0:'):
      #I can't risk running this if its owned by root. Under BAD mount bind conditions, this could reset the whole os
      # print "Resetting ownership of home dir from %s to %d:%d" % (current_ownership, chroot_uid, chroot_gid)
      # TOO DANGEROUS, what if you have a hardlink or mount --bind to / or something crazy like that!
      #chown -R -h -P ${CHROOT_UID}:${CHROOT_GID} ${BASE_DIR}${CHROOT_HOME} 
      #Much safer
      call('chown', '-R', '-h', '-P', '--from', current_ownership, unchroot_home)

  try:
    #Needed for dns support. Does not work with (ubuntu's on by default) stupid dnsmasq shit
    copy_file('/etc/resolv.conf', path_join(chroot_dir, 'etc'))
  except DistutilsFileError:
    logger.warning('Resolv.conf not copied. This is probably a dnsmasq issue. Solution unknown')
  
  if host_modules:
    mount_bind(host_modules, unchroot_host_modules)
    make_readonly_mount(unchroot_host_modules)
  mount_bind('/proc', path_join(chroot_dir, 'proc'))
  mount_bind('/dev', path_join(chroot_dir, 'dev'))
  mount_bind('/sys', path_join(chroot_dir, 'sys'))
  mount_bind('/dev/pts', path_join(chroot_dir, 'dev', 'pts'))
  mount_bind(dev_shm, unchroot_dev_shm);

  env['HISTFILE'] = path_join(chroot_home, '.bash_history')
  env['HOME'] = chroot_home
  env.pop('SUDO_USER', None)
  env.pop('SUDO_UID', None)
  env.pop('SUDO_GID', None)
  env.pop('SUDO_GROUP', None)

  if not options.simple:
    call(opencl_init)

  #This won't work if useradd or usermod or groupadd or groupmod are missing
  if not options.simple:
    call('chroot', chroot_dir, 'groupadd', '-g', str(chroot_gid), chroot_group)
    call('chroot', chroot_dir, 'groupmod', '-g', str(chroot_gid), chroot_group)
    call('chroot', chroot_dir, 'useradd', '-d', chroot_home, '-g', str(chroot_gid), '-s', '/bin/bash', chroot_user)
    call('chroot', chroot_dir, 'usermod', '-u', str(chroot_uid), '-g', str(chroot_gid), chroot_user)


    #safer way first :)
    if os.path.exists(path_join(chroot_dir, 'etc', 'sudoers.d')):
      with open(path_join(chroot_dir, 'etc', 'sudoers.d', 'chroot_fun'), 'w') as fid:
        fid.write('%s ALL=(ALL) NOPASSWD:ALL\n' % chroot_user)
    else: #I don't like doing this, but if I have to...
      chroot_sudoers = path_join(chroot_dir, 'etc', 'sudoers')
      if os.path.exists(chroot_sudoers):
        with open(chroot_sudoers, 'r') as fid:
          lines = fid.readlines()
          found = False
          for l in range(len(lines)):
            line = lines[l];
            parts = re.split('\s+', line)
            if parts[0] == chroot_user:
              line = '%s ALL=(ALL) NOPASSWD:ALL\n' % chroot_user
              lines[l] = l
              found = True
              break
          if not found:
            lines.append('\n%s ALL=(ALL) NOPASSWD:ALL\n' % chroot_user)
        with open(chroot_sudoers, 'w') as fid:
          fid.writelines(lines)

  #Copy the XAuth key
  if not options.simple:
    if 'XAUTHORITY' in env and os.path.exists(env['XAUTHORITY']):
      copy_file(env['XAUTHORITY'], path_join(unchroot_home, os.path.basename(env['XAUTHORITY'])))
      os.chown(path_join(unchroot_home, os.path.basename(env['XAUTHORITY'])), chroot_uid, chroot_gid)
      env['XAUTHORITY'] = path_join(chroot_home, os.path.basename(env['XAUTHORITY']))

  #print chroot_user, chroot_group, chroot_uid, chroot_gid, chroot_home, host_modules, os_distro, dev_shm
  cmd = ['chroot', '--userspec', '%d:%d' % (chroot_uid, chroot_gid), chroot_dir] + args[1:]
  logger.info('Chroot command: %s', cmd)
  Popen(cmd).wait()

  chroot_in_use = False
  chroot_stat = os.stat(chroot_dir)
  for proc in glob('/proc/[0-9]*'):
    try: #In case pid ceases to exist
      proc_stat = os.stat(path_join(proc, 'root'))
      if chroot_stat.st_ino == proc_stat.st_ino and \
         chroot_stat.st_dev == proc_stat.st_dev:
        chroot_in_use=True
        break
    except:
      pass

  if not chroot_in_use:
    umount(unchroot_host_modules, True)
    umount(path_join(chroot_dir, 'proc'), True)
    umount(unchroot_dev_shm, True)
    umount(path_join(chroot_dir, 'dev', 'pts'), True)
    umount(path_join(chroot_dir, 'dev'), True)
    umount(path_join(chroot_dir, 'sys'), True)
