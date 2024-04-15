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
    if len(sys.argv) != 2:
        print("Usage: python convert-unicode-text.py 'input_text'")
        sys.exit(1)

    input_text = sys.argv[1]
    output_text = convert_to_unicode_special_chars(input_text)
    print(output_text)
