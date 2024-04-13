import sys
import re

def convert_unicode_special_chars_to_chars(text):
    def replace_unicode(match):
        # Extract the Unicode hexadecimal code from the match object (group 1)
        unicode_hex = match.group(1)
        # Convert Unicode hexadecimal code to character and return it
        return chr(int(unicode_hex, 16))

    # Define a regular expression to match Unicode representations (within square brackets)
    unicode_pattern = r"\[U\+([0-9a-fA-F]{4})\]"

    # Replace Unicode representations with their corresponding characters
    result = re.sub(unicode_pattern, replace_unicode, text)
    return result

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python unicode-to-utf8.py input_file output_file")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    try:
        # Read input from the input file
        with open(input_file, "r", encoding="utf-8") as f_in:
            input_text = f_in.read()

        # Convert Unicode representations to characters
        output_text = convert_unicode_special_chars_to_chars(input_text)

        # Write the result to the output file using UTF-8 encoding
        with open(output_file, "wb") as f_out:
            f_out.write(output_text.encode("utf-8", errors="ignore"))

        print(f"Conversion completed. Result written to {output_file}")

    except FileNotFoundError:
        print("Error: Input file not found.")
        sys.exit(1)
