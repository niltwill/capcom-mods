import argparse
import glob
import re
import os
import unicodedata


"""
Script to convert AJ:AA Trilogy's GS4 (Apollo Justice) script binary files

* You can simply convert every file in the same directory by using the command:
ajaat-gs4-script.py decode *.bin

* To convert back to binary:
ajaat-gs4-script.py encode *.txt

Different languages have different problematic files which need some byte correction.
For this, you can use the command:
ajaat-gs4-script.py compare --fix [original].bin [name].encoded.bin

Make sure to put the original binary file first, then your modified one!
This should only fix those few different bytes and ignore the rest of your modifications.

To do it all in one go, simply edit and run the batch script: "ajaat-gs4-script_comparefix.bat" (which should only fix those files that have this byte issue).
Replace "en" with the language you need in that file. It assumes that every script binary file is in the same directory and that you did not rename the encoded files.
"""


def decode_gs4_script(input_file, output_file):
  with open(input_file, "rb") as f_in, open(output_file, "w") as f_out:
    data = f_in.read()

    try:
      # Attempt decoding with UTF-16LE (utf-16le) - alternative would be MacRoman (macroman)
      text = data.decode("utf-16le", errors="replace")
    except UnicodeDecodeError:
      print("Warning: Decoding failed with the UTF-16LE encoding.")
      return 1

    output_lines = []
    for char in text:
      # Check if character is within the basic ASCII range without control characters (0-31, 127)
      if 32 <= ord(char) <= 126:
        output_lines.append(char)
      elif unicodedata.category(char)[0] == 'C':
        #output_lines.append("\\x{:02o}|".format(ord(char))) # convert control characters to octal values
        #output_lines.append("\\x{:02x}|".format(ord(char))) # convert control characters to hexadecimal values
        output_lines.append("\\{:d}|".format(ord(char))) # convert control characters to decimal values
      else:
        # Convert non-ASCII character to its hex representation (with Unicode codepoint ID)
        hex_char = hex(ord(char))[2:].zfill(2)
        output_lines.append(f"[U+{hex_char}]")

    # Write the converted text with annotations to the temporary output file
    f_out.write("".join(output_lines))


def swap_hex_in_file(annotated_file, output_file):
  #pattern = r"\[U\+(?![eE])([0-9a-fA-F]{1,4})\b\]"
  pattern = r"\[U\+([0-9a-fA-F]{1,4})\b\]"

  def swap_hex(matchobj):   
    hex_str = matchobj.group(1)
    # Convert hexadecimal string to Unicode character
    unicode_char = chr(int(hex_str, 16))
    # Convert Unicode character to its hexadecimal representation with leading zeros
    unicode_hex = format(ord(unicode_char), '04X')
    # Split the hexadecimal representation into individual characters with [U+...] format
    return f'[U+{unicode_hex}]'

  with open(annotated_file, "r") as f_in, open(output_file, "w") as f_out:
    annotated_text = f_in.read()
    swapped_text = re.sub(pattern, swap_hex, annotated_text)
    f_out.write(swapped_text)


def encode_gs4_script(input_file, output_file, target_encoding="utf-16le"):
  with open(input_file, "r") as f_in, open(output_file, "wb") as f_out:
    text = f_in.read()
    
    # Define a regular expression to match control characters
    #controlchar_pattern = r"\\x([0-9a-fA-F]{2,4})\|"
    controlchar_pattern = r"\\(\d+)\|"
    
    def replace_decimal(match):
      decimal_value = int(match.group(1))
      hex_code = format(decimal_value, '04X')
      return f"[U+{hex_code}]"
    
    # Define a regular expression to match hex annotations (within square brackets)
    hex_pattern = r"\[U\+([0-9a-fA-F]{4})\]"
    
    def replace_hex(match):
      # Extract the hex code from the match object (group 1)
      hex_code = match.group(1)
      char_code = int(hex_code, 16)
      
      try:
          return chr(char_code)
      except UnicodeEncodeError:
          # If decoding fails, replace with a placeholder (e.g., "?")
          return "?"

    # Replace annotations with their corresponding characters
    text_without_dec = re.sub(controlchar_pattern, replace_decimal, text)
    text_without_hex = re.sub(hex_pattern, replace_hex, text_without_dec)
    
    try:
      # Encode the text without hex annotations back to the target encoding
      encoded_data = text_without_hex.encode(target_encoding)
    except UnicodeEncodeError:
      print(f"Error: Encoding back to {target_encoding} failed. Consider a different encoding.")
      return

    f_out.write(encoded_data)


def compare_files(input_file, output_file, fix=False):
    with open(input_file, 'rb') as f_input, open(output_file, 'rb+') as f_output:
        input_data = f_input.read()
        output_data = f_output.read()
        num = 0
        prior_byte = 0

        print('')
        print(f'Checking binary file differences: "{input_file}" compared with "{output_file}"...')

        # Check for byte differences
        for i, (input_byte, output_byte) in enumerate(zip(input_data, output_data)):
            if input_byte != output_byte:
                if not fix:
                    print('')
                    print(f'Byte mismatch at position {i}.')
                    print(f'Input (original) byte: {input_byte}, Output byte: {output_byte}')

                if fix:
                    try:
                        # Replace 253 followed by 255 with corresponding bytes from input file
                        if output_byte == 253 and i + 1 < len(output_data) and output_data[i + 1] == 255:
                            f_output.seek(i)
                            f_output.write(input_byte.to_bytes(1, byteorder='little'))
                            f_output.write(input_data[i + 1:i + 2])
                            prior_byte = 0  # Reset prior_byte since both bytes are replaced
                            print(f'Fixed bytes at decimal offset {i}-{i+1} in "{output_file}"')
                        else:
                            prior_byte = output_byte  # Update prior_byte if not part of 253-255 pair
                    except (IOError, OSError) as e:
                        print(f"Error fixing byte at position {i}: {e}")

                num += 1

        if num > 0 and not fix:
            print('')
            print(f'After you encode the file, please fix the {num} error(s) in the "{output_file}" with a hex editor.')
        elif not fix:
            print('')
            print('No discrepancies were found.')


def rename_decoded_file(output_file):
  final_name = os.path.splitext(output_file)[0]
  os.rename(output_file, final_name)


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Convert GS4 scripts")
    subparsers = parser.add_subparsers(title="Main Commands", dest="command")

    # Subparser for decoding
    decode_parser = subparsers.add_parser("decode", help="Decode GS4 script to human-readable format")
    decode_parser.add_argument("input_file", type=str, help="Path to the input binary file or wildcard pattern (mandatory)")
    decode_parser.add_argument("output_file", type=str, nargs='?', default=None, help="Path to the output text file (optional)")

    # Subparser for encoding
    encode_parser = subparsers.add_parser("encode", help="Encode human-readable GS4 script back to binary")
    encode_parser.add_argument("input_file", type=str, help="Path to the input text file or wildcard pattern (mandatory)")
    encode_parser.add_argument("output_file", type=str, nargs='?', default=None, help="Path to the output binary file (optional)")

    # Subparser for comparison
    compare_parser = subparsers.add_parser("compare", help="Compare the original and modified binary (only do this with the original and unmodified binary)")
    compare_parser.add_argument("file1", type=str, help="Path to the one (original or edited) of the binary file (mandatory)")
    compare_parser.add_argument("file2", type=str, help="Path to the other (original or edited) binary file (mandatory)")
    compare_parser.add_argument("--fix", action="store_true", help="Attempt to fix some MacRoman(?) byte differences, always use the original file first (optional)")

    args = parser.parse_args()

    # Validate argument usage based on chosen command
    if args.command == "decode" or args.command == "encode":
        if not args.input_file:
            parser.error(f"{args.command} requires input_file argument")
    elif args.command == "compare":
        if not args.file1 or not args.file2:
            parser.error("compare requires both file1 and file2 arguments")
    else:
        parser.error("Invalid command. Choose either decode, encode or compare")

    # Decode argument
    if args.command == "decode":
        input_files = glob.glob(args.input_file)
        for input_file in input_files:
            output_file = args.output_file if args.output_file else f"{os.path.splitext(input_file)[0]}.txt"
            decode_gs4_script(input_file, output_file)
            swap_hex_in_file(output_file, f"{output_file}.2") # make hex characters 4 bytes

            # remove temporary output file if it exists
            try:
                os.remove(output_file)
            except FileNotFoundError:
                pass

            # rename the final file to the original output file
            rename_decoded_file(f"{output_file}.2")
            print(f'Converted "{input_file}" to human-readable format: "{output_file}"')

    # Encode argument
    elif args.command == "encode":
        input_files = glob.glob(args.input_file)
        for input_file in input_files:
            output_file = args.output_file if args.output_file else f"{os.path.splitext(input_file)[0]}.encoded.bin"
            encode_gs4_script(input_file, output_file)
            print(f'Converted "{input_file}" back to binary format: "{output_file}"')

    # Compare argument
    elif args.command == "compare":
        compare_files(args.file1, args.file2, fix=args.fix)

if __name__ == "__main__":
  main()
