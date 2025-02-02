# Script to convert the GMD (script) files to readable text files and back
# For PW:AA - Dual Destinies (GS5) and PW:AA - Spirit of Justice (GS6)

import argparse
import ast
import glob
import os
import re
import struct
import zlib


GMD_VERSIONS = {
    66049: 1,
    66306: 2,
    1: 66049,
    2: 66306
}


LANGUAGES = {
    0: "Japanese",
    1: "English",
    2: "French",
    3: "Spanish",
    4: "German",
    5: "Italian",
    "Japanese": 0,
    "English": 1,
    "French": 2,
    "Spanish": 3,
    "German": 4,
    "Italian": 5
}


def convert_gmd_version(ver):
    """
    Converts GMD version to V1 and V2 and back.
    """
    return GMD_VERSIONS.get(ver, ver)


def convert_lang(lang):
    """
    Converts the language of the GMD.
    """
    return LANGUAGES.get(lang, lang)


def read_data(file, is_le=True, fmt_types='I'):
    """Reads bytes from the file and unpacks them according to the specified format types.

    Args:
        file: The file object to read from.
        is_le: A boolean flag to indicate little-endian (True) or big-endian (False).
        fmt_types: A string representing the format types (e.g., '4sIIIIIIIII' for multiple types).

    Returns:
        A tuple with the unpacked values.
    """
    endian_type = '<' if is_le else '>'
    format_string = endian_type + fmt_types
    size = struct.calcsize(format_string)  # Calculate the byte size needed
    data = file.read(size)  # Read only the required bytes
    
    if len(data) < size:
        raise ValueError("Unexpected end of file while reading data")

    return struct.unpack(format_string, data)

def write_data(file, fmt_types='I', is_le=True, *values):
    """Packs data and writes it to a file, supporting different endianness and data types.

    Args:
        file: The file object to write to.
        fmt_types: A string representing the format types (e.g., 'I' for unsigned int, 'H' for unsigned short).
        is_le: A boolean flag to indicate little-endian (True) or big-endian (False).
        *values: The values to pack and write to the file.
    """
    endian_type = '<' if is_le else '>'
    format_string = endian_type + fmt_types
    packed_data = struct.pack(format_string, *values)
    file.write(packed_data)


def write_hash_table(file, sorted_tuples, max_size=1024, num_entries=256, is_le=True, fmt_type='I'):
    """Creates and writes a 1024-byte hash table to a file.

    Args:
        file: The file object to write to.
        sorted_tuples: A list of sorted tuples (position, value) to populate the hash table.
        max_size: The maximum size of the hash table in bytes (default is 1024).
        num_entries: The number of entries in a section (default is 256).
        is_le: The byte order flag ('True' for little-endian, 'False' for big-endian).
        fmt_type: The format type for packing (e.g., 'I' for unsigned int).
    """
    # Change endian type
    endian_type = '<' if is_le else '>'

    # Create a 1024-byte table (zero-padded)
    binary_table = bytearray(max_size)
    
    # Populate the hash table
    for position, value in sorted_tuples:
        if position < max_size:
            # Determine the section
            section_index = position // num_entries  # 0, 1, 2, or 3
            # Normalize the position within the section
            normalized_position = position - (section_index * num_entries)
            # Calculate the byte index in the table
            byte_index = (section_index * num_entries) + normalized_position
            # Write the value into the table using struct.pack_into
            struct.pack_into(endian_type + fmt_type, binary_table, byte_index, value)

    # Write the binary table to the file
    file.write(binary_table)


def calculate_hash(label_name, encoding='utf-8'):
    """
    Calculates Hash1 and Hash2 for a given label name.
    
    Parameters:
        label_name (str): The label name to hash.
        encoding (str): The encoding used for the name.

    Returns:
        tuple: Hash1 and Hash2 as unsigned 32-bit integers.
    """
    # Create the concatenated strings
    double_name = label_name + label_name
    triple_name = label_name + label_name + label_name

    # Compute CRC32
    hash1 = zlib.crc32(double_name.encode(encoding))
    hash2 = zlib.crc32(triple_name.encode(encoding))

    # Invert and mask to simulate 32-bit unsigned integers
    inverted_hash1 = ~hash1 & 0xFFFFFFFF
    inverted_hash2 = ~hash2 & 0xFFFFFFFF

    return inverted_hash1, inverted_hash2


def xor_cipher(data, version=1):
    """
    Applies XOR cipher to the input data based on version.
    """
    if version == 1:
        key1 = "fjfajfahajra;tira9tgujagjjgajgoa"
        key2 = "mva;eignhpe/dfkfjgp295jtugkpejfu"
    elif version == 2:
        key1 = "e43bcc7fcab+a6c4ed22fcd433/9d2e6cb053fa462-463f3a446b19"
        key2 = "861f1dca05a0;9ddd5261e5dcc@6b438e6c.8ba7d71c*4fd11f3af1"
    else:
        raise ValueError("Invalid version")

    # Apply XOR to data using the two keys
    result = bytearray()
    for i, byte in enumerate(data):
        result.append(byte ^ ord(key1[i % len(key1)]) ^ ord(key2[i % len(key2)]))
    return bytes(result)


def is_plaintext(data):
    """
    Checks if the data contains valid plaintext sequences starting with <E and ending with a number + >.
    """
    try:
        # Decode the data as ASCII, ignoring decoding errors
        text = data.decode('ascii', errors='ignore')
        # Match sequences starting with <E and ending with a number followed by >
        return bool(re.search(r"<E[\w\s]+[0-9]+>", text))
    except Exception:
        return False


def process_content(file, section_size):
    """
    Reads and processes content to detect if it's plaintext or encrypted.
    Tries to decrypt with XOR if content doesn't look like plaintext.
    """
    try:
        # Read the content
        ciphertext = bytearray(file.read(section_size))
        
        # Check if the content is plaintext
        if is_plaintext(ciphertext):
            return ciphertext  # Already plaintext, return as-is

        # Try decryption with XOR
        plaintext = xor_cipher(ciphertext.copy())

        # Re-check if XOR result is plaintext
        if is_plaintext(plaintext):
            return plaintext  # Successfully decrypted

        # Check if there's any content
        if len(ciphertext) == 0:
            filename = os.path.basename(file.name) if hasattr(file, 'name') else str(file)
            print(f"WARNING: Section content of '{filename}' is empty.")
            plaintext = bytearray()
            return plaintext

        # If all checks fail, return as is
        #raise ValueError("Content cannot be decrypted: invalid format or key mismatch.")
        return ciphertext

    except Exception as e:
        print(f"Error processing content: {e}")
        return None


def parse_gmd_file(file_path, is_le=True, label_sep='<SEC_END>', hash_table_size=1024, encoding='utf-8'):
    """
    This processes the GMD file (first part of decoding).
    """
    try:
        with open(file_path, 'rb') as file:
            # Validate file size
            file.seek(0, 2)  # Move to the end of the file
            file_size = file.tell()
            file.seek(0)  # Reset to the start

            if file_size < 40:
                raise ValueError(f"File too small: {file_size} bytes, expected at least 40 bytes")

            # Read and parse the header in one step
            magic, version, language, unknown1, unknown2, label_count, section_count, label_size, section_size, name_size = read_data(file, is_le=is_le, fmt_types='4sIIIIIIIII')

            # Check for magic word
            if magic != b'GMD\x00':
                raise ValueError("Invalid GMD file: Magic word mismatch")

            # Read the filename
            filename = file.read(name_size).decode(encoding).rstrip('\x00')

            # Skip the null terminator after the filename
            file.seek(1, 1)

            # Convert version to be 1 or 2
            version = convert_gmd_version(version)

            # Convert the language
            language = convert_lang(language)

            label_offsets = []

            if version == 1:  # GMD V1 (Dual Destinies)
                # Parse the offsets for the label pointer table
                for _ in range(label_count):
                    # First offset is the label number
                    offset = read_data(file, is_le=is_le, fmt_types='I')[0]
                    label_offsets.append(offset)
                    # Second offset is the pointer value
                    offset = read_data(file, is_le=is_le, fmt_types='I')[0]
                    label_offsets.append(offset)
            elif version == 2:  # GMD V2 (Spirit of Justice)
                label_ref1 = []
                label_ref2 = []

                # Parse the offsets for the label table
                for _ in range(label_count):
                    # First offset is the label number
                    offset = read_data(file, is_le=is_le, fmt_types='I')[0]
                    label_offsets.append(offset)
                    # Second offset is the hash1
                    offset = read_data(file, is_le=is_le, fmt_types='I')[0]
                    label_offsets.append(offset)
                    # Third offset is the hash2
                    offset = read_data(file, is_le=is_le, fmt_types='I')[0]
                    label_offsets.append(offset)
                    # Skip 8 bytes to get to the next entry
                    #file.seek(8, 1)
                    # Label start position index (within all the labels)
                    offset = read_data(file, is_le=is_le, fmt_types='I')[0]
                    label_ref1.append(offset)
                    # Unknown label reference (maybe to another label index in the hash table?)
                    offset = read_data(file, is_le=is_le, fmt_types='I')[0]
                    label_ref2.append(offset)

                # Store the hash table's positions
                label_map = {
                    "label_data": [],  # To store tuples of (position, value)
                    "ff_marker": []    # To store tuple of FF FF FF FF
                }

                # Read the hash map in its entirety
                hash_table = file.read(hash_table_size)

                # Iterate through the block, 4 bytes at a time
                for i in range(0, hash_table_size, 4):
                    chunk = hash_table[i:i + 4]

                    # Check if it's FF FF FF FF
                    if chunk == b'\xFF\xFF\xFF\xFF':
                        label_value = int.from_bytes(chunk, byteorder='little', signed=False)
                        label_map["ff_marker"].append((i, label_value))

                    # Collect label index positions
                    if chunk != b'\x00\x00\x00\x00' and chunk != b'\xFF\xFF\xFF\xFF':  # Skip zero entries and the FF FF FF FF marker
                        label_value = int.from_bytes(chunk, byteorder='little', signed=False)
                        label_map["label_data"].append((i, label_value))
            else:
                raise ValueError("Unsupported GMD version")

            # Parse the label names
            label_names = []
            for i in range(label_count):
                # Check if the offset for this label is 0x0
                if label_offsets[2 * i + 1] == 0x0:  # Pointer value at even indices
                    label_names.append("NO_LABEL")
                else:
                    label = b""
                    while True:
                        char = file.read(1)
                        if char == b'\x00':  # Null terminator indicates the end of the label
                            break
                        label += char
                    label_names.append(label.decode(encoding))  # Decode the label to a string


            # Process the main content
            processed_content = process_content(file, section_size)
            if processed_content is not None:
                plaintext = processed_content
            else:
                print("Failed to process the main content")
                return

            # Convert plaintext to a string and replace newlines
            decrypted_text = plaintext.decode(encoding)
            decrypted_text = decrypted_text.replace('\x00', label_sep)  # Replace '\x00' with an end marker
            decrypted_text = decrypted_text.replace('\r\n', '\n')  # Handle newlines properly

            # Split the decrypted content by the end markers, but keep them in the content
            content_parts = decrypted_text.split(label_sep)

            # Ensure the number of end separators matches the number of the section count
            if section_count != len(content_parts)-1:
                print(f"Warning: The number of section count ({section_count}) does not match the number of end separators ({len(content_parts)-1})")

            # Prepare a dictionary to hold label-content pairs
            section_content = {}

            # Output the labels and their corresponding content
            for idx, (label, content) in enumerate(zip(label_names, content_parts)):
                # Re-attach the end marker at the end of each content part except the last one
                #content_with_marker = content + (label_sep if idx < len(content_parts) - 1 else '')
                content_with_marker = content + label_sep

                # Add the label and its content as a pair to the dictionary
                section_content[f"{idx}:{label}"] = content_with_marker.strip()

            # Base dictionary that is common for both versions
            base_data = {
                "magic": magic.decode(encoding),
                "version": version,
                "language": language,
                "unknown1": unknown1,
                "unknown2": unknown2,
                "label_count": label_count,
                "section_count": section_count,
                "label_size": label_size,
                "section_size": section_size,
                "name_size": name_size,
                "filename": filename,
                "label_offsets": label_offsets,
            }

            # For version 1, return the base dictionary directly
            if version == 1:
                base_data["label_names"] = label_names
                base_data["section_content"] = section_content
                return base_data

            # For version 2, add the extra fields
            elif version == 2:
                # Reset label map if there is no label
                if label_count == 0:
                    label_map.clear()

                base_data["label_ref1"] = label_ref1
                base_data["label_ref2"] = label_ref2
                base_data["label_map"] = label_map
                base_data["label_names"] = label_names
                base_data["section_content"] = section_content

                return base_data

    except Exception as e:
        print(f"Error parsing GMD file: {e}")
        return None


def write_gmd_data_to_file(gmd_data, output_file, encoding='utf-8'):
    """
    Writes the parsed GMD data to a readable text file.
    """
    try:
        with open(output_file, 'w', encoding=encoding) as file:
            filename = gmd_data['filename']
            version = gmd_data['version']
            language = gmd_data['language']
            label_count = gmd_data['label_count']
            section_count = gmd_data['section_count']
            section_content = gmd_data['section_content']
            label_offsets = gmd_data['label_offsets']
            label_names = gmd_data['label_names']

            # Prepare content to write
            content = []

            # Write the filename, magic word + version, and language in one go
            content.append(f"{{{filename}}}\n")
            content.append(f"{{GMD V{version}}}\n")
            content.append(f"{{{language}}}\n")
            content.append(f"{{{label_count}}}\n")
            content.append(f"{{{section_count}}}\n")

            if version == 2:
                # As this is an unknown label reference, it is needed
                label_ref2 = gmd_data['label_ref2']
                if label_ref2:
                    content.append(f"{{{label_ref2}}}\n")

                # This is needed to repopulate the content of the hash table later
                label_map = gmd_data['label_map']
                if label_map:
                    content.append(f"{{{label_map['label_data']}}}\n")
                    content.append(f"{{{label_map['ff_marker']}}}\n")

            content.append("\n")  # Separate the header

            # Filter offsets based on version
            if version == 1:
                filtered_offsets = [label_offsets[i] for i in range(1, len(label_offsets), 2)]
            elif version == 2:
                filtered_offsets = [label_offsets[i] for i in range(len(label_offsets)) if i % 3 != 0]

            # Write the label offsets and label names in one go
            for idx, label in enumerate(label_names):
                # Access content with the formatted key
                section_data = section_content.get(f"{idx}:{label}", '')

                if version == 1:
                    label_offset = filtered_offsets[idx] if idx < len(filtered_offsets) else 'N/A'
                elif version == 2:
                    hash1 = filtered_offsets[2 * idx] if 2 * idx < len(filtered_offsets) else 'N/A'
                    hash2 = filtered_offsets[2 * idx + 1] if 2 * idx + 1 < len(filtered_offsets) else 'N/A'
                    label_offset = f"{hash1}+{hash2}"

                content.append(
                    f"{{{idx}:{label_offset}:{label}}}\n{section_data}\n\n"
                    if idx < (label_count - 1) 
                    else f"{{{idx}:{label_offset}:{label}}}\n{section_data}\n"
                )

            # Write everything in one go
            file.writelines(content)

    except Exception as e:
        print(f"Error writing to file: {e}")


def read_decoded_text_file(input_file, encoding='utf-8'):
    """
    Read the exported GMD file and extract key fields along with labels and their content.
    """
    gmd_data = {
        "labels": []  # To store label data (index, offset, name, content)
    }
    try:
        with open(input_file, 'r', encoding=encoding) as file:
            lines = file.readlines()

        # Parse header fields
        gmd_data['filename'] = lines[0].strip().strip('{}')  # First line: filename
        gmd_data['version'] = int(lines[1].strip().strip('{}').replace('GMD V', ''))  # Second line: version
        gmd_data['language'] = lines[2].strip().strip('{}')  # Third line: language
        gmd_data['label_count'] = int(lines[3].strip().strip('{}'))  # Fourth line: label count
        gmd_data['section_count'] = int(lines[4].strip().strip('{}'))  # Fifth line: section count
        ver = gmd_data['version']

        header_num = 5
        if ver == 2:
            if len(lines) > 5:
                gmd_data['label_ref2'] = (lines[5].strip().strip('{}'))  # Fifth line: label ref2 (unknown)
                header_num += 1
            if len(lines) > 6:
                gmd_data['label_map'] = (lines[6].strip().strip('{}'))  # Sixth line: label map (labels)
                header_num += 1
            if len(lines) > 7:
                gmd_data['label_map_marker'] = (lines[7].strip().strip('{}'))  # Seventh line: ff marker
                header_num += 1

        # Process labels and content
        current_label = None
        current_content = []
        for line in lines[header_num:]:  # Skip header
            line = line.rstrip("\n")

            if line.startswith("{") and ":" in line:  # Start of a new label
                # Save the previous label
                if current_label:
                    current_label['content'] = "\n".join(current_content).rstrip("\n")
                    gmd_data['labels'].append(current_label)
                    current_content = []

                # Parse label: {index:offset:name}
                parts = line.strip("{}").split(":")
                if ver == 1:
                    current_label = {
                        "index": int(parts[0]),
                        "offset": int(parts[1]),
                        "name": parts[2],
                        "content": None
                    }
                elif ver == 2:
                    offset_parts = parts[1].split('+')
                    current_label = {
                        "index": int(parts[0]),
                        "offset": {"hash1": int(offset_parts[0]), "hash2": int(offset_parts[1])},
                        "name": parts[2],
                        "content": None
                    }

            elif current_label:  # Append line to current label's content
                current_content.append(line)

        # Handle the last label
        if current_label:
            current_label['content'] = "\n".join(current_content).rstrip("\n")
            gmd_data['labels'].append(current_label)

        return gmd_data

    except Exception as e:
        print(f"Error reading GMD file: {e}")
        return None


def replace_fullwidth_with_placeholder(text):
    """
    Convert full width characters to 3 placeholder chars.
    (This is needed to get accurate length in some labels.)
    """
    result = []
    for char in text:
        # Check if the character is fullwidth
        if '\uFF00' <= char <= '\uFFEF':  # Fullwidth character range
            # Replace fullwidth character with 3 chars
            result.append('###')
        else:
            result.append(char)  # Keep the original character if it's not fullwidth

    return ''.join(result)


def write_gmd_file(output_file, gmd_data, is_le=True, xor_encoding=False, label_sep='<SEC_END>', MAX_HASH_SIZE=1024, encoding='utf-8'):
    """
    Write the processed data back to a GMD file as binary.
    """
    try:
        with open(output_file, 'wb') as file:
            # Get the GMD magic word
            magic = f"GMD"
            magic_bin = magic.encode(encoding) + b'\0'

            # Get the version
            version = gmd_data['version']
            ver = version
            version = convert_gmd_version(version)

            # Get the language
            language = gmd_data['language']
            language = convert_lang(language)

            # Get the label count
            label_count = gmd_data['label_count']

            # Get the section count
            section_count = gmd_data['section_count']

            # Easier version reference
            ver = convert_gmd_version(version)

            # Process the data with the labels
            if ver == 1:
                offsets = []
            elif ver == 2:
                offsets = {}

            label_names = []
            section_size = 0
            content_bytes = bytearray()

            for label in gmd_data['labels']:
                index = label['index']
                offset = label['offset']
                name = label['name']

                if ver == 1:
                    offsets.append(index)
                    offsets.append(offset)
                # Check hashes and make new ones, if necessary
                # (if labels have been edited)
                elif ver == 2:
                    # Process each offset
                    try:
                        # Access hash1 and hash2 directly
                        hash1_orig = offset['hash1']
                        hash2_orig = offset['hash2']

                        # Calculate the CRC32 hashes
                        hash1, hash2 = calculate_hash(name, encoding)

                        # If original hash1 is not the same, use new one
                        if hash1_orig != hash1:
                            hash1_orig = hash1

                        # If original hash2 is not the same, use new one
                        if hash2_orig != hash2:
                            hash2_orig = hash2

                        offsets[index] = [hash1_orig, hash2_orig]

                    except KeyError as e:
                        print(f"Key not found: {e}")

                label_names.append(name)
                label_content = label['content']

                # Replace the end markers with a zero in the content and fix line endings
                content_with_hex = label_content.replace(label_sep, '\x00').replace("\n", "\r\n")

                if(xor_encoding):                    
                    # Convert the string to a bytearray for XOR cipher
                    byte_data = bytearray(content_with_hex, encoding)
                    cur_content = bytes(byte_data)

                    # Save the content for later
                    content_bytes += cur_content

                    # Add to the section size
                    section_size += len(cur_content)
                else:
                    cur_content = content_with_hex.encode(encoding)

                    # Save the content for later
                    content_bytes += cur_content

                    # Add to the section size
                    section_size += len(cur_content)

            # Make sure the label count is sufficient
            if label_count == len(label_names):
                # Get all label strings for reference
                label_strings = '\0'.join(label_names) + '\0'

                # Replace fullwidth characters with placeholders to get correct length
                # Otherwise we will lose out on 2 extra characters for each fullwidth char
                length_strings = replace_fullwidth_with_placeholder(label_strings)

                # Get final length
                label_size = len(length_strings)

                #label_lengths = [len(label)+1 for label in label_names]
                #label_size = sum(label_lengths)
                if label_count < 1:
                    label_size = 0
            else:
                print("The label count does not match to the actual label names!")
                return

            # Get the filename
            filename = gmd_data['filename']
            filename_len = len(filename)
            filename_bin = filename.encode(encoding) + b'\0'

            # Prepare the header data to be written in one go
            header_data = [
                magic_bin, version, language, 0x00, 0x00,
                label_count, section_count, label_size, section_size,
                filename_len
            ]

            # Correct the format string to match the structure of `header_data`
            fmt_string = '4sIIIIIIIII'

            # Write the header GMD data in one go (except the filename, as its length can change)
            write_data(file, fmt_string, is_le, *header_data)
            file.write(filename_bin)

            # Write the offsets with their indices
            if ver == 1:
                offsets_to_write = offsets  # Prepare the list of offsets to be written
                fmt_string = 'I' * len(offsets_to_write)
                write_data(file, fmt_string, is_le, *offsets_to_write)
            elif ver == 2:
                # Get the unknown label references
                label_ref2 = gmd_data['label_ref2']
                label_list = ast.literal_eval(label_ref2)

                # Initialize the starting position
                current_position = 0

                # Initialize list to use these values later
                label_pos = {}

                # Loop through the label names and calculate the starting position
                for n in label_names:
                    # Calculate the CRC32 hashes
                    hash1, hash2 = calculate_hash(n, encoding)
                    # Write the position after the hashes
                    label_pos[current_position] = {hash1, hash2}

                    # Replace fullwidth characters with placeholders to get correct length
                    # Otherwise we will lose out on 2 extra characters for each fullwidth char
                    length_strings = replace_fullwidth_with_placeholder(n)

                    # Add the length of the label and the null terminator to the position
                    current_position += len(length_strings) + 1  # +1 for the null terminator

                # Iterate through label_pos and append keys to offsets without reordering
                for key2, value_list2 in label_pos.items():
                    for value in value_list2:
                        # Check each value in offsets
                        for key1, value_list1 in offsets.items():
                            if value in value_list1:
                                # Avoid duplicates and ensure key2 is added at the end
                                if key2 not in value_list1:
                                    value_list1.append(key2)

                # Add elements from the label list to the offsets
                if len(label_list) == len(offsets):
                    for key, value in offsets.items():
                        value.append(label_list[key])

                # Write the offsets from the dictionary
                offsets_to_write = []
                for key, values in offsets.items():
                    offsets_to_write.append(key)  # Append the key
                    offsets_to_write.extend(values)  # Append all values for this key

                # Now write all the offsets in one go
                fmt_string = 'I' * len(offsets_to_write)
                write_data(file, fmt_string, is_le, *offsets_to_write)

                # Now to reconstruct the label map/hash table (1024 bytes here)
                label_map = [gmd_data['label_map']]
                label_map_marker = [gmd_data['label_map_marker']]

                # Step 1: Combine the data
                combined_map = label_map + label_map_marker

                # Step 2: Order the data by the first value in each tuple
                parsed_data = [ast.literal_eval(entry) for entry in combined_map]
                all_tuples = [item for sublist in parsed_data for item in sublist]
                sorted_tuples = sorted(all_tuples, key=lambda x: x[0])

                # Step 3. Write the hash table
                write_hash_table(file, sorted_tuples, max_size=MAX_HASH_SIZE, num_entries=MAX_HASH_SIZE // 4, is_le=is_le, fmt_type='I')

            # Write the label names with null termination
            for n in label_names:
                file.write(n.encode(encoding) + b'\0')

            # Encode in one go
            if(xor_encoding):
                encoded_data = xor_cipher(content_bytes)
                file.write(encoded_data)
            else:
                file.write(content_bytes)

    except Exception as e:
        print(f"Error writing binary GMD file: {e}")


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Convert PW:AA - Dual Destinies (GS5) and PW:AA - Spirit of Justice (GS6) GMD scripts")
    subparsers = parser.add_subparsers(title="Main Commands", dest="command")

    # Subparser for info
    info_parser = subparsers.add_parser("i", help="Get the raw, unprocessed file data of the GMD script")
    info_parser.add_argument("input_file", type=str, help="Path to the input binary file or wildcard pattern (mandatory)")
    info_parser.add_argument("output_file", type=str, nargs='?', default=None, help="Path to the output text file (optional)")
    info_parser.add_argument("--be", action="store_true", help="Use big-endian instead of little-endian (optional)")
    info_parser.add_argument("--out", action="store_true", help="Do not print to the console, write to an output file instead (optional)")

    # Subparser for decoding
    decode_parser = subparsers.add_parser("d", help="Decode GMD scripts to readable format")
    decode_parser.add_argument("input_file", type=str, help="Path to the input binary file or wildcard pattern (mandatory)")
    decode_parser.add_argument("output_file", type=str, nargs='?', default=None, help="Path to the output text file (optional)")
    decode_parser.add_argument("--be", action="store_true", help="Use big-endian instead of little-endian (optional)")

    # Subparser for encoding
    encode_parser = subparsers.add_parser("e", help="Encode readable GS4/GS5 text scripts back to GMD")
    encode_parser.add_argument("input_file", type=str, help="Path to the input text file or wildcard pattern (mandatory)")
    encode_parser.add_argument("output_file", type=str, nargs='?', default=None, help="Path to the output GMD file (optional)")
    encode_parser.add_argument("--be", action="store_true", help="Use big-endian instead of little-endian (optional)")
    encode_parser.add_argument("--xor", action="store_true", help="Re-encrypt with XOR, recommended for DD [Dual Destinies] (optional)")

    args = parser.parse_args()

    # Validate argument usage based on chosen command
    if args.command == "i" or args.command == "d" or args.command == "e":
        if not args.input_file:
            parser.error(f"{args.command} requires input_file argument")
    else:
        parser.error("Invalid command. Choose either: i, d or e")

    # Define default values
    encoding='utf-8'
    label_sep='<SEC_END>'
    MAX_HASH_SIZE=1024

    # Info argument
    if args.command == "i":  # Info
        is_le = not args.be
        input_files = glob.glob(args.input_file)
        for input_file in input_files:
            output_file = args.output_file if args.output_file else f"{os.path.splitext(input_file)[0]}-raw.txt"
            gmd_data = parse_gmd_file(input_file, is_le=is_le, label_sep=label_sep, hash_table_size=MAX_HASH_SIZE, encoding=encoding)
            if args.out:
                if gmd_data:
                    with open(output_file, "w", encoding=encoding) as outfile:
                        for key, value in gmd_data.items():
                            if key == "content":
                                outfile.write(f"{key}: {len(value)} bytes\n")
                            else:
                                outfile.write(f"{key}: {value}\n")
                        print(f'Converted "{input_file}" to raw readable format: "{output_file}"')
            else:
                if gmd_data:
                    for key, value in gmd_data.items():
                        if key == "content":
                            print(f"{key}: {len(value)} bytes")
                        else:
                            print(f"{key}: {value}")
    elif args.command == "d":  # Decode
        is_le = not args.be
        input_files = glob.glob(args.input_file)
        for input_file in input_files:
            output_file = args.output_file if args.output_file else f"{os.path.splitext(input_file)[0]}.txt"
            gmd_data = parse_gmd_file(input_file, is_le=is_le, label_sep=label_sep, hash_table_size=MAX_HASH_SIZE, encoding=encoding)
            if gmd_data:
                write_gmd_data_to_file(gmd_data, output_file, encoding=encoding)
                print(f'Converted "{input_file}" to readable format: "{output_file}"')
    elif args.command == "e":  # Encode
        is_le = not args.be
        xor_encoding = args.xor
        input_files = glob.glob(args.input_file)
        for input_file in input_files:
            output_file = args.output_file if args.output_file else f"{os.path.splitext(input_file)[0]}.gmd"
            gmd_data = read_decoded_text_file(input_file, encoding=encoding)
            if gmd_data:
                write_gmd_file(output_file, gmd_data, is_le=is_le, xor_encoding=xor_encoding, label_sep=label_sep, MAX_HASH_SIZE=MAX_HASH_SIZE, encoding=encoding)
                print(f'Converted "{input_file}" back to GMD format: "{output_file}"')


# Entry point for the script
if __name__ == "__main__":
    main()
