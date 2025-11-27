#!/usr/bin/env false

#*# linux/common_source

# Use the sh POSIX compliant version of source_once
source_once > /dev/null 2>&1 && return 0

#**
# =============
# Common Source
# =============
#
# .. default-domain:: bash
#
# .. file:: common_source.sh
#
# Cross OS compatible common values files
#
# There are many differences between bash scripts between Windows (using mingw/cygwin), macOS (which uses a MODIFIED version of bash 3.2), and the many versions of Linux out there, that primarily use bash 4+. In addition to the shell behaving different, many pieces of basic information are retrieved in different ways, such as the kind of OS, number of processor cores, etc... This sets a collection of variables to try and normalize these behaviors for other vsi scripts to use, no matter what OS they are running on.
#
# .. note::
#   Should be Bourne Shell compatible, not just Bourne again shell compatible.
#**

#**
# .. envvar:: VSI_OS
#
# Operating system name
#
# Lowercase representation of the Operating system name. Based off of the ``OSTYPE`` environment variable, which is always defined in Bourne Shell.
#
# .. rubric:: Example
#
# Values include linux, darwin, windows, bsd, solaris, and unknown
#
# .. note::
#   Only systems that are not EOL are considered. For example, Windows 95 doesn't have the wmic used, but is pass end-of-life, so it is not a concern.
#
# .. seealso::
#   :envvar:`VSI_DISTRO`, :envvar:`VSI_DISTRO_VERSION`
#**

#**
# .. envvar:: VSI_PATH_ESC
#
# Path escape string for windows path translation
#
# MSYS2, Git for Windows, etc.. translate unix style paths to windows style for you when even you call a non-bash command. This helps bridge the gap between the unix style systems and windows. However, sometimes it translates too much, which can cause a lot of issue.
#
#   This environment variable exists to add a / on Windows, and null on all other OSes
#
# .. rubric:: Example
#
# .. code-block:: bash
#
#     foo -v /tmp:/tmp
#   Becomes
#     foo -v C:/Users/user/AppData/Temp:C:/Users/user/AppData/Temp
#
#   But what you really might want is
#     foo -v C:/Users/user/AppData/Temp:/tmp
#
#   Using VSI_PATH_ESC
#     foo -v /tmp:${VSI_PATH_ESC}/tmp
#   Becomes
#     foo -v C:/Users/user/AppData/Temp://tmp
#
# .. note::
#   Cygwin does not automatically translate paths, you have to explicitly call cygpath, so :envvar:`VSI_PATH_ESC` is set to null. Using cygwin will take a lot more work, and is usually less preferred for this reason
#
# .. rubric:: Bugs
#
# There is a // artifact left over when there should be a /. This usually does not cause problems, but on rare occasions it does. It is ugly on all occasions.
#**

# In general, sh doesn't set OSTYPE; bash always does
: ${OSTYPE=$(uname | tr '[A-Z]' '[a-z]')}

VSI_PATH_ESC=''

case "${OSTYPE}" in
  linux*)
    VSI_OS=linux
    ;;
  darwin*)
    VSI_OS=darwin
    VSI_DISTRO=darwin
    VSI_DISTRO_VERSION="$(sw_vers -productVersion)"
    ;;
  win32*|cygwin*|msys*|ming*)
    VSI_OS=windows
    VSI_DISTRO=windows
    VSI_DISTRO_VERSION="$(wmic os get version /format:table | sed -n 2p)"
    if ! [[ ${OSTYPE} =~ cygwin.* ]]; then
      VSI_PATH_ESC='/'
    fi
    ;;
  solaris*)
    VSI_OS=solaris
    VSI_DISTRO="${OSTYPE}"
    read VSI_DISTRO_VERSION < /etc/release
    VSI_DISTRO_VERSION="${VSI_DISTRO_VERSION% *}"
    VSI_DISTRO_VERSION="${VSI_DISTRO_VERSION#* }"
    ;;
  *bsd*)
    VSI_OS=bsd
    VSI_DISTRO="${OSTYPE}"
    VSI_DISTRO_VERSION="$(uname -r)"
    ;;
  *)
    VSI_OS=unknown
    VSI_DISTRO=unknown
    VSI_DISTRO_VERSION=unknown
    ;;
esac

#**
# .. envvar:: VSI_MUSL
#
#   :Value: * ``0`` - Not a musl libc OS
#           * ``1`` - Is a musl libc based OS
#           * ``-1`` - Unable to determine
#
# Checks to see if this is a musl based operating system. Inspect the grep executable for the string "musl". If it is found, like on alpine, then this is marked as a musl libc OS ``1``, else ``0``.
#**

# Default: I can't figure it out, probably glibc
VSI_MUSL=-1
if command -v ldd 2>&1 > /dev/null; then
  if ! VSI_MUSL=$(ldd --version 2>&1); then
    # Some versions of ldd fail when using the --version flag, but succeed on
    # no flag
    VSI_MUSL="$(ldd 2>&1 || :)"
  fi
  # Was musl not found in first line
  if command -v awk 2>&1 > /dev/null; then
    if echo "${VSI_MUSL}" | awk '{if (NR < 2 && $0 ~ /musl/) {exit 1} else {exit 0}}'; then
      VSI_MUSL=0
    else
      VSI_MUSL=1
    fi
  else
    if echo "${VSI_MUSL}" | head -n1 | grep -q musl; then
      VSI_MUSL=1
    else
      VSI_MUSL=0
    fi
  fi
fi

# Old highly unreliable method
# if grep -q musl "$(unalias grep &> /dev/null || :; unset grep; command -v grep)"; then
#   VSI_MUSL=1
# else
#   VSI_MUSL=0
# fi

#**
# .. envvar:: VSI_DISTRO
#
# Name of the distribution.
#
# For the various Linux distributions, it is often hard to know what OS you are dealing with. :envvar:`VSI_DISTRO` will tell you the name of the distribution, which is typically all lowercase (in all test cases). Many different versions store the distribution name in different locations---only most modern Linux distributions use the standard /etc/os-release, but many LTS distributions that are not EOL (end-of-life) use less standard methods. This variable checks all of these known possibilities.
#
# .. note::
#   Other OSes like Windows, Mac, BSD, and solaris will have something set to :envvar:`VSI_DISTRO`
#
#   +----------+-----------+--------------------------+
#   |  OS      | VSI_DISTRO|                          |
#   +==========+===========+==========================+
#   |  Windows | windows   | (same as VSI_OS)         |
#   +----------+-----------+--------------------------+
#   |  BSDs    | ${OS_TYPE}| (expected bsd*, freebsd*)|
#   +----------+-----------+--------------------------+
#   |  Solaris | ${OS_TYPE}| (expected solaris*)      |
#   +----------+-----------+--------------------------+
#   |  Mac     | darwin    | (same as VSI_OS)         |
#   +----------+-----------+--------------------------+
#
# .. seealso::
#   :envvar:`VSI_DISTRO_LIKE` :envvar:`VSI_DISTRO_CORE`
#**

#**
# .. envvar:: VSI_DISTRO_VERSION
#
# The version of the distribution
#
# .. note::
#   For non-Linux distributions, this is the same as the :envvar:`VSI_OS_VERSION`
#
#   Understanding Windows versions
#
#    +----+-------------------------------------------------+
#    |10.0|Windows 10     and Windows Server 2016           |
#    +----+-------------------------------------------------+
#    |6.3 |Windows 8.1    and Windows Server 2012R2         |
#    +----+-------------------------------------------------+
#    |6.2 |Windows 8      and Windows Server 2012           |
#    +----+-------------------------------------------------+
#    |6.1 |Windows 7      and Windows Server 2008R2         |
#    +----+-------------------------------------------------+
#    |6.0 |Windows Vista  and Windows Server 2008           |
#    +----+-------------------------------------------------+
#    |5.2 |Windows XP x64 and Windows Server 2003 and 2003R2|
#    +----+-------------------------------------------------+
#    |5.1 |Windows XP                                       +
#    +----+-------------------------------------------------+
#    |5.0 |Windows 2000     and Windows 2000 Server         |
#    +----+-------------------------------------------------+
#    |4.0 |Windows NT 4.0   and Windows NT 4.0 Server       |
#    +----+-------------------------------------------------+
#    |3.51|Windows NT 3.51 and Windows NT 3.51 Server       |
#    +----+-------------------------------------------------+
#    |3.5 |Windows NT 3.5 and Windows NT 3.5 Server         |
#    +----+-------------------------------------------------+
#    |3.10|Windows NT 3.1 and Windows NT 3.1 Server         |
#    +----+-------------------------------------------------+
#    |------------------- NT line                           |
#    +----+-------------------------------------------------+
#    |4.90|Windows Me                                       |
#    +----+-------------------------------------------------+
#    |4.10|Windows 98                                       |
#    +----+-------------------------------------------------+
#    |4.00|Windows 95                                       |
#    +----+-------------------------------------------------+
#    |3.2 |Windwos 3.2                                      |
#    +----+-------------------------------------------------+
#    |3.11|Windwos 3.11                                     |
#    +----+-------------------------------------------------+
#    |3.10|Windows 3.1                                      |
#    +----+-------------------------------------------------+
#    |3.00|Windows 3.0                                      |
#    +----+-------------------------------------------------+
#    |2.11|Windows 2.11                                     |
#    +----+-------------------------------------------------+
#    |2.10|Windows 2.10                                     |
#    +----+-------------------------------------------------+
#    |2.03|Windows 2.03                                     |
#    +----+-------------------------------------------------+
#    |1.04|Windows 1.04                                     |
#    +----+-------------------------------------------------+
#    |1.03|Windows 1.03                                     |
#    +----+-------------------------------------------------+
#    |1.02|Windows 1.02                                     |
#    +----+-------------------------------------------------+
#    |1.01|Windows 1.01                                     |
#    +----+-------------------------------------------------+
#
# .. seealso::
#   :envvar:`VSI_DISTRO_VERSION_LIKE` :envvar:`VSI_DISTRO_VERSION_CORE`
#**

#**
# .. envvar:: VSI_DISTRO_LIKE
#
# Name of the distribution this distribution is based off of
#
# Some os-release files typically have an ID_LIKE to specify which distribution it was based off of. For example Ubuntu is based off of debian and Mint is based off of Ubuntu. This captures and stores that "like" behavior.
#
# This is not as useful as the :envvar:`VSI_DISTRO_CORE` which is more useful in determining "should I use yum or apt, etc..."
#
# .. seealso::
#   :envvar:`VSI_DISTRO` :envvar:`VSI_DISTRO_CORE`
#**

#**
# .. envvar:: VSI_DISTRO_VERSION_LIKE
#
# Version of :envvar:`VSI_DISTRO_LIKE`
#
# The version release (number when possible) of the :envvar:`VSI_DISTRO_LIKE`. This is not as useful as :envvar:`VSI_DISTRO_VERSION_CORE` for determining things such as "For this fedora based distributions, should I be using dnf or yum". If it was centos, ``_LIKE`` would be rhel, and ``_CORE`` would be fedora, and then all you would need to check is if the fedora version (:envvar:`VSI_DISTRO_VERSION_CORE`) is >= 22 or not.
#
# .. seealso::
#   :envvar:`VSI_DISTRO` :envvar:`VSI_DISTRO_CORE`
#**

#**
# .. envvar:: VSI_DISTRO_CORE
#
# Name of the distribution this distribution is based off of
#
# Unlike :envvar:`VSI_DISTRO_LIKE`, :envvar:`VSI_DISTRO_CORE` will tell you the distribution that this distribution is REALLY based off of. For example, centos is "like" rhel but they are both really fedora at the core. Which means they use yum, etc. This is what really matters for a lot of logic that you would be using these variables in the first place.
#
# While the ``_LIKE`` variable identifies the parent distribution, ``_CORE`` should identify the progenitor, typically debian, fedora, slackware, gentoo, etc...
#
# .. seealso::
#   :envvar:`VSI_DISTRO_VERSION_CORE` :envvar:`VSI_DISTRO`
#**

#**
# .. envvar:: VSI_DISTRO_VERSION_CORE
#
# Version of :envvar:`VSI_DISTRO_CORE`
#
# The version of the :envvar:`VSI_DISTRO_CORE` that the distribution is based off of
#
# .. seealso::
#   :envvar:`VSI_DISTRO_CORE`
#**

if [ -f "/etc/os-release" ]; then
  # Run in a sub-shell so I can source os-release
  VSI_DISTRO="$(. /etc/os-release;

                # Only Ubuntues have this file
                # Fix bug https://bugs.launchpad.net/linuxmint/+bug/1641491
                if [ -f "/etc/lsb-release" ]; then
                  . /etc/lsb-release
                  DISTRIB_ID="$(echo ${DISTRIB_ID} | sed 's|.*|\L&|')"
                  if [ "${DISTRIB_ID}" != "${ID}" ]; then
                    echo "Fixing" >&2
                    ID_CORE="${ID_LIKE}"
                    ID_LIKE="${ID}"
                    ID="${DISTRIB_ID}"
                    VERSION_LIKE="${VERSION_ID}"
                    VERSION_ID="${DISTRIB_RELEASE}"
                  fi
                fi

                # Get gentoo version
                if [ -f "/etc/gentoo-release" ]; then
                  read VERSION < /etc/gentoo-release
                  VERSION_ID="${VERSION##* }"
                fi

                # Capture ubuntu derivatives are debian derived
                if [ "${ID_LIKE-}" = "ubuntu" ]; then
                  ID_CORE=debian
                # Opensuse leap does it in the backwards order of centos
                elif [ "${ID-}" = "opensuse-leap" ]; then
                  ID_CORE="${ID_LIKE%% *}"
                  ID_LIKE="${ID_LIKE#* }"
                # If there is a space, this is like centos that says "rhel fedora"
                elif [ "${ID_LIKE+set}" = "set" ] && [ "${ID_LIKE}" != "${ID_LIKE%% *}" ]; then
                  ID_CORE="${ID_LIKE#* }"
                  ID_LIKE="${ID_LIKE%% *}"
                fi

                # Some distros like mint store the like version here
                if [ "${UBUNTU_CODENAME+set}" = "set" ]; then
                  : ${VERSION_LIKE=${UBUNTU_CODENAME}}
                fi

                # copy right
                : ${ID_LIKE="${ID}"}
                : ${VERSION_LIKE="${VERSION_ID-}"}
                : ${ID_CORE="${ID_LIKE}"}
                : ${VERSION_CORE="${VERSION_LIKE}"}

                # Pass the results out out
                echo "${ID}:${VERSION_ID-}:${ID_LIKE}:${VERSION_LIKE}:${ID_CORE}:${VERSION_CORE}"
              )"

  #DISTRO:VERSION:MIDDLE_DISTRO:MIDDLE_VERSION:CORE_DISTRO:CORE_VERSION
  # Parse the answer
  VSI_DISTRO_VERSION_CORE="${VSI_DISTRO##*:}"
  VSI_DISTRO="${VSI_DISTRO%:*}"
  VSI_DISTRO_CORE="${VSI_DISTRO##*:}"
  VSI_DISTRO="${VSI_DISTRO%:*}"
  VSI_DISTRO_VERSION_LIKE="${VSI_DISTRO##*:}"
  VSI_DISTRO="${VSI_DISTRO%:*}"
  VSI_DISTRO_LIKE="${VSI_DISTRO##*:}"
  VSI_DISTRO="${VSI_DISTRO%:*}"
  VSI_DISTRO_VERSION="${VSI_DISTRO##*:}"
  VSI_DISTRO="${VSI_DISTRO%:*}"

  # If a debian derivative
  if [ "${VSI_DISTRO}" != "${VSI_DISTRO_CORE}" ] && [ "${VSI_DISTRO_CORE}" = "debian" ]; then
    # Read the debian version here
    read VSI_DISTRO_VERSION_CORE < /etc/debian_version
  fi

# Remove this special case after 30 Nov 2020
# Older redhats don't have os-release. Read it here
elif [ -f "/etc/redhat-release" ]; then
  read VSI_DISTRO < /etc/redhat-release
  VSI_DISTRO_VERSION="${VSI_DISTRO#* * }"

  # Remove all but the first part (the version)
  VSI_DISTRO_VERSION="${VSI_DISTRO_VERSION%% *}"

  # Need to be remain sh parsable compatible
  # get distro (lowercased)
  VSI_DISTRO="$(echo "${VSI_DISTRO%% *}" | sed s"|.*|\L&|")"
  # VSI_DISTRO=$(sed s"|.*|\L&|" <<< ${VSI_DISTRO%% *})

# Remove this special case after 31 Mar 2022
# Older sles doesn't have an os-release. Read it here
elif [ -f "/etc/SuSE-release" ]; then
  {
    read VSI_DISTRO
    read VSI_DISTRO_VERSION
    read VSI_DISTRO_VERSION_LIKE
  }< /etc/SuSE-release

  # simplify
  if [[ ${VSI_DISTRO} =~ 'SUSE Linux Enterprise Server' ]]; then
    VSI_DISTRO=sles
  fi
  # Parse the version number out, and put it together
  VSI_DISTRO_VERSION="${VSI_DISTRO_VERSION##* }.${VSI_DISTRO_VERSION_LIKE##* }"
  VSI_DISTRO_VERSION_LIKE="${VSI_DISTRO_VERSION}"

# Slackware
elif [ -f "/etc/slackware-version" ]; then
  read VSI_DISTRO < /etc/slackware-version
  VSI_DISTRO_VERSION="${VSI_DISTRO##* }"
  VSI_DISTRO="${VSI_DISTRO% *}"
  VSI_DISTRO="$(echo "${VSI_DISTRO}" | tr '[A-Z]' '[a-z]')"

# Special case for arch linux
elif [ -f "/etc/arch-release" ]; then
  VSI_DISTRO=arch
  VSI_DISTRO_VERSION=''

# Special case for clearlinux
elif [ -f "/usr/share/clear/version" ]; then
  VSI_DISTRO='clearlinux'
  read VSI_DISTRO_VERSION < /usr/share/clear/version || :
  # EOF is reached, but that's ok

# Special case for busybox
elif command -v busybox >/dev/null 2>&1; then
  VSI_DISTRO="$(busybox | head -n 1)"
  VSI_DISTRO_VERSION="${VSI_DISTRO#* v}"
  VSI_DISTRO_VERSION="${VSI_DISTRO_VERSION%% *}"
  VSI_DISTRO="$(echo "${VSI_DISTRO%% *}" | tr '[A-Z]' '[a-z]')"
else
  : ${VSI_DISTRO=unknown}
  : ${VSI_DISTRO_VERSION='?'}
fi

# Handle rhel intricacies
if [ "${VSI_DISTRO}" = "centos" ] || \
   [ "${VSI_DISTRO}" = "rocky" ] || \
   [ "${VSI_DISTRO}" = "rhel" ]; then
  VSI_DISTRO_CORE=fedora
  VSI_DISTRO_VERSION=${VSI_DISTRO_VERSION%%.*}
  VSI_DISTRO_VERSION_LIKE="${VSI_DISTRO_VERSION_LIKE%%.*}"

  # https://access.redhat.com/support/policy/updates/errata
  case "${VSI_DISTRO_VERSION}" in
    4*) VSI_DISTRO_VERSION_CORE=3       ;; # Mostly EOL (ELS)
    5*) VSI_DISTRO_VERSION_CORE=6       ;; # ELS
    6*) VSI_DISTRO_VERSION_CORE="13 14" ;; # ELS Jun 30, 2020
    7*) VSI_DISTRO_VERSION_CORE=19      ;; # EOL Jun 30, 2024
    8*) VSI_DISTRO_VERSION_CORE=28      ;; # EOL May 31, 2029
    9*) VSI_DISTRO_VERSION_CORE=34      ;; # EOL May 31, 2032
  esac

  if [ "${VSI_DISTRO}" = "centos" ]; then
    : ${VSI_DISTRO_LIKE=rhel}
  elif [ "${VSI_DISTRO}" = "rhel" ]; then
    VSI_DISTRO_LIKE="${VSI_DISTRO_CORE}"
  fi
fi

# Turn debian codenames to numbers
# https://wiki.debian.org/DebianReleases
if [ "${VSI_DISTRO_CORE-}" = "debian" ]; then
  # Remove the /sid for some debian derivatives
  VSI_DISTRO_VERSION_CORE="${VSI_DISTRO_VERSION_CORE%/sid}"
  # turn codenames to numbers
  case "${VSI_DISTRO_VERSION_CORE-}" in
    squeeze)  VSI_DISTRO_VERSION_CORE=6  ;; # LTS Feb 29 2016
    wheezy)   VSI_DISTRO_VERSION_CORE=7  ;; # ELTS ~2020-06-30
    jessie)   VSI_DISTRO_VERSION_CORE=8  ;; # ELTS ~2022-06-30
    stretch)  VSI_DISTRO_VERSION_CORE=9  ;; # EOL 2020-07-06 LTS 2022-06-30
    buster)   VSI_DISTRO_VERSION_CORE=10 ;; # EOL 2022-08
    bullseye) VSI_DISTRO_VERSION_CORE=11 ;; # Release 2021-08-14 EOL +3years?
    bookworm) VSI_DISTRO_VERSION_CORE=12 ;; # Release ?
    trixie)   VSI_DISTRO_VERSION_CORE=13 ;; # Release ?
  esac
fi

# Fix the case when OSes like mint are like ubuntu but use the codename
# https://wiki.ubuntu.com/Releases
# https://launchpad.net/ubuntu/
if [ "${VSI_DISTRO_LIKE-}" = "ubuntu" ]; then
  case "${VSI_DISTRO_VERSION_LIKE-}" in
    precise) VSI_DISTRO_VERSION_LIKE=12.04 ;; # EOL Apr 28, 2017
    trusty)  VSI_DISTRO_VERSION_LIKE=14.04 ;; # EOL Apr, 2019, ESM Apr 2022
    utopic)  VSI_DISTRO_VERSION_LIKE=14.10 ;; # EOL Jul 23,  2015
    vivid)   VSI_DISTRO_VERSION_LIKE=15.04 ;; # EOL Feb 4, 2016
    wily)    VSI_DISTRO_VERSION_LIKE=15.10 ;; # EOL Jul 28, 2016
    xenial)  VSI_DISTRO_VERSION_LIKE=16.04 ;; # EOL Apr 2021, ESM Apr 2024
    yakkety) VSI_DISTRO_VERSION_LIKE=16.10 ;; # EOL Jul 20, 2017
    zesty)   VSI_DISTRO_VERSION_LIKE=17.04 ;; # EOL Jan 13, 2018
    artful)  VSI_DISTRO_VERSION_LIKE=17.10 ;; # EOL Jul 19, 2018
    bionic)  VSI_DISTRO_VERSION_LIKE=18.04 ;; # EOL Apr 2023, ESM Apr 2028
    cosmic)  VSI_DISTRO_VERSION_LIKE=18.10 ;; # EOL Jul 18, 2019
    disco)   VSI_DISTRO_VERSION_LIKE=19.04 ;; # EOL Jan 23, 2020
    eoan)    VSI_DISTRO_VERSION_LIKE=19.10 ;; # EOL Jul 17, 2020
    focal)   VSI_DISTRO_VERSION_LIKE=20.04 ;; # EOL April 2025, ESM Apr 2030
    groovy)  VSI_DISTRO_VERSION_LIKE=20.10 ;; # EOL July 22, 2021
    hirsute) VSI_DISTRO_VERSION_LIKE=21.04 ;; # EOL ~Jan 2022
    impish)  VSI_DISTRO_VERSION_LIKE=21.10 ;; # EOL July 2022
    jammy)   VSI_DISTRO_VERSION_LIKE=22.04 ;; # EOL April 2027, ESM Apr 2032
    kinetic) VSI_DISTRO_VERSION_LIKE=22.10 ;; # Release October 20, 2022 EOL ~July 2023
  esac
fi

# Copy unknowns right
: ${VSI_DISTRO_LIKE="${VSI_DISTRO}"}
: ${VSI_DISTRO_VERSION_LIKE="${VSI_DISTRO_VERSION}"}
: ${VSI_DISTRO_CORE="${VSI_DISTRO_LIKE}"}
: ${VSI_DISTRO_VERSION_CORE="${VSI_DISTRO_VERSION_LIKE}"}

# This makes copying version left easy
if [ "${VSI_DISTRO_CORE}" = "${VSI_DISTRO_LIKE}" ]; then
  VSI_DISTRO_VERSION_LIKE="${VSI_DISTRO_VERSION_CORE}"
fi

#**
# .. envvar:: VSI_OS_VERSION
#
# Version of the operating system
#
# For the Windows operating systems, this is the same as :envvar:`VSI_DISTRO_VERSION`. For Linux/Unix based operating systems, this will evaluate to the kernel version
#
# .. seealso::
#   :envvar:`VSI_DISTRO_VERSION`
#**

case VSI_OS in
  windows)
     VSI_OS_VERSION="${VSI_DISTRO_VERSION}"
     ;;
  *)
     VSI_OS_VERSION="$(uname -r)"
     ;;
esac

#**
# .. envvar:: VSI_ARCH
#
# System architecture
#
# The architecture of the CPU in use (same as uname -m)
#
# .. rubric:: Example
#
# Possible values include (but may not be limited to)
#
# .. code-block:: bash
#
#   i386 i686 x86_64 ia64 alpha amd64 arm armeb armel hppa m32r m68k mips
#   mipsel powerpc ppc64 s390 s390x sh3 sh3eb sh4 sh4eb sparc
#
#   Typically found: x86_64
#**

VSI_ARCH="$(uname -m)"

#**
# .. envvar:: VSI_NUMBER_CORES
#
# Determines the number of CPU cores available on the machine.
#**

case "${VSI_OS}" in
  darwin)
    if [ "$(sw_vers -buildVersion)" = "Darling" ]; then
      VSI_DISTRO=darling
    fi
    if command -v sysctl >/dev/null 2>&1; then # Normal darwin
      VSI_NUMBER_CORES="$(\sysctl -n hw.logicalcpu)"
    elif [ -f "/Volumes/SystemRoot/proc/cpuinfo" ]; then # darling
      VSI_NUMBER_CORES="$(\grep processor /Volumes/SystemRoot/proc/cpuinfo | wc -l)"
      # Left trim white spaces
      VSI_NUMBER_CORES="${VSI_NUMBER_CORES#"${VSI_NUMBER_CORES%%[![:space:]]*}"}"
    else
      echo "Warning: unable to determine number of cores" >&2
      VSI_NUMBER_CORES=4
    fi
    ;;
  windows)
    VSI_NUMBER_CORES="${NUMBER_OF_PROCESSORS}"
    ;;
  *)
    if command -v nproc >/dev/null 2>&1; then
      VSI_NUMBER_CORES="$(\nproc)"
    elif [ -f "/proc/cpuinfo" ]; then
      VSI_NUMBER_CORES="$(\grep processor /proc/cpuinfo | wc -l)"
    else
      echo "Warning: unable to determine number of cores" >&2
      VSI_NUMBER_CORES=4
    fi
    ;;
esac
