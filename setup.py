import urllib2
import os
import zipfile
import fnmatch
import platform
import shutil
from glob import glob

BASE_SDK_URL = "http://commondatastorage.googleapis.com/dart-archive/channels/dev/raw/latest/sdk/"
CUSTOM_SDK_URL = "https://raw.githubusercontent.com/IOT-DSA/dart-sdk-builds/master/"

sdk_urls = {
    "linux-ia32": BASE_SDK_URL + "dartsdk-linux-ia32-release.zip",
    "linux-x64": BASE_SDK_URL + "dartsdk-linux-x64-release.zip",
    "linux-armv5tel": CUSTOM_SDK_URL + "dgbox.zip",
    "linux-arm": CUSTOM_SDK_URL + "arm.zip",
    "darwin-ia32": BASE_SDK_URL + "dartsdk-macos-ia32-release.zip",
    "darwin-x64": BASE_SDK_URL + "dartsdk-macos-x64-release.zip",
    "windows-ia32": BASE_SDK_URL + "dartsdk-windows-ia32-release.zip",
    "windows-x64": BASE_SDK_URL + "dartsdk-windows-x64-release.zip"
}


def fetch(url, file_name):
    u = urllib2.urlopen(url)
    f = open(file_name, 'wb')
    meta = u.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    print "Downloading: %s Bytes: %s" % (file_name, file_size)

    file_size_dl = 0
    block_sz = 8192
    while True:
        buff = u.read(block_sz)
        if not buff:
            break

        file_size_dl += len(buff)
        f.write(buff)
        status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
        status = status + chr(8) * (len(status) + 1)
        print status
    f.close()


def extract_zip_file(name, target, check_single_dir=True):
    zfile = zipfile.ZipFile(name)

    zfile.extractall(target)
    if not check_single_dir:
        return
    files = glob(os.path.join(target, "*"))
    if len(files) == 1:
        main_dir = files[0]
        parent_dir = os.path.dirname(main_dir)
        all_files = recursive_glob(main_dir, "*")
        for oldfile in all_files:
            newfile = oldfile.replace(main_dir, parent_dir)
            os.renames(oldfile, newfile)


def recursive_glob(treeroot, pattern):
    results = []
    for base, dirs, files in os.walk(treeroot):
        goodfiles = fnmatch.filter(files, pattern)
        results.extend(os.path.join(base, f) for f in goodfiles)
    return results


def is_internet_on():
    try:
        urllib2.urlopen("https://www.google.com/", timeout=1)
        return True
    except urllib2.URLError:
        pass
    return False


def remove_if_exists(path):
    if os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)
    else:
        try:
            os.remove(path)
        except OSError:
            pass


def fail(msg):
    print("Failed: " + msg)
    exit(1)


if not is_internet_on():
    fail("You must be connected to the internet to use this tool.")

arch = platform.machine().lower()

if arch == "i386" or arch == "i686":
    arch = "ia32"

if arch == "x86_64":
    arch = "x64"

if arch != "armv5tel" and arch.__contains__("arm"):
    arch = "arm"

system_name = platform.system().lower()

system_id = system_name + "-" + arch

if not sdk_urls.__contains__(system_id):
    fail("Unsupported System Type: " + system_id)

remove_if_exists("dart-sdk")
remove_if_exists("dart-sdk.zip")
fetch(sdk_urls[system_id], "dart-sdk.zip")
extract_zip_file("dart-sdk.zip", "dart-sdk")
remove_if_exists("dart-sdk.zip")
for path in glob(os.path.join("dart-sdk", "bin", "*")):
    if os.path.isdir(path):
        continue

    try:
        os.chmod(path, 777)
    except OSError:
        pass
