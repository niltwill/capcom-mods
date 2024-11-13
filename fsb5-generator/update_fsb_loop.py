import sys
import struct


def update_loop_in_fsb(filename, loop_start=None, loop_end=None):
    with open(filename, 'r+b') as f:

        # Validate loop_start and loop_end
        if loop_start is None or loop_end is None:
            print(f"Error: Both loop_start and loop_end must be provided when loop is enabled for {filename}.")
            return

        # Set them here now to be able to reference later
        loop_begin = struct.pack('<I', loop_start)
        loop_fin = struct.pack('<I', loop_end)

        # Seek to offset 72-75 for loop start and 76-79 for loop end
        f.seek(72)  # Offset 72 (loop enabled/disabled already set)
        f.write(loop_begin)  # Loop start in little-endian
        f.seek(76)  # Offset 76
        f.write(loop_fin)  # Loop end in little-endian


if __name__ == "__main__":
    # Ensure the correct number of arguments is passed
    if len(sys.argv) < 4:
        print("Usage: python update_fsb_loop.py <filename> <loop_start> <loop_end>")
        sys.exit(1)

    filename = sys.argv[1]
    loop_start = int(sys.argv[2])  # Convert the loop start to integer
    loop_end = int(sys.argv[3])    # Convert the loop end to integer

    update_loop_in_fsb(filename, loop_start=loop_start, loop_end=loop_end)
