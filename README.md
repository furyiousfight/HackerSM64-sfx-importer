# HackerSM64-sfx-importer
A command line tool designed to streamline the addition of custom sound effects for HackerSM64.

## Features
- Automatic sound bank creation and modification.
- Adding of new sound effects to custom banks.
- Automatic length detection of new sounds.
- Avoids creation of duplicate sound effects in a given bank.
- Case and Space insensitive to the names of sound banks, and sound effects.

## Known issues
- No support for vanilla sound banks.
- No support for looping sound effects.

## Requirements
- [FFmpeg](https://www.gyan.dev/ffmpeg/builds/)
- pydub
    - If not installed, Simply run `pip install -r requirements.txt` from the command line.

## Usage
- From the command line, run `sfx.py`
- From there you will be prompted to enter the following information:
    - Decomp directory
    - Sound effect file location
    - Bank name
    - Sfx name
- Ensure your sound effect file ends in a .aiff, e.g /SFX/Audio.aiff
- There is currently no support for vanilla banks, so avoid naming your custom bank any of the following:
    - ACTION
    - MOVING
    - VOICE
    - GENERAL
    - ENV
    - OBJ
    - AIR
    - MENU
    - GENERAL2
    - OBJ2

## Troubleshooting
- If you are having issues accessing a repository on a WSL2 partition, try the following filepath
    - //wsl.localhost/
    - Or, otherwise try copying the address from the windows explorer
- If you are experiencing issues with FFmpeg, ensure you are running a new instance of command prompt after setting the windows `PATH:`
