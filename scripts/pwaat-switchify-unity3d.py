import argparse
import os
import sys


def find_second_occurrence(data: bytes, pattern: bytes) -> int:
    """Return the start index of the second occurrence of pattern, or -1."""
    first = data.find(pattern)
    if first == -1:
        return -1
    second = data.find(pattern, first + len(pattern))
    return second


def make_it_switch_compatible(file_path: str) -> bool:
    """
    Finds the second '2017' in the file, skips 11 bytes from its start,
    and replaces 0x13 (PC) with 0x26 (Switch) at that position.
    """
    try:
        with open(file_path, 'r+b') as f:
            data = f.read()

            pattern = b'2017'
            second_pos = find_second_occurrence(data, pattern)

            if second_pos == -1:
                print(f"Error: Could not find second '{pattern.decode()}' in file.")
                return False

            # 4 bytes for "2017" + 7 bytes for ".4.8f1\x00" = 11 bytes offset
            target_pos = second_pos + 11

            if target_pos >= len(data):
                print(f"Error: File too short (need at least {target_pos + 1} bytes).")
                return False

            format_byte = data[target_pos]

            if format_byte == 0x26:
                print(f"Already Switch version (0x26 at 0x{target_pos:04x}).")
                return False

            if format_byte != 0x13:
                print(f"Skipped: unexpected byte 0x{format_byte:02x} at 0x{target_pos:04x} (expected 0x13).")
                return False

            # Patch in-place
            f.seek(target_pos)
            f.write(b'\x26')
            print(f"Patched at offset {target_pos} (0x{target_pos:04x}).")
            return True

    except FileNotFoundError:
        print(f"Error: File not found.")
    except PermissionError:
        print(f"Error: Permission denied.")
    except OSError as e:
        print(f"Error: {e}")

    return False


def process_list_file(list_path: str) -> None:
    try:
        with open(list_path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                print(f"Processing... {line}")
                make_it_switch_compatible(line)
    except OSError as e:
        print(f"Error reading list file '{list_path}': {e}")
        sys.exit(1)


def process_directory(dir_path: str) -> None:
    patched = 0
    skipped = 0

    for root, dirs, files in os.walk(dir_path):
        for filename in files:
            file_path = os.path.join(root, filename)
            print(f"Processing... {file_path}")
            if make_it_switch_compatible(file_path):
                patched += 1
            else:
                skipped += 1

    print(f"\nDone. Patched: {patched}, Skipped/Failed: {skipped}")


def main():
    parser = argparse.ArgumentParser(description="PWAAT Switchify - Converts PC unity3d files to Switch format.")
    parser.add_argument('target', nargs='?', default='list.txt', help='Path to a list file OR a directory to scan recursively (default: list.txt)')
    args = parser.parse_args()

    if not os.path.exists(args.target):
        print(f"Error: '{args.target}' not found.")
        sys.exit(1)

    if os.path.isdir(args.target):
        process_directory(args.target)
    else:
        process_list_file(args.target)


if __name__ == "__main__":
    main()
