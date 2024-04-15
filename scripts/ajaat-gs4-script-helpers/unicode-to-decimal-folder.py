import os
import sys

def convert_to_decimal(text):
    result = ''
    for char in text:
        if ord(char) > 127:
            # Character is non-ASCII, convert it to decimal representation
            decimal_value = ord(char)
            result += f"\\L{decimal_value}|"
        else:
            # Character is ASCII, keep it unchanged
            result += char
    return result


def process_file(file_path):
    base, ext = os.path.splitext(file_path)
    output_file = f"{base}_dec{ext}"

    try:
        with open(file_path, "r", encoding="utf-8") as f_in:
            input_text = f_in.read()

        output_text = convert_to_decimal(input_text)

        with open(output_file, "w", encoding="utf-8") as f_out:
            f_out.write(output_text)

        print(f"Conversion completed for {output_file}")

    except FileNotFoundError:
        print(f"Error: File not found - {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error processing file {file_path}: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python unicode-to-decimal-folder.py <input_folder>")
        sys.exit(1)

    input_path = sys.argv[1]

    if os.path.isdir(input_path):
        for root, dirs, files in os.walk(input_path):
            for file in files:
                if file.endswith("_utf8.txt"):
                    file_path = os.path.join(root, file)
                    process_file(file_path)
    elif os.path.isfile(input_path) and input_path.endswith('_utf8.txt'):
        process_file(input_path)
    else:
        print("Provided path is neither a directory nor a text file.")
