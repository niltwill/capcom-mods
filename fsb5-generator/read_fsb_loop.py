import sys
import struct

def read_loop_from_fsb(filename):
    with open(filename, 'rb') as f:
        # Move to offset 68 (decimal) to check if loop is enabled or disabled
        f.seek(68)
        
        # Read 4 bytes as little-endian unsigned integer
        loop_enabled_bytes = struct.unpack('<I', f.read(4))[0]
        
        # Check if the value matches the loop identifier
        loop_enabled = loop_enabled_bytes == 100663313

        print(f"Loop {'enabled' if loop_enabled else 'disabled'} in {filename}")

        if loop_enabled:
            # Seek to offset 72-75 for loop start and 76-79 for loop end
            f.seek(72)  # Loop start
            loop_start = struct.unpack('<I', f.read(4))[0]
            f.seek(76)  # Loop end
            loop_end = struct.unpack('<I', f.read(4))[0]
            
            print(f"Loop start sample: {loop_start}")
            print(f"Loop end sample: {loop_end}")
        else:
            print("No loop data present")

if __name__ == "__main__":
    # Ensure the correct number of arguments is passed
    if len(sys.argv) < 2:
        print("Usage: python read_fsb_loop.py <filename>")
        sys.exit(1)

    filename = sys.argv[1]
    read_loop_from_fsb(filename)
