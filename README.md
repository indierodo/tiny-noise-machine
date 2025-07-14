# Tiny Noise Machine

A background sound player for MacOS built with rumps, pygame and py2app. It's missing a better way to select the audio files, but it works.

## Download

Download from this repo's [releases page](https://github.com/indierodo/tiny-noise-machine/releases).

## Usage

Copy your audio files to this directory:

```
/Users/<YOUR-USER>/Library/com.indierodo.tinynoisemachine/content
```

Supported audio types: `.wav`, `.mp3`, `.ogg`, `.opus`, `.flac`, `.aiff`.

## Build

```
python -m pip install -r requirements.txt
python setup.py py2app
```

Modify your .app's file `__init__.py` using this [workaround](https://github.com/ronaldoussoren/py2app/issues/533#issuecomment-3070794107).

(Optional) Package it for distribution:

```
create-dmg \
  --volname "Tiny Noise Machine" \
  --window-pos 200 120 \
  --window-size 600 300 \
  --icon-size 100 \
  --icon "Tiny Noise Machine.app" 175 120 \
  --hide-extension "Tiny Noise Machine.app" \
  --app-drop-link 425 120 \
  "tiny-noise-machine.dmg" \
  "dist/"
```
