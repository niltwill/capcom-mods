import argparse
import glob
import re
import os
import unicodedata

"""
WARNING: This script is experimental! It is not able to handle all GS4 script files correctly/perfectly yet.
Here are the problematic files that don't yet work, as they don't even get decoded correctly (I only tested the English script binaries):
* sc0_1_h02.user.2.en.bin
* sc1_0_000.user.2.en.bin
* sc1_3_h03.user.2.en.bin
* sc2_0_013.user.2.en.bin
* sc2_0_016.user.2.en.bin
* sc2_3_h00.user.2.en.bin
* sc3_0_00a.user.2.en.bin
* sc3_3_00c.user.2.en.bin
* sc3_3_010.user.2.en.bin
"""

def convert_gs4_script(input_file, output_file):
  """
  Args:
      input_file: Path to the input file.
      output_file: Path to the output file (will contain UTF-8 text with annotations).
  """
  with open(input_file, "rb") as f_in, open(output_file, "w") as f_out:
    data = f_in.read()
    
    # some problematic files seem to work better with some characters replaced?
    #data = data.replace(b'\x00', b'')

    try:
      # Attempt decoding with UTF-16LE first (common for GS4 scripts)
      text = data.decode("utf-16le")
    except UnicodeDecodeError:
      # If UTF-16LE fails, try common encodings for legacy files
      encodings_to_try = ["macroman", "latin-1"]
      for encoding in encodings_to_try:
        try:
          text = data.decode(encoding, errors="replace")
          break  # Exit the loop if decoding succeeds
        except UnicodeDecodeError:
          pass  # If decoding fails, continue trying other encodings
      else:
        print(f"Warning: Decoding failed with all attempted encodings. Using 'utf-8' with replacements.")
        text = data.decode("utf-8", errors="replace")

    output_lines = []
    for char in text:
      # Check if character is within the basic ASCII range without control characters (0-31, 127)
      if 32 <= ord(char) <= 126:
        output_lines.append(char)
      elif unicodedata.category(char)[0] == 'C':
        #output_lines.append("\\{:02o}".format(ord(char))) # convert control characters to octal values
        output_lines.append("[U+{:02x}]".format(ord(char))) # convert control characters to hexadecimal values
        #output_lines.append("\\{:d}".format(ord(char))) # convert control characters to decimal values
      else:
        # Convert non-ASCII character to its hex representation (without prefix)
        hex_char = hex(ord(char))[2:].zfill(2)
        output_lines.append(f"[U+{hex_char}]")

    # Write the converted text with annotations to the temporary output file
    f_out.write("".join(output_lines))



def swap_hex_in_file(annotated_file, output_file):
  """
  Args:
      annotated_file: Path to the file containing annotated text.
  """
  #pattern = r"\[U\+(?![eE])([0-9a-fA-F]{1,4})\b\]"
  pattern = r"\[U\+([0-9a-fA-F]{1,4})\b\]"

  def swap_hex(matchobj):
    """
    hex_str = matchobj.group(1)
    bytes_list = [hex_str[i:i + 2] for i in range(0, len(hex_str), 2)]
    if len(bytes_list) == 2:
        if bytes_list[0] != '0':
            bytes_list = bytes_list[::-1]
    return "".join(bytes_list)
    """
    
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


def convert_back(input_file, output_file, target_encoding="utf-16le"):
  """
  Args:
      input_file: Path to the UTF-8 decoded text file with hex annotations.
      output_file: Path to the output file after re-encoding and replacing hex.
      target_encoding: The desired encoding for the output file (e.g., "utf-16le", "macroman", "latin-1").
      
  Note: Always do a comparison check with the "compare" command
        and fix any wrong bytes manually with a hex editor.
  """
  with open(input_file, "r") as f_in, open(output_file, "wb") as f_out:
    text = f_in.read()
    
    # Define a regular expression to match hex annotations (within square brackets)
    hex_pattern = r"\[U\+([0-9a-fA-F]{3,4})\]"
    
    def replace_hex(match):
      # Extract the hex code from the match object (group 1)
      hex_code = match.group(1)
      # Convert the hex code to integer (base 16)
      char_code = int(hex_code, 16)
      # Try decoding the character code using the target encoding
      try:
        return chr(char_code)
      except UnicodeDecodeError:
        # If decoding fails, replace with a placeholder (e.g., "?")
        return "?"
    
    # Replace hex annotations with their corresponding characters
    text_without_hex = re.sub(hex_pattern, replace_hex, text)
    
    try:
      # Encode the text without hex annotations back to the target encoding
      encoded_data = text_without_hex.encode(target_encoding)
    except UnicodeEncodeError:
      print(f"Error: Encoding back to {target_encoding} failed. Consider a different encoding.")
      return

    f_out.write(encoded_data)


def compare_files(input_file, output_file):
    with open(input_file, 'rb') as f_input, open(output_file, 'rb+') as f_output:
        input_data = f_input.read()
        output_data = f_output.read()
        num = 0

        print('')
        print(f'Checking binary file differences: "{input_file}" compared with "{output_file}"...')
        
        # Check for byte differences
        for i, (input_byte, output_byte) in enumerate(zip(input_data, output_data)):
            if input_byte != output_byte:
                print('')
                print(f'Byte mismatch at position {i}.')
                print(f'Input (original) byte: {input_byte}, Output byte: {output_byte}')
                
                if(input_byte == 13):
                    print('NOTE: This byte is 13, which means it could be a newline in Windows format. Unix-based systems have 10.')
                
                # Auto-fix the misaligned byte in the output file (only works with original file as is, you should do this after you edit the file yourself)
                #f_output.seek(i)
                #f_output.write(input_byte.to_bytes(1, byteorder='little'))
                #print(f'Fixed misaligned byte at position {i} in "{output_file}".')
                
                num = num + 1

        print('')
        if num > 0:
            print(f'After you encode the file, please fix the {num} error(s) in the "{output_file}" with a hex editor.')
        else:
            print('No discrepancies were found.')


def rename_decoded_file(output_file):
  """
  Args:
      output_file: Path to the decoded file.
  """
  final_name = os.path.splitext(output_file)[0]  # Get the filename without extension
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

    # Subparser for comparison (separate subparser recommended)
    compare_parser = subparsers.add_parser("compare", help="Compare the original and modified binary")
    compare_parser.add_argument("file1", type=str, help="Path to the one (original or edited) of the binary file (mandatory)")
    compare_parser.add_argument("file2", type=str, help="Path to the other (original or edited) binary file (mandatory)")

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
            convert_gs4_script(input_file, output_file)
            swap_hex_in_file(output_file, f"{output_file}.2")

            # remove temporary file if it exists
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
            convert_back(input_file, output_file, target_encoding="utf-16le")
            print(f'Converted "{input_file}" back to binary format: "{output_file}"')

    # Compare argument
    elif args.command == "compare":
        compare_files(args.file1, args.file2)


if __name__ == "__main__":
  main()
