import shutil
import os
import re
import subprocess
import json
from pathlib import Path
import glob
from pydub.utils import mediainfo

def set_decomp_directory(decomp_dir):
    # Expand the WSL path using os.path.expanduser
    decomp_dir = os.path.expanduser(decomp_dir)

    # Check if the specified directory exists
    if not os.path.exists(decomp_dir):
        print("Invalid decomp directory. Please provide a valid path.")
        return False

    # Check if sm64.ld file exists in the base directory
    sm64_ld_path = os.path.join(decomp_dir, 'sm64.ld')
    if not os.path.exists(sm64_ld_path):
        print("Invalid decomp directory. Please provide a valid path.")
        return False

    # Set the decomp directory as a global variable or use it as needed
    global decomp_directory
    decomp_directory = decomp_dir
    return True

def get_duration_and_convert_to_hex(file_path):
    # Get the audio file duration in milliseconds
    audio_info = mediainfo(file_path)
    duration_ms = int(float(audio_info['duration']) * 96)

    # Convert the duration to hexadecimal
    duration_hex = hex(duration_ms)

    return duration_hex

def check_sound_input(sound_path):
    # Check if the specified file exists
    if not os.path.exists(sound_path):
        print("Invalid sound file path. Please provide a valid path.")
        return False

    # Check if the file type is valid
    if not sound_path.lower().endswith(('.aiff')):
        print("Invalid file type. Supported type: .aiff")
        return False

    return True

def update_sequences_json(bank_name, decomp_directory, hex_value_bank_name):
    sequences_json_path = os.path.join(decomp_directory, 'sound', 'sequences.json')

    with open(sequences_json_path, 'r') as json_file:
        data = json.load(json_file)

    # Check if "00_sound_player" is in the data
    if "00_sound_player" in data:
        # Check if the bank already exists in the list
        if any(bank_name in line for line in data["00_sound_player"]):
            #DEBUG#print(f"The bank {bank_name} already exists in the file.")
            pass
        else:
            # Add the new bank to the list
            data["00_sound_player"].append(f'{hex_value_bank_name}')

    # Write the updated data back to the JSON file
    with open(sequences_json_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def update_external(file_path, bank_name):
    file_path = os.path.join(file_path, 'src', 'audio', 'external.c')
    with open(file_path, 'r') as file:
        content = file.readlines()

    # Check if SOUND_BANK_{sound_bank} already exists
    sound_bank_declaration = f'SOUND_BANK_{bank_name.upper()}'
    if any(sound_bank_declaration in line for line in content):
        #DEBUG#print(f"{sound_bank_declaration} already exists in the file.")
        return

    # Find both instances of 'case SOUND_BANK_GENERAL:'
    indices = [i for i, line in enumerate(content) if 'case SOUND_BANK_GENERAL:' in line]

    for index in indices:
        # Iterate downward until no more lines with 'case' in them
        i = index + 1
        while 'case' in content[i]:
            i += 1
        # Append a new line beneath it
        content.insert(i, f'                        case {sound_bank_declaration}:\n')

    with open(file_path, 'w') as file:
        file.writelines(content)

    #DEBUG#print(f"{sound_bank_declaration} has been added to the file.")

def get_input(prompt):
    while True:
        value = input(prompt)
        # Replace spaces with underscores
        value = value.replace(' ', '_')
        # Check if the value is alphanumeric and contains underscores
        if value.replace('_', '').isalnum():
            return value
        else:
            print("Invalid input. Please enter alphanumeric characters and underscores only.")

def update_sound_player(file_path, enum_value, bank_name, sound_name, inst_pos, hex_length):
    file_path = os.path.join(file_path, 'sound', 'sequences', '00_sound_player.s')
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Step 0: Find a line beginning with 'seq_initchannels' and replace it if it's not 'seq_initchannels 0x1fff'
    for i, line in enumerate(lines):
        if line.startswith('seq_initchannels'):
            if line.strip() != 'seq_initchannels 0x1fff':
                lines[i] = 'seq_initchannels 0x1fff\n'
            break

    chan_setbank_value = enum_value + 1
    inst_pos = 0 if inst_pos is None else inst_pos

    # Step 1
    startchannel_line = f'seq_startchannel {enum_value}'
    startchannel_exists = any(startchannel_line in line for line in lines)
    channel_suffix = bank_name
    if startchannel_exists:
        startchannel_index = next(i for i, line in enumerate(lines) if startchannel_line in line)
        channel_suffix = lines[startchannel_index].split(startchannel_line)[1].strip().split('.')[1]

    # Step 2a
    if startchannel_exists:
        table_section = f'.{channel_suffix}_table'
        table_exists = any(line.strip().startswith(table_section) for line in lines)
        if table_exists:
            table_index = next(i for i, line in enumerate(lines) if line.strip().startswith(table_section))
            last_sound_ref_index = None
            for i, line in enumerate(lines[table_index + 1:], start=table_index + 1):
                if 'sound_ref' in line:
                    last_sound_ref_index = i
                elif last_sound_ref_index is not None:
                    break
            if last_sound_ref_index is not None and f'sound_ref .sound_{sound_name.lower()}\n' not in lines:
                lines.insert(last_sound_ref_index + 1, f'sound_ref .sound_{sound_name.lower()}\n')
                sound_layer_lines = [
                    f'\n.sound_{sound_name.lower()}:\n',
                    f'chan_setbank {chan_setbank_value}\n',
                    f'chan_setinstr {inst_pos}\n',
                    f'chan_setlayer 0, .layer_{sound_name.lower()}\n',
                    'chan_end\n\n',
                    f'.layer_{sound_name.lower()}:\n',
                    f'layer_note1 39, {hex_length}, 127\n',
                    'layer_end\n'
                ]
                lines[last_sound_ref_index + 2:last_sound_ref_index + 2] = sound_layer_lines

    if not startchannel_exists:
        last_startchannel_pos = max(i for i, line in enumerate(lines) if 'seq_startchannel' in line)
        new_line = f'seq_startchannel {enum_value}, .channel_{bank_name}\n'
        if not any(new_line.strip() == line.strip() for line in lines):
            lines.insert(last_startchannel_pos + 1, new_line)
        align_index = next(i for i, line in enumerate(lines) if '.align 2, 0' in line)
        new_lines = [
            f'\n.channel_{bank_name}:\n',
            'chan_largenoteson\n',
            'chan_setinstr 0\n',
            'chan_setpanmix 127\n',
            'chan_setnotepriority 14\n',
            'chan_setval 0\n',
            'chan_iowriteval 5\n',
            'chan_stereoheadseteffects 1\n',
            f'chan_setdyntable .channel_{bank_name}_table\n',
            'chan_jump .main_loop_023589\n\n',
            f'.channel_{bank_name}_table:\n',
            f'sound_ref .sound_{sound_name.lower()}\n',
            f'\n.sound_{sound_name.lower()}:\n',
            f'chan_setbank {chan_setbank_value}\n',
            f'chan_setinstr {inst_pos}\n',
            f'chan_setlayer 0, .layer_{sound_name.lower()}\n',
            'chan_end\n\n',
            f'.layer_{sound_name.lower()}:\n',
            f'layer_note1 39, {hex_length}, 127\n',
            'layer_end\n'
        ]
        lines.insert(align_index, '\n')  # Insert a newline before .align 2, 0
        lines[align_index:align_index] = new_lines  # Insert the new lines before .align 2, 0
        print(f"Sound bank '{bank_name}' successfully created.")
        print(f"Sound '{sound_name}' successfully added to bank '{bank_name}'.")

    with open(file_path, 'w') as file:
        file.writelines(lines)
        
def get_last_bank_channel(bank_path, bank_name):
    last_channel = 0x00
    sound_bank_declaration = f'SOUND_BANK_{bank_name.upper()},'
    try:
        with open(bank_path, 'r') as bank_file:
            lines = bank_file.readlines()
            for i in reversed(range(len(lines))):
                if sound_bank_declaration in lines[i]:
                    last_line = lines[i]
                    break
            if last_line:
                #DEBUG#print(f'Last line: {last_line}')  # Print the last line
                match = re.search(r', 0x([0-9A-Fa-f]+)', last_line)
                if match:
                    last_channel = int(match.group(1), 16) + 1
                    ##DEBUG#print(f'Match: {match.group(1)}, Last channel: {last_channel}')  # Print the match result and the last channel
    except (FileNotFoundError, TypeError, ValueError) as e:
        print(f'Error: {e}')  # Print the error message
        pass
    return last_channel

def get_json_file(bank_name, decomp_directory):
    # Define the directory where the JSON files are located
    json_dir = os.path.join(decomp_directory, 'sound', 'sound_banks')

    # Find files that match the format '[hex]_[bank_name].json' in the specified directory
    files = glob.glob(os.path.join(json_dir, f'*_{bank_name}.json'))
    
    # If a matching file is found, return its path
    if files:
        return files[0]
    
    # If no matching file is found, return None
    return None

def create_or_update_json_file(bank_path, sound_name, bank_name, decomp_directory):
    hex_value_bank_name = os.path.basename(bank_path).split('.')[0]
    inst_json_path = get_json_file(bank_name, decomp_directory) or os.path.join(decomp_directory, 'sound', 'sound_banks', f'{hex_value_bank_name}.json')
    update_sequences_json(bank_name, decomp_directory, hex_value_bank_name)
    #DEBUG#print(f"DEBUG: hex_value_bank_name = {hex_value_bank_name}")

    if os.path.exists(inst_json_path):
        # Update the existing JSON file
        with open(inst_json_path, 'r') as inst_json_file:
            inst_json_data = json.load(inst_json_file)

        # Check if the sound_name entry already exists
        inst_key = f'inst_{sound_name.lower()}'
        if inst_key not in inst_json_data['instruments']:
            # Add the sound_name entry
            inst_json_data['instruments'][inst_key] = {
                "release_rate": 208,
                "envelope": "envelope0",
                "sound": sound_name.lower()
            }
            inst_json_data['instrument_list'].append(inst_key)
            print(f"Sound '{sound_name}' successfully added to bank '{bank_name}'.")

            with open(inst_json_path, 'w') as inst_json_file:
                json.dump(inst_json_data, inst_json_file, indent=2)

            # Return the position of the added sound effect
            
            return len(inst_json_data['instrument_list']) - 1
        else:
            print(f"Sound '{sound_name}' already exists in bank '{bank_name}'.")

    else:
        # Create a new JSON file with the specified structure
        default_data = {
            "date": "1996-03-19",
            "sample_bank": f"sfx_{bank_name.lower()}",
            "envelopes": {
                "envelope0": [
                    [1, 32700],
                    "hang"
                ]
            },
            "instruments": {
                f'inst_{sound_name.lower()}': {
                    "release_rate": 208,
                    "envelope": "envelope0",
                    "sound": sound_name.lower()
                }
            },
            "instrument_list": [f'inst_{sound_name.lower()}']
        }

        # Save the default JSON data to the new file
        with open(inst_json_path, 'w') as inst_json_file:
            json.dump(default_data, inst_json_file, indent=2)

        # Since this is a new file, the position of the added sound effect is 0
        return 0

def get_unused_hex_value():
    sound_banks_path = os.path.join(decomp_directory, 'sound', 'sound_banks')
    used_hex_values = set()

    # Collect used hex values from existing sound bank files
    for file_path in Path(sound_banks_path).rglob('*.json'):
        hex_value = file_path.stem.split('_')[0]
        used_hex_values.add(hex_value)

    # Find an unused hex value
    for i in range(256):
        hex_value = format(i, '02X')
        if hex_value not in used_hex_values:
            return hex_value
    # Return a default hex value if no unused value is found (unlikely to happen)
    return 'FF'

def add_sound_effect(sound_path, bank_name, sound_name):
    # Convert WSL path to Windows path for raw sound file
    sound_folder = os.path.join(decomp_directory, 'sound', 'samples', f'sfx_{bank_name.lower()}')

    # Create the sfx_[sound_bank].lower() folder if it doesn't exist
    if not os.path.exists(sound_folder):
        os.makedirs(sound_folder)

    raw_sound_path = os.path.join(sound_folder, f"{sound_name}.aiff")
    shutil.copy(sound_path, raw_sound_path)
    hex_value_bank = get_unused_hex_value()
    sound_bank_path = os.path.join(decomp_directory, 'sound', 'sound_banks', f'{hex_value_bank}_{bank_name}.json')
    sounds_h_path = os.path.join(decomp_directory, 'include', 'sounds.h')

    # Step 0: Check if SOUND_BANK_[bank_name] enum entry exists and add if not
    with open(sounds_h_path, 'r+') as sounds_h_file:
        content = sounds_h_file.readlines()

    enum_declaration = f'    SOUND_BANK_{bank_name.upper()},'
    if any(enum_declaration in line for line in content):
        #DEBUG#print(f"{enum_declaration} already exists in the file.")
        pass
    else:
        # Find the index of SOUND_BANK_COUNT
        index = content.index('    SOUND_BANK_COUNT\n')

        # Insert the new enum entry before SOUND_BANK_COUNT
        content.insert(index, enum_declaration + '\n')

        # Write the modified content back to the file
        with open(sounds_h_path, 'w') as sounds_h_file:
            sounds_h_file.writelines(content)

        #DEBUG#print(f"{enum_declaration} has been added to the file.")

    # Check if SOUND_BANK_{sound_bank} exists in the enum
    enum_start = [i for i, line in enumerate(content) if 'enum SoundBank {' in line.strip()]
    enum_end = [i for i, line in enumerate(content) if 'SOUND_BANK_COUNT' in line.strip()]
    if enum_start and enum_end:
        enum_content = content[enum_start[0]:enum_end[0]]
        if not any(enum_declaration in line for line in enum_content):
            # If it doesn't exist, place the new line in the enum
            # Ensure the line above ends with a comma
            if not content[enum_end[0] - 1].strip().endswith(','):
                content[enum_end[0] - 1] = content[enum_end[0] - 1].rstrip() + ',\n'
            content.insert(enum_end[0], f'    {enum_declaration}\n')

    # Write the updated content back to sounds.h
    with open(sounds_h_path, 'w') as sounds_h_file:
        sounds_h_file.writelines(content)

    # Re-read the content of the file
    with open(sounds_h_path, 'r') as sounds_h_file:
        content = sounds_h_file.readlines()

    # Get the last channel
    last_channel = get_last_bank_channel(sounds_h_path, bank_name)

    # Find the position of '#endif'
    endif_pos = max(i for i, line in enumerate(content) if '#endif' in line)

    # Check if SOUND_BANK_{sound_bank} exists
    sound_bank_declaration = f'SOUND_BANK_{bank_name.upper()},'
    sound_name_declaration = f'SOUND_{bank_name.upper()}_{sound_name.upper()}'
    sound_arg_load = f'SOUND_ARG_LOAD(SOUND_BANK_{bank_name.upper()}, 0x{last_channel:02X}, 0xFF, SOUND_DISCRETE)'

    # Calculate the number of spaces needed for alignment
    num_spaces = 66 - len(sound_name_declaration) - len('#define ')

    # Generate the full line with padding
    define_declaration = f'#define {sound_name_declaration}{" " * num_spaces}{sound_arg_load}\n'

    # Check if a line with both '#define' and 'SOUND_BANK_{bank_name}' exists
    matching_lines = [i for i, line in enumerate(content) if '#define' in line and sound_bank_declaration in line]

    # Check if a line with '{sound_name_declaration}' exists
    matching_sound_name_lines = [i for i, line in enumerate(content) if sound_name_declaration in line]

    if not matching_sound_name_lines:
        if matching_lines:
            # If such lines exist, place the new line below the last one
            last_matching_line_pos = max(matching_lines)
            content.insert(last_matching_line_pos + 1, define_declaration)
        else:
            # If no such line exists, place the new line above '#endif'
            content.insert(endif_pos, define_declaration)
    # Write the updated content back to sounds.h
    with open(sounds_h_path, 'w') as sounds_h_file:
        sounds_h_file.writelines(content)
    # Step 4: Create or update [hex_value]_[bank_name].json
    inst_pos = create_or_update_json_file(sound_bank_path, sound_name, bank_name, decomp_directory)
    #DEBUG#print(f"The position of the instrument is {inst_pos}.")
    hex_length = get_duration_and_convert_to_hex(raw_sound_path)

    # Step 5: find the length of the enum array
    enum_start = [i for i, line in enumerate(content) if 'enum SoundBank {' in line.strip()]
    enum_end = [i for i, line in enumerate(content) if 'SOUND_BANK_COUNT' in line.strip()]
    if enum_start and enum_end:
        enum_content = content[enum_start[0]:enum_end[0]]
        # Remove any whitespace and commas from the lines
        enum_content = [line.strip().replace(',', '') for line in enum_content]
        # Print out the lines in enum_content
        for line in enum_content:
            #DEBUG#print(f"'{line}'")
            pass
        # Try to get the index of the enum_name
        try:
            enum_value = enum_content.index(f'SOUND_BANK_{bank_name.upper()}')
        except ValueError:
            enum_value = None
        #DEBUG#print(f"The value of SOUND_BANK_{bank_name.upper()} is {enum_value-1}.")
        
    update_sound_player(decomp_directory, enum_value-1, bank_name, sound_name, inst_pos, hex_length)
    update_external(decomp_directory, bank_name)
    # Step 6: Success message
    #print(f"Successfully added sound effect {sound_name} to bank {bank_name}!")

# Example usage:
decomp_input = os.path.expanduser(input("Enter the full path of your decomp directory: "))
if set_decomp_directory(decomp_input):
    sound_input = input("Enter the full path of your sound file: ")
    if check_sound_input(sound_input):
        bank_name = get_input("Enter the bank name: ")
        sound_name = get_input("Enter the sound name: ")
        add_sound_effect(sound_input, bank_name, sound_name)
