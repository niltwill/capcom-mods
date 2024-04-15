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

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python unicode-to-decimal-file.py input_file output_file")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    try:
        with open(input_file, "r", encoding="utf-8") as f_in:
            input_text = f_in.read()

        output_text = convert_to_decimal(input_text)

        with open(output_file, "w", encoding="utf-8") as f_out:
            f_out.write(output_text)

        print(f"Conversion completed: {output_file}")

    except FileNotFoundError:
        print(f"Error: File not found: {input_file}")
        sys.exit(1)
    except Exception as e:
        print(f"Error processing file {input_file}: {str(e)}")
        sys.exit(1)
