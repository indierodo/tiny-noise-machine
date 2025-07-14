from setuptools import setup

APP = ['main.py']
DATA_FILES = []
OPTIONS = {
   'argv_emulation': False,
   'plist': {
       'LSUIElement': True,
       'CFBundleName': 'Tiny Noise Machine',
       'CFBundleDisplayName': 'Tiny Noise Machine',
       'CFBundleIdentifier': 'com.indierodo.tinynoisemachine',
   },
   'packages': ['rumps', 'pygame', 'Quartz'],
   'iconfile': 'tinynoisemachineicon.icns',
}

setup(
   app=APP,
   data_files=DATA_FILES,
   options={'py2app': OPTIONS},
   setup_requires=['py2app'],
)