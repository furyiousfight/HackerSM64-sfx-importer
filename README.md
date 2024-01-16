# HackerSM64-sfx-importer
A command line tool designed to streamline the addition of custom sound effects for HackerSM64.

## Features
- Automatic sound bank creation and modification.
    - The tool automates the following changes:
        - Creates a copy of the given sound effect `.aiff` file within the associated sample folder
        - Sounds.h
            - On new bank creation:
                - Appends the new bank into the SoundBank enum, above `SOUND_BANK_COUNT`
                - Generates and appends an appropriate `SOULD_ARG_LOAD` line above the `#endif` near the bottom of the file
            - On adding to an existing bank:
                - Appends the appropraite `#define` below the most recent match, and updates the sound ID of the new line accordingly.
        - 00_sound_player.s
            - On new bank creation:
                - Appends an appropriate `seq_startchannel` with a calculated ID, and `.channel`` based on the given bank name.
                - Creates a `.channel` and associated table, places the new `sound_ref` within the table, and creates entry for the `.sound` and `.layer`
            - On adding to an existing bank:
                - Appends the new `sound_ref` to the appropriate table
                - Creates new entries below the associated table for the corresponding `.sound` and `.layer`
        - sequences.json
            - On new bank creation, appends the file name of the banks generated `.json` file to the array `"00_sound_player"`
        - `X`.json
            - On new bank creation:
                - Creates a `.json` file and associated sample folder, based on the given bank name
            - Handles the update or creation of the `instruments` and `instruments_list`
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
