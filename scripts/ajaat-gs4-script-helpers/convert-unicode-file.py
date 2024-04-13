import sys

def convert_to_unicode_special_chars(text):
    result = ''
    for char in text:
        if ord(char) > 127:
            # Character is non-ASCII, convert it to Unicode representation
            unicode_hex = hex(ord(char))[2:].upper()  # Get hexadecimal Unicode code point
            result += f"[U+{unicode_hex.zfill(4)}]"
        else:
            # Character is ASCII, keep it unchanged
            result += char
    return result

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python convert-unicode-file.py input_file output_file")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    try:
        with open(input_file, "r", encoding="utf-8") as f_in:
            input_text = f_in.read()

        output_text = convert_to_unicode_special_chars(input_text)

        with open(output_file, "w", encoding="utf-8") as f_out:
            f_out.write(output_text)

        print(f"Conversion completed. Result written to {output_file}")

    except FileNotFoundError:
        print("Error: Input file not found.")
        sys.exit(1)
