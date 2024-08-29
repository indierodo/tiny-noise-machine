from setuptools import setup

APP = ['Tiny Noise Machine.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'plist': {
        'LSUIElement': True,
    },
    'packages': ['rumps', 'pygame', 'Quartz'],
    'iconfile': 'tinynoisemachineicon.icns',
    'resources': ['content']
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)