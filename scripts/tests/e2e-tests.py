import os.path
from zipfile import ZipFile
import subprocess
import shutil
import sys
import json

if not os.path.exists("scripts/tests/e2e-tests.py"):
    sys.exit("This script is intended to be executed from the root folder.")
root = os.getcwd()

# First we build the extension
subprocess.call("npm run build".split(), cwd=root)
# the nwe clone gecko
subprocess.call("git clone hg::https://hg.mozilla.org/mozilla-central gecko".split(), cwd=root)
# We then remove the old extension
subprocess.call("rm -rf gecko/browser/extensions/translations/extension".split(), cwd=root)
# and extract the newly one built there
subprocess.call("unzip web-ext-artifacts/firefox_translations.xpi -d gecko/browser/extensions/translations/extension/".split(), cwd=root)
# copy the tests
subprocess.call("mkdir -p gecko/browser/extensions/translations/test/browser/".split(), cwd=root)
subprocess.call("cp scripts/tests/browser.ini gecko/browser/extensions/translations/test/browser/".split(), cwd=root)
subprocess.call("cp scripts/tests/browser_translation_test.html gecko/browser/extensions/translations/test/browser/".split(), cwd=root)
subprocess.call("cp scripts/tests/browser_translation_test.js gecko/browser/extensions/translations/test/browser/".split(), cwd=root)
subprocess.call("cp -r scripts/tests/esen/ gecko/browser/extensions/translations/test/browser/esen/".split(), cwd=root)

# let's download bergamot-translator-worker-with-wormhole.wasm
engineRegistryRootURL = ""
fileName = ""
with open('extension/model/engineRegistry.js') as fp:
        Lines = fp.readlines()
        for line in Lines:
            if "engineRegistryRootURL " in line:
                engineRegistryRootURL = line.split("=")[1].replace("\"","").replace(";","").strip()
            if "fileName:" in line:
                fileName = line.split(":")[1].replace("\"","").replace(",","").strip()

subprocess.call(("curl", "-L", "-o", "gecko/browser/extensions/translations/test/browser/"+fileName, engineRegistryRootURL + fileName), cwd=root)

# patching BrowserGlue.jsm
f = open("extension/manifest.json")
data = json.load(f)
extension_version = data["version"]
f.close()
with open("gecko/browser/components/BrowserGlue.jsm") as fp:
   count = 0
   Lines = fp.readlines()
   for line in Lines:
       if "resource://builtin-addons/translations/" in line:
           Lines[count - 1] = '            "{}",\n'.format(extension_version)
           with open("gecko/browser/components/BrowserGlue.jsm", "w") as outfile:
               outfile.write("".join(Lines))
           break
       count += 1

# enable our test
with open('gecko/mozconfig', 'w') as f:
    print('ac_add_options --enable-artifact-builds', file=f)

with open('gecko/browser/extensions/translations/moz.build', 'a') as f:
    print('BROWSER_CHROME_MANIFESTS += [\"test/browser/browser.ini\"]', file=f)

# build a and run our test
subprocess.call("./mach build".split(), cwd="gecko")
subprocess.call("./mach test browser/extensions/translations/test/browser/browser_translation_test.js".split(), cwd="gecko")