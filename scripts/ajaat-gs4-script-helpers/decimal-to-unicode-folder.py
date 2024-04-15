import os
import sys
import re

def convert_decimal_to_unicode(text):
    def replace_unicode(match):
        decimal_code = int(match.group(1))
        hex_code = hex(decimal_code)[2:]
        return chr(int(hex_code, 16))

    unicode_pattern = r"\\L(\d+)\|"
    result = re.sub(unicode_pattern, replace_unicode, text)
    return result

def process_file(file_path):
    base, ext = os.path.splitext(file_path)
    output_file = f"{base}_utf8{ext}"

    try:
        with open(file_path, "r", encoding="utf-8") as f_in:
            input_text = f_in.read()

        output_text = convert_decimal_to_unicode(input_text)

        with open(output_file, "wb") as f_out:
            f_out.write(output_text.encode("utf-8", errors="ignore"))

        print(f"Conversion completed for {output_file}")

    except FileNotFoundError:
        print(f"Error: File not found - {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error processing file {file_path}: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python decimal-to-unicode-folder.py <input_folder>")
        sys.exit(1)

    input_path = sys.argv[1]

    if os.path.isdir(input_path):
        for root, dirs, files in os.walk(input_path):
            for file in files:
                if file.endswith(".txt"):
                    file_path = os.path.join(root, file)
                    process_file(file_path)
    elif os.path.isfile(input_path) and input_path.endswith('.txt'):
        process_file(input_path)
    else:
        print("Provided path is neither a directory nor a text file.")
