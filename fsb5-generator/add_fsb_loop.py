import sys
import struct

# FSB header: 896 bytes
loop_initial = struct.pack('<I', 100663313)
#crc32 = struct.pack('<I', 1832501054)

def update_loop_in_fsb(filename, loop_start=None, loop_end=None):
    with open(filename, 'r+b') as f:

        # Validate loop_start and loop_end
        if loop_start is None or loop_end is None:
            print(f"Error: Both loop_start and loop_end must be provided when loop is enabled for {filename}.")
            return

        # Set them here now to be able to reference later
        loop_begin = struct.pack('<I', loop_start)
        loop_fin = struct.pack('<I', loop_end)

        # Read all data from the file
        file_data = f.read()

        # Search the first 896 bytes for a sequence of 12 empty bytes (0x00)
        empty_seq = b'\x00' * 12
        header_area = file_data[:896]
        remove_offset = header_area.find(empty_seq)

        # If a sequence of 12 empty bytes is found, remove it
        if remove_offset != -1:
            file_data = file_data[:remove_offset] + file_data[remove_offset + 12:]

        # Insert new data at offset 68
        new_offset = 68
        file_data = file_data[:new_offset] + loop_initial + file_data[new_offset:]

        # Insert `loop_start` at offset 72
        new_offset = 72
        file_data = file_data[:new_offset] + loop_begin + file_data[new_offset:]

        # Insert `loop_fin` at offset 76
        new_offset = 76
        file_data = file_data[:new_offset] + loop_fin + file_data[new_offset:]

        # Replace the 4 bytes at offset 84, crc32 value (doing so ruins the audio completely, avoid)
        #replacement_offset = 84
        #file_data = file_data[:replacement_offset] + crc32 + file_data[replacement_offset + 4:]

        # Add 12 to the 4-byte integer at offset 20 (actually, no need to change audio data length)
        #offset_20 = 20
        #original_value = struct.unpack('<I', file_data[offset_20:offset_20 + 4])[0]
        #modified_value = original_value + 12
        #file_data = file_data[:offset_20] + struct.pack('<I', modified_value) + file_data[offset_20 + 4:]

        # Go back to the beginning of the file and write the modified data
        f.seek(0)
        f.write(file_data)
        f.truncate()  # Truncate the file in case the new data is shorter


if __name__ == "__main__":
    # Ensure the correct number of arguments is passed
    if len(sys.argv) < 4:
        print("Usage: python add_fsb_loop.py <filename> <loop_start> <loop_end>")
        sys.exit(1)

    filename = sys.argv[1]
    loop_start = int(sys.argv[2])  # Convert the loop start to integer
    loop_end = int(sys.argv[3])    # Convert the loop end to integer

    update_loop_in_fsb(filename, loop_start=loop_start, loop_end=loop_end)
