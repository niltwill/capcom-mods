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

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python decimal-to-unicode-file.py input_file output_file")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    try:
        with open(input_file, "r", encoding="utf-8") as f_in:
            input_text = f_in.read()

        output_text = convert_decimal_to_unicode(input_text)

        with open(output_file, "wb") as f_out:
            f_out.write(output_text.encode("utf-8", errors="ignore"))

        print(f"Conversion completed: {output_file}")

    except FileNotFoundError:
        print(f"Error: File not found: {input_file}")
        sys.exit(1)
    except Exception as e:
        print(f"Error processing file {input_file}: {str(e)}")
        sys.exit(1)
