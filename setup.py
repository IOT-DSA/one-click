from sys import stdin, stdout
import urllib2
import os
import zipfile
import fnmatch
import platform
import shutil
import json
import stat

from glob import glob

OFFLINE = False

DART_SDK_BASE_URL = "https://commondatastorage.googleapis.com/dart-archive/channels/dev/raw/latest/sdk/"
DART_SDK_CUSTOM_URL = "https://raw.githubusercontent.com/IOT-DSA/dart-sdk-builds/master/"
DART_SDK_VERSION = "1.17.1";
DART_SDK_CHANNEL = "stable";

LINK_BASE_URL = "https://dsa.s3.amazonaws.com/links/";
DIST_BASE_URL = "https://dsa.s3.amazonaws.com/dists/";


def get_dart_dl_url(platform):
    if not (platform.startswith("linux-") or platform.startswith("windows-") or
            platform.startswith("macos-")):
        return "https://iot-dsa.github.io/dart-sdk-builds/{0}".format(platform)
    return "https://commondatastorage.googleapis.com/dart-archive/channels/{0}/raw/{1}/sdk/dartsdk-{2}-release.zip".format(DART_SDK_CHANNEL, DART_SDK_VERSION, platform)


def fetch(url, file_name):
    print("Fetching %s" % (url))
    u = urllib2.urlopen(url)
    f = open(file_name, 'wb')
    meta = u.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    print("Fetch %s (%s bytes)" % (file_name, file_size))

    file_size_dl = 0
    block_sz = 8192
    while True:
        buff = u.read(block_sz)
        if not buff:
            break

        file_size_dl += len(buff)
        f.write(buff)
        status = r"%10d of %d bytes [%3.2f%%]" % (file_size_dl, file_size, file_size_dl * 100. / file_size)
        status += chr(8) * (len(status) + 1)
        stdout.write(status + "\r")
        stdout.flush()
    f.close()
    print("")


def remove_if_exists(npath):
    if os.path.isdir(npath):
        shutil.rmtree(npath, ignore_errors=True)
    else:
        try:
            os.remove(npath)
        except OSError:
            pass


def read_json_url(url):
    u = urllib2.urlopen(url)
    content = u.read()
    return json.loads(content)


def extract_zip_file(name, target, check_single_dir=True):
    print("Extract " + name)
    remove_if_exists(target)
    os.makedirs(target)

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
        remove_if_exists(main_dir)


def recursive_glob(treeroot, pattern):
    results = []
    for base, dirs, files in os.walk(treeroot):
        goodfiles = fnmatch.filter(files, pattern)
        results.extend(os.path.join(base, f) for f in goodfiles)
    return results


def is_internet_on():
    try:
        urllib2.urlopen(DIST_BASE_URL + "dists.json", timeout=1)
        return True
    except urllib2.URLError:
        pass
    return False


def fail(msg):
    print("Failed: " + msg)
    exit(1)


if not is_internet_on():
    fail("You must be connected to the internet to use this tool.")

if not OFFLINE:
    if os.path.exists("dglux-server"):
        fail("You already have a distribution installed.")

    arch = platform.machine().lower()

    if arch == "i386" or arch == "i686":
        arch = "ia32"

    if arch == "x86_64":
        arch = "x64"

    if arch == "amd64":
        arch = "x64"

    if arch != "armv5tel" and arch.__contains__("arm"):
        arch = "arm"

    system_name = platform.system().lower()

    system_id = system_name + "-" + arch

    system_id = system_id.replace("darwin-", "macos-")

    # TODO: Reimplement platform failsafe
    #if not sdk_urls.__contains__(system_id):
        #fail("Unsupported System Type: " + system_id)

    remove_if_exists("dart-sdk")
    remove_if_exists("dart-sdk.zip")
    fetch(get_dart_dl_url(system_id), "dart-sdk.zip")

extract_zip_file("dart-sdk.zip", "dart-sdk")
remove_if_exists("dart-sdk.zip")

for path in glob(os.path.join("dart-sdk", "bin", "*")):
    if os.path.isdir(path):
        continue

    try:
        mode = os.stat(path).st_mode
        mode |= (mode & 292) >> 2
        os.chmod(path, mode)
    except OSError:
        pass


if not OFFLINE:
    dist_info = read_json_url(DIST_BASE_URL + "dists.json")
    dists = dist_info["dists"]

    mid = 1

    mapping = {}
    idx = 1

    for key in dists.keys():
        mapping[mid] = key
        mid += 1

    print("Choose your distribution:")

    for nkey in dists.keys():
        display_name = dists[nkey]["displayName"]
        print("- [" + str(idx) + "] " + display_name)
        idx += 1


    def do_select():
        stdout.write("Distribution: ")
        result = stdin.readline()
        try:
            mr = int(result)

            if mr < 1 or mr > mid - 1:
                print("Invalid Distribution.")
                return do_select()

            return mapping[mr]
        except SyntaxError:
            print("Invalid Distribution.")
            return do_select()

    dist_id = do_select()
    dist = dists[dist_id]
    base_url = dist_info.get("baseUrl", DIST_BASE_URL)
    fetch(base_url + dist_id + "/" + dist["latest"] + "/" + dist["file"], "dglux-server.zip")
else:
    if not os.path.exists("dart-sdk.zip"):
        fail("Dart SDK is missing in the offline package.")
    if not os.path.exists("dglux-server.zip"):
        fail("Distribution is missing in the offline package.")

extract_zip_file("dglux-server.zip", "dglux-server")
remove_if_exists("dglux-server.zip")
