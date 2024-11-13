import sys
import struct

# FSB header: 896 bytes (836?)

def remove_loop_in_fsb(filename):
    with open(filename, 'r+b') as f:

        # Read all data from the file
        file_data = f.read()

        # Remove 12 bytes at offset 68 (loop)
        remove_offset = 68
        file_data = file_data[:remove_offset] + file_data[remove_offset+12:]

        # Reinsert the removed 12 bytes at offset 879 (end of header)
        insert_offset = 879
        zero_bytes = b'\x00' * 12
        file_data = file_data[:insert_offset] + zero_bytes + file_data[insert_offset:]

        # Go back to the beginning of the file and write the modified data
        f.seek(0)
        f.write(file_data)
        f.truncate()  # Truncate the file in case the new data is shorter


if __name__ == "__main__":
    # Ensure the correct number of arguments is passed
    if len(sys.argv) < 2:
        print("Usage: python remove_fsb_loop.py <filename>")
        sys.exit(1)

    filename = sys.argv[1]

    remove_loop_in_fsb(filename)
