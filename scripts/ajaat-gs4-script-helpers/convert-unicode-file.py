import os
import re
import sys

def convert_unicode_special_chars_to_chars(text):
    def replace_unicode(match):
        unicode_hex = match.group(1)
        return chr(int(unicode_hex, 16))

    unicode_pattern = r"\[U\+([0-9a-fA-F]{4})\]"
    result = re.sub(unicode_pattern, replace_unicode, text)
    return result

def process_file(file_path):
    base, ext = os.path.splitext(file_path)
    output_file = f"{base}_utf8{ext}"

    try:
        with open(file_path, "r", encoding="utf-8") as f_in:
            input_text = f_in.read()
        output_text = convert_unicode_special_chars_to_chars(input_text)
        with open(output_file, "w", encoding="utf-8") as f_out:
            f_out.write(output_text)
        print(f"Conversion completed for: {output_file}")
    except FileNotFoundError:
        print(f"Error: File not found - {file_path}")
    except Exception as e:
        print(f"Error processing file {file_path}: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <input_path>")
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
