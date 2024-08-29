#!/bin/bash
pip install -r requirements.txt
output="$HOME/Applications/Tiny Noise Machine.app"
find . -name ".DS_Store" -delete
# python setup.py py2app -A
python setup.py py2app
rm -rf "$output"
mv "./dist/Tiny Noise Machine.app" "$output"
open "$output"