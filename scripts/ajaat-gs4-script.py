# -*- coding: utf-8 -*-

import argparse
import glob
import re
import os
import sys
import unicodedata


"""
Script to convert AJ:AA Trilogy's GS4 (Apollo Justice) script binary files

---

***IMPORTANT: For the mappings to work, also download this file and place it in the same directory to the script:
https://raw.githubusercontent.com/niltwill/capcom-mods/main/scripts/ajaat-gs4-script-mappings.txt

The "L" prefix before a decimal number means "Language", indicating that it's possibly a language character. This letter can be ignored.
It is only an indicator letter to convert only these characters into unicode when using a different helper script.

---

* You can simply convert every file in the same directory by using the command:
ajaat-gs4-script.py decode *.bin

* To convert back to binary:
ajaat-gs4-script.py encode *.txt

Different languages have some different problematic files which need some byte corrections.
For this, you can use the command:
ajaat-gs4-script.py compare --fix [original].bin [name].encoded.bin

Make sure to put the original binary file first, then your modified one!
This should only fix those few different bytes and ignore the rest of your modifications.

To do it all in one go, simply edit and run the batch script: "ajaat-gs4-script_comparefix.bat" (which should only fix those files that have this byte issue):
https://raw.githubusercontent.com/niltwill/capcom-mods/main/scripts/ajaat-gs4-script_comparefix.bat

Replace "en" with the language you need in that file. It assumes that every script binary file is in the same directory and that you did not rename the encoded files.
"""


def load_mappings(filename, separator):
    # Get the directory path of the script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the full path to the mappings file
    mappings_file_path = os.path.join(script_dir, filename)

    replacement_mapping = {}
    try:
        with open(mappings_file_path, 'r') as file:
            for line in file:
                # Skip empty lines and lines starting with '#'
                if line.strip() == '' or line.strip().startswith('#'):
                    continue

                # Split the line by '=', but only once to separate the numeric sequence from the rest of the line
                numeric_sequence, remaining_part = line.split('=', 1)

                # Split the remaining part by '|'
                parts = remaining_part.split('|')
                if len(parts) != 2:
                    # Skip lines that do not contain exactly one '|' sign after the '='
                    continue

                replacement_string, argument_info = parts
                
                # Add back the separator to the string
                replacement_string += separator

                # Split the argument_info string to extract the argument number and range
                argument_range = tuple(map(int, argument_info.strip().split('-')))

                replacement_mapping[numeric_sequence.strip()] = (replacement_string.strip(), argument_range)
    except FileNotFoundError:
        print(f"Error: Mapping file '{filename}' not found.")
        print("Download it from this URL and place it into the script's directory:")
        print("https://raw.githubusercontent.com/niltwill/capcom-mods/main/scripts/ajaat-gs4-script-mappings.txt")
        sys.exit(1)

    return replacement_mapping


# Function to convert the decimal ASCII to symbol representation
def convert_decimal_to_ascii(decimal_value):
    if 32 <= decimal_value <= 126:
        ascii_symbol = chr(decimal_value)
        return ascii_symbol
    else:
        return decimal_value


# Function to convert ASCII symbol to decimal representation
def convert_ascii_to_decimal(char):
    ascii_symbol = char
    if 32 <= ord(ascii_symbol) <= 126:
        return ord(ascii_symbol)
    else:
        return ascii_symbol


def get_first_numeric_values(string, num_parameters):
    # Use rfind to locate the last pipe delimiter
    last_pipe_index = string.rfind("|")

    # Split the string at pipes up to the last delimiter (inclusive)
    if last_pipe_index != -1:
        parts = string.split("|", last_pipe_index + 1)  # Include last delimiter
    else:
        parts = [string]  # No pipes found, return the entire string

    # Check if enough values are present
    if len(parts) >= num_parameters:
        return parts[:num_parameters]
    else:
        return None


def find_and_add_delimiters(string):
    # Find all occurrences of "\L[numeric]" or digits not followed by a pipe
    matches = re.findall(r"\\L(\d+)(?!\|)", string)

    # Add delimiters after each match
    for match in matches:
        string = string.replace(match, match + "|")

    return string


def replace_all_occurrences_backwards(string, expression, replacement, count=None):
    if count is None:
        count = string.count(expression) # If count is not specified, replace all occurrences

    while count > 0:
        last_index = string.rfind(expression)
        if last_index != -1:
            before_last = string[:last_index]
            after_last = string[last_index + len(expression):]
            string = before_last + replacement + after_last
            count -= 1
        else:
            break
    return string


# Function to convert certain ASCII symbols to their decimals (32-126)
def convert_ascii_symbols(replacement_string, ascii_part, num_parameters):
    # Remove the "|" delimiter
    command_name = replacement_string[:-1]

    # Do not process these commands with this method
    # (they don't process properly)
    cmd_support = {"\swoosh", "\person_face"}
    if command_name in cmd_support:
        return replacement_string + ascii_part

    # Really barebones command range support here
    # Cause I didn't want to make this super complicated
    # As there are not that many commands with a range
    current_cmds = ascii_part.count('\\', 0)
    base_param = num_parameters - current_cmds
    
    if command_name == "\music":
        if base_param == 3:
            num_parameters = 3

    if command_name == "\cmd051":
        if base_param == 1:
            num_parameters = 1
        elif base_param == 2:
            num_parameters = 2
        elif base_param == 3:
            num_parameters = 3
        elif base_param == 4:
            num_parameters = 4

    if command_name == "\cmd066":
        if base_param == 1:
            num_parameters = 1
        elif base_param == 2:
            num_parameters = 2

    if command_name == "\cmd073":
        if base_param == 3:
            num_parameters = 3

    if command_name == "\cmd095":
        if base_param == 3:
            num_parameters = 3

    if command_name == "\cmd104":
        if base_param == 4:
            num_parameters = 4

    if command_name == "\codeblock":
        if base_param == 2:
            num_parameters = 2

    # Match only the "\L[numeric]" values (
    regex_numonly = r"\\L?(\d+)\|?"
    
    # Used to build the string to return
    final_string = ""
    
    # Define full command
    full_string = replacement_string + ascii_part
    full_cmd_count = full_string.count('\\', 0)
    
    # If only the command name exists, but we have parameters defined, gracefully return
    #if full_cmd_count == 1 and num_parameters > 0:
    #    return replacement_string + ascii_part

    if current_cmds < num_parameters:
        # Find all matches with their starting and ending positions
        matches = [match.span() for match in re.finditer(regex_numonly, ascii_part)]
        characters = []

        i = 0  # Index for the string
        for start, end in matches:
            # Add characters before the match
            characters.extend(ascii_part[i:start])
            i = end  # Update index to skip matched characters

        # Add remaining characters and unmatched parts
        characters.extend(ascii_part[i:])
        converted_text = ascii_part

        # Used for the second check of command parameters
        cmd_values = num_parameters
        fixed_cmds = ""
        x = ""

        for c in characters:
            while (num_parameters - len(matches)) != 0:
                
                # Convert "1\1" and the other numbers like that manually
                # (Due to the regex)
                if "1\\1" in ascii_part:
                    converted = convert_ascii_to_decimal(str(1))
                    x = "\\" + str(converted) + "|\\1|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                elif "2\\2" in ascii_part:
                    converted = convert_ascii_to_decimal(str(2))
                    x = "\\" + str(converted) + "|\\2|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                elif "3\\3" in ascii_part:
                    converted = convert_ascii_to_decimal(str(3))
                    x = "\\" + str(converted) + "|\\3|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                elif "4\\4" in ascii_part:
                    converted = convert_ascii_to_decimal(str(4))
                    x = "\\" + str(converted) + "|\\4|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                elif "5\\5" in ascii_part:
                    converted = convert_ascii_to_decimal(str(5))
                    x = "\\" + str(converted) + "|\\5|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                elif "6\\6" in ascii_part:
                    converted = convert_ascii_to_decimal(str(6))
                    x = "\\" + str(converted) + "|\\6|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                elif "7\\7" in ascii_part:
                    converted = convert_ascii_to_decimal(str(7))
                    x = "\\" + str(converted) + "|\\7|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                elif "8\\8" in ascii_part:
                    converted = convert_ascii_to_decimal(str(8))
                    x = "\\" + str(converted) + "|\\8|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                elif "9\\9" in ascii_part:
                    converted = convert_ascii_to_decimal(str(9))
                    x = "\\" + str(converted) + "|\\9|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                elif ascii_part == "\\1|1":
                    converted = convert_ascii_to_decimal(str(1))
                    x = "\\1|" + "\\" + str(converted) + "|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                elif ascii_part == "\\2|2":
                    converted = convert_ascii_to_decimal(str(2))
                    x = "\\2|" + "\\" + str(converted) + "|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                elif ascii_part == "\\3|3":
                    converted = convert_ascii_to_decimal(str(3))
                    x = "\\3|" + "\\" + str(converted) + "|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                elif ascii_part == "\\4|4":
                    converted = convert_ascii_to_decimal(str(4))
                    x = "\\4|" + "\\" + str(converted) + "|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                elif ascii_part == "\\5|5":
                    converted = convert_ascii_to_decimal(str(5))
                    x = "\\5|" + "\\" + str(converted) + "|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                elif ascii_part == "\\6|6":
                    converted = convert_ascii_to_decimal(str(6))
                    x = "\\6|" + "\\" + str(converted) + "|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                elif ascii_part == "\\7|7":
                    converted = convert_ascii_to_decimal(str(7))
                    x = "\\7|" + "\\" + str(converted) + "|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                elif ascii_part == "\\8|8":
                    converted = convert_ascii_to_decimal(str(8))
                    x = "\\8|" + "\\" + str(converted) + "|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                elif ascii_part == "\\9|9":
                    converted = convert_ascii_to_decimal(str(9))
                    x = "\\9|" + "\\" + str(converted) + "|"
                    final_string += replacement_string + x
                    num_parameters -= 1
                else:
                    converted = convert_ascii_to_decimal(str(c))

                    # Fix replacing the wrong (first) element if duplicate numbers exist
                    # - Only for those commands where it causes issues -
                    if command_name == "\cmd024":
                        match_number_repetitions = r"(?<!\\)(\d)(?:\W|\||\d)*\1"
                        match_nums = re.search(match_number_repetitions, converted_text)
                        if match_nums:
                            value = match_nums.group()
                            if "|" in value and "|\\" not in value: # Make sure to only do this if the repetition is in a different part, not same value
                                x = replace_all_occurrences_backwards(str(converted_text), str(c), "\\" + str(converted) + "|", count=1)
                                # Boldly assuming it has all the parameters already (should be fine, except if not)
                                return replacement_string + x

                    x = converted_text.replace(str(c), "\\" + str(converted) + "|", 1)
                    
                    # Fix double backslashes
                    if "\\124|\\124|" in x:
                        temp = x
                        temp = temp.replace("\\124|\\124|", "|\\124|")
                        x = temp

                    # Final string to use if command parameters are enough
                    final_string = replacement_string + x
                    num_parameters -= 1

                    # Check if we have enough command parameters
                    # (As sometimes, the \L[numeric] values may add some extra false numbers
                    values = get_first_numeric_values(x, num_parameters)
                    if values:
                      remaining_string = x[x.rfind("|") + 1:]
                      for v in values:
                        if cmd_values == num_parameters:
                            break
                        if v.startswith("\\"):
                            cmd_values -= 1
                            fixed_cmds += v + "|"
                        else:
                            for char in v:
                                if cmd_values != num_parameters:
                                    converted = convert_ascii_to_decimal(str(char))
                                    fixed_cmds += "\\" + str(converted) + "|"
                                    cmd_values -= 1
                                    num_parameters -= 1
                                else:
                                    fixed_cmds += char
                            if remaining_string:
                                fixed_cmds += remaining_string
                            # Add \L[numeric] value delimiters back
                            fixed_delimiters = find_and_add_delimiters(fixed_cmds)
                            final_string += replacement_string + fixed_delimiters

    # Fix the "|" mistakes
    if "\\124||" in final_string:
        temp = final_string
        temp = temp.replace("\\124||", "|\\124|")
        final_string = temp

    if final_string.endswith("||"):
        temp = final_string
        temp = temp.replace("||", "|\\124|")
        final_string = temp

    # Return the final result 
    return final_string


def count_backslashes_with_numbers(text, num_parameters):
    count = 0
    pattern = r"\\L?(\d+)"
    matches = re.findall(pattern, text)
    for match in matches:
        if count < num_parameters:
            count += 1
    return count


def replace_single_backslashes(text, num_parameters):
    result = ""
    pattern = r"\\L?(\d+)"
    matches = re.finditer(pattern, text)
    ignore_indices = set()
    for match in matches:
        if num_parameters != 0:
            # Get the starting index (excluding captured digits)
            start_index = match.start(1) - 1  # Backslash index (excluding digits)
            # Check for optional "L"
            if text[start_index - 1] == "L" and text[start_index - 2] == "\\":
                start_index -= 2
            # Adjust for "L" and preceding backslash
            if text[start_index] == "L":
                start_index -= 1
            num_parameters -= 1
        ignore_indices.add(start_index)

    filtered_matches = re.finditer(r"\\", text)
    for match in filtered_matches:
        if match.start() not in ignore_indices:
          start = match.start()
          end = match.end()

          # Build the new string with replacement
          result = text[:match.start()] + "\\92|" + text[match.end():]

          # Fix double "\\"
          if "\\92||" in result:
            result = text[:match.start()] + "\\92|\\92" + text[match.end():]

          return result


def ascii_convert_command(ascii_part, num_parameters):
    cmd_count = ascii_part.count('\\', 0)
    iteration = num_parameters - cmd_count

    # Exceptional cases that require manual handling
    #if ascii_part == "\\0|0":
    #    return "\\0|\\48"
    if ascii_part == r'\0|\\0|':
        return r'\0|\92|\0|'

    # If there are a ton of values after command, return as is
    if iteration < 0:
        return ascii_part
        
    # Create a copy so that it doesn't overwrite current value
    ascii_part_copy = ascii_part

    split_cmd = ascii_part_copy.split('|')
    secondProcess = False
    for part in split_cmd:
        if not part.startswith('\\') and not part.endswith('|') and len(part) == 1:
            x = ascii_part_copy.replace(part, "\\" + str(convert_ascii_to_decimal(part)) + "|", 1)
            ascii_part_copy = x
        elif not part.startswith('\\'):
            for p in part:
                while p in ascii_part_copy and iteration != 0:
                    x = ascii_part_copy.replace(p, "\\" + str(convert_ascii_to_decimal(p)) + "|", 1)
                    if "\\\\" in x:
                        iteration = 0
                        secondProcess = True
                        break
                    ascii_part_copy = x
                    iteration -= 1

    if "\\\\" in ascii_part_copy or secondProcess:
        # Assuming it did not replace properly, try a different method
        ascii_part_copy2 = ascii_part
        cmd_count = ascii_part.count('\\', 0)
        iteration = num_parameters - cmd_count

        # Replace sole numeric values with temporary markers
        # (I know there can be better ways, but this is the most simple)
        ap0 = ascii_part_copy2.replace('\\0', '\\Q')
        ap1 = ap0.replace('\\1', '\\W')
        ap2 = ap1.replace('\\2', '\\E')
        ap3 = ap2.replace('\\3', '\\R')
        ap4 = ap3.replace('\\4', '\\T')
        ap5 = ap4.replace('\\5', '\\Z')
        ap6 = ap5.replace('\\6', '\\U')
        ap7 = ap6.replace('\\7', '\\I')
        ap8 = ap7.replace('\\8', '\\O')
        ap9 = ap8.replace('\\9', '\\P')

        split_cmd = ap9.split('|')
        new_parts = []
        new_part = []
        remaining_string = []
        removed_char = 0
        for part in split_cmd:
            if not part.startswith('\\'):
                # This method doesn't actually support "b\0" (char before \num value)
                if "\\" in part:
                    return ascii_part_copy2
                remaining_string.append(part)
                while iteration != 0:
                    for p in part:
                        if iteration != 0:
                            decimal_value = convert_ascii_to_decimal(p)
                            new_part.append("\\" + str(decimal_value) + "|")
                            iteration -= 1
                            removed_char += 1
                    remaining_string = [i[removed_char:] for i in remaining_string]
                    new_parts.append("".join(new_part))
            else:
                ap0 = part.replace('\\P', '\\9')
                ap1 = ap0.replace('\\O', '\\8')
                ap2 = ap1.replace('\\I', '\\7')
                ap3 = ap2.replace('\\U', '\\6')
                ap4 = ap3.replace('\\Z', '\\5')
                ap5 = ap4.replace('\\T', '\\4')
                ap6 = ap5.replace('\\R', '\\3')
                ap7 = ap6.replace('\\E', '\\2')
                ap8 = ap7.replace('\\W', '\\1')
                final_string = ap8.replace('\\Q', '\\0')
                new_parts.append(final_string + "|")

        joinedlist = new_parts + remaining_string

        # Also convert any "\" ASCII symbols now before returning it
        # num_parameters + 1 --> because this now also includes the command name
        count_cmd_backslashes = count_backslashes_with_numbers("".join(joinedlist), num_parameters + 1)
        if count_cmd_backslashes < num_parameters:
            if "\\\\" in ascii_part_copy:
                fix_doubleslashes = ascii_part_copy.replace('\\\\', '\\\\92|')
                ascii_part_copy = fix_doubleslashes
            backslash_fix = replace_single_backslashes(ascii_part_copy, (num_parameters + 1) - count_cmd_backslashes)
            return backslash_fix
        else:
            return "".join(joinedlist)

    # Also convert any "\" ASCII symbols now before returning it
    # num_parameters + 1 --> because this now also includes the command name
    count_cmd_backslashes = count_backslashes_with_numbers(ascii_part_copy, num_parameters + 1)
    if count_cmd_backslashes < num_parameters:
        if "\\\\" in ascii_part_copy:
            fix_doubleslashes = ascii_part_copy.replace('\\\\', '\\\\92|')
            ascii_part_copy = fix_doubleslashes
        backslash_fix = replace_single_backslashes(ascii_part_copy, (num_parameters + 1) - count_cmd_backslashes)
        return backslash_fix
    else:
        return ascii_part_copy


# Function to replace ASCII symbols before numerical values
# This only converts the chars before the values
def ascii_convert_prevalues(ascii_part, num):
    # These are not needed for this, but doesn't hurt to keep them either
    cmd_count = ascii_part.count('\\', 0)
    cmd_left = num - cmd_count

    # Return language-specific exceptions here (add your own ones if needed)
    # -de-
    if ascii_part == r'\6|\0|\0|\0|h\L228|tte er so stehen m\L252|ssen,':
        return r'\6|\0|\0|\0|h\L228|tte er so stehen m\L252|ssen,'

    # Convert two or triple pipes before splitting
    if "|||" in ascii_part:
        temp = ascii_part
        temp = temp.replace('|||', '|\\124|\\124|')
        ascii_part = temp
    elif "||" in ascii_part:
        temp = ascii_part
        temp = temp.replace('||', '|\\124|')
        ascii_part = temp

    converted_chars = []
    remaining_string = []
    #converted_num = cmd_count
    converted_num = 0
    split_pattern = r".{2,}(\d+)" # Match only the values before numbers
    string_split = ascii_part.split('|')
    firstOnly = False
    if converted_num <= 4: # Maximum parameter number for all the commands involved
        for text in string_split:
            match = re.search(split_pattern, text)
            if match:
                string = match.group()
                length = len(string)
                firstChar = False
                secondChar = False
                if length >= 3:
                    if not string[0] == "\\" and not firstOnly:
                        # Convert first char
                        decimal_value = convert_ascii_to_decimal(string[0])
                        converted_chars.append("\\" + str(decimal_value) + "|")
                        converted_num += 1
                        firstChar = True
                        if not string[1] == "\\":
                            # Convert second char
                            decimal_value = convert_ascii_to_decimal(string[1])
                            converted_chars.append("\\" + str(decimal_value) + "|")
                            converted_num += 1
                            secondChar = True
                            firstOnly = True
                    elif string[0] == " " and firstOnly:
                        # Don't convert spaces at this point
                        converted_chars.append(" " + string[1:] + "|")
                    else:
                        converted_chars.append("\\" + string[1:] + "|")
                    if firstChar and not secondChar:
                        converted_chars.append(string[1:] + "|")
                    elif firstChar and secondChar:
                        converted_chars.append(string[2:] + "|")
            else:
                if text.startswith("\\"):
                    if len(text) >= 1:
                        if text[1].isnumeric():
                            converted_chars.append(text + "|")
                        elif text[1] == "L":
                            converted_chars.append(text + "|")
                        else:
                           converted_chars.append(text) 
                    else:
                        converted_chars.append(text + "|")
                else:
                    # text at the end (not getting handled in this function)
                    remaining_string.append(text)

        return "".join(converted_chars + remaining_string)


# Convert the last characters only
def ascii_convert_aftervalues(ascii_part, num):
    #cmd_count = ascii_part.count('\\', 0)
    #cmd_left = num - cmd_count

    # Do not proceed if there is a pipe at the end (that means it's a command end)
    if ascii_part.endswith('|'):
        return ascii_part

    # Return language-specific exceptions here (add your own ones if needed)
    # -ko-
    if ascii_part == r'\5|\84|\36|\L47560|\L52840|\L45236| \L46300|\L47084|\L45212| \L46319|\L54633|\L45768|\L45796|.':
        return ascii_part

    # Convert two or triple pipes before splitting
    # (should be redundant as this has happened before earlier, but anyway)
    if "|||" in ascii_part:
        temp = ascii_part
        temp = temp.replace('|||', '|\\124|\\124|')
        ascii_part = temp
    elif "||" in ascii_part:
        temp = ascii_part
        temp = temp.replace('||', '|\\124|')
        ascii_part = temp

    converted_chars = []
    starting_string = []
    space_text = []
    non_matches = 0
    split_pattern = r"\\L?(\d+).*" # values after numbers
    string_split = ascii_part.split('|')
    for text in string_split:
        # If language text has space, do not convert that
        if " \L" in text:
            space_text.append(text + "|")

        match = re.search(split_pattern, text)
        if not match:
            # Text at the end
            length = len(text)
            if length == 1:
                # Always convert these
                decimal_value = convert_ascii_to_decimal(text)
                converted_chars.append("\\" + str(decimal_value) + "|")
                non_matches += 1
            elif length == 2:
                # Always convert these
                for char in text:
                    decimal_value = convert_ascii_to_decimal(char)
                    converted_chars.append("\\" + str(decimal_value) + "|")
                    non_matches += 1
            elif length > 2:
                # Convert only first char here too (should be enough for these commands)
                for char in text:
                    if non_matches < 1:
                        decimal_value = convert_ascii_to_decimal(char)
                        converted_chars.append("\\" + str(decimal_value) + "|")
                        non_matches += 1
                    else:
                        converted_chars.append(char)
            else:
                # If we'd ever reach this point, and don't know what to do, put it back as is
                converted_chars.append(text)
        else:
            # Matching numbers come first
            string = match.group()
            starting_string.append(string + "|")

    # Add original spaces back to strings with \L numbers, if they contain them
    for i, space_element in enumerate(space_text):
        for j, orig_element in enumerate(starting_string):
            if space_element.strip() == orig_element:
                starting_string[j] = space_element
                break

    return "".join(starting_string + converted_chars)


def is_language_related(char):
    # Get the general category of the character
    category = unicodedata.category(char)
    # Check if the character belongs to a script commonly used in languages
    if category.startswith('L') is not None:
        return True
    else:
        return False


def process_replacement(replacement_string, line, start_index, ascii_part, num_parameters):
    modified_line = None
    converted_cmd = None

    # Replace some problematic commands
    if replacement_string in ["\\swoosh|", "\\person|", "\\person_face|", "\\music|", "\\bganim|",
    "\\cmd024|", "\\cmd095|"]:
        converted_cmd = ascii_convert_command(ascii_part, num_parameters)

    # Replace chars before values (that remained)
    if replacement_string in ["\\cmd055|", "\\cmd073|", "\\cmd095|", "\\cmd104|"]:
        converted_cmd = ascii_convert_prevalues(ascii_part, num_parameters)

    # Apply the conversion if any
    if converted_cmd is not None:
        modified_line = replacement_string + converted_cmd
        ascii_part = converted_cmd  # Update ascii_part with converted_cmd

    # Replace chars after values
    if replacement_string in ["\\cmd051|", "\\cmd055|", "\\cmd066|", "\\cmd073|", "\\cmd095|"]:
        converted_cmd = ascii_convert_aftervalues(ascii_part, num_parameters)

    # Apply the conversion if any
    if converted_cmd is not None:
        modified_line = replacement_string + converted_cmd
        ascii_part = converted_cmd  # Update ascii_part with converted_cmd

    return modified_line, ascii_part


def decode_gs4_script(input_file, output_file, mappings_file):
  with open(input_file, "rb") as f_in, open(output_file, "w") as f_out:
    data = f_in.read()

    try:
      # Attempt decoding with UTF-16LE (utf-16le) - alternative would be ISO-8859-1 (latin-1)
      text = data.decode("utf-16le", errors="replace")
    except UnicodeDecodeError:
      print("Warning: Decoding failed with the UTF-16LE encoding.")
      sys.exit(1)

    output_lines = []
    for char in text:
      # Check if character is within the basic ASCII range without control characters (0-31, 127)
      if 32 <= ord(char) <= 126:
        output_lines.append(char)
      elif unicodedata.category(char)[0] == 'C':
        #output_lines.append("\\x{:02o}||".format(ord(char))) # convert control characters to octal values
        #output_lines.append("\\x{:02x}||".format(ord(char))) # convert control characters to hexadecimal values
        string = "{:d}||".format(ord(char))
        if (string.startswith("5") or string.startswith("6")) and len(string) >= 6:
            output_lines.append("\n\\{:d}|".format(ord(char))) # add newline for the command control characters
        else:
            output_lines.append("\\{:d}|".format(ord(char))) # convert control characters to decimal values
      else:
        # Convert non-ASCII characters to their decimal representations
        # Otherwise use hex (with the Unicode code point)
        if is_language_related(char):
            try:
                dec_char = ord(char)
                output_lines.append(f"\\L{dec_char}|")
            except:
                hex_char = hex(ord(char))[2:].zfill(2)
                output_lines.append(f"[U+{hex_char}]")
        else:
            try:
                dec_char = ord(char)
                output_lines.append(f"\\{dec_char}|")
            except:
                hex_char = hex(ord(char))[2:].zfill(2)
                output_lines.append(f"[U+{hex_char}]")

    # Load mappings from the mappings file
    replacement_mapping = load_mappings(mappings_file, '|')

    # Apply replacements
    for numeric_sequence, (replacement_string, argument_range) in replacement_mapping.items():
        output_string = "".join(output_lines)
        output_string = output_string.replace(numeric_sequence, replacement_string)
        if argument_range:
            lines = output_string.split("\n")
            for i, line in enumerate(lines):
                if i == len(lines) - 1 and not line.strip():
                    break
                start_index = 0
                while True:
                    start_index = line.find(replacement_string, start_index)
                    if start_index == -1:
                        break
                    ascii_part = (line[start_index + len(replacement_string):])
                    line = replacement_string + ascii_part
                    num_parameters = argument_range[0]

                    # Process the line with ASCII symbol conversion (through two methods)
                    converted_line = convert_ascii_symbols(replacement_string, ascii_part, num_parameters)
                    if converted_line:
                        line = converted_line
                        ascii_part = (converted_line[start_index + len(replacement_string):])

                    # Additional commands to convert from ASCII symbols to decimals
                    modified_line, ascii_part = process_replacement(replacement_string, line, start_index, ascii_part, num_parameters)
                    if modified_line is not None:
                        line = modified_line
                        ascii_part = (modified_line[start_index + len(replacement_string):])

                    start_index += len(replacement_string)
                lines[i] = line
            output_string = '\n'.join(lines)
        output_lines = output_string.splitlines(keepends=True)

    # Write the converted text with annotations to the output file
    f_out.write("".join(output_lines))


# The first line is problematic due to different positions of certain chars in various files,
# so it's not really handled (as of yet)
def fix_first_line(annotated_file, output_file):
  with open(annotated_file, "r") as f_in, open(output_file, "w") as f_out:
    try:
        # Handle the first line, remove the "L" chars and convert ASCII symbols here too
        first_line = f_in.readline()

        # Split the line in case of extra newlines
        lines = first_line.splitlines()

        # Remove the "L" from first line, as that's needed for the regex to work
        modified_line = re.sub(r'\\L(\d+)', r'\\\1', lines[0])

        # Manually catch and convert any "\\" sign (regex is not going to find this)
        if "\\\\" in modified_line:
            changed_line = modified_line
            changed_line = changed_line.replace('\\\\', '\\92|\\')
            modified_line = changed_line

        # Match two patterns with regex
        #pattern_before = r'(?<=\|)([^|\\]*)'  # Pattern to capture text before \number
        pattern_before = r'(?<=\|)([^\\\\]*)'
        pattern_after = r'\\(\d+)([^|]*)'  # Pattern to capture \number and text after it

        # Find all matches for pattern_before in the string
        matches_before = re.finditer(pattern_before, modified_line)

        # Find all matches for pattern_after in the string
        matches_after = re.finditer(pattern_after, modified_line)

        # Empty string to hold the values
        final_line = ""

        # Manually add the very first byte if the second byte starts with "\"
        # (As the regex fails to catch this one)
        second_byte = modified_line[1]
        if second_byte == '\\':
            first_byte = modified_line[0]
            replaced_char = convert_ascii_to_decimal(first_byte)
            final_line += "\\" + str(replaced_char) + "|"

        # Extract captured groups from matches
        for match_before, match_after in zip(matches_before, matches_after):
            text_before = match_before.group(1)  # Capture the text before \number
            # Capture the numeric value (\number)
            number = match_after.group(1)
            # Capture the text after \number
            text_after = match_after.group(2)

            if number:
                final_line += "\\" + str(number) + "|"
            if text_before:
                for char in text_before:
                    replaced_char = convert_ascii_to_decimal(char)
                    final_line += "\\" + str(replaced_char) + "|"
            if text_after:
                for char in text_after:
                    replaced_char = convert_ascii_to_decimal(char)
                    final_line += "\\" + str(replaced_char) + "|"

        modified_line = final_line

        f_out.write(modified_line + '\n' + f_in.read())
    except IndexError:
        print(f"Can't read first line of: {f_in}")
        sys.exit(1)


def remove_newlines_and_replace_inplace(filename, mappings_file):
    temp_filename = filename + ".temp"  # Create a temporary filename

    # Load mappings from the mappings file
    replacement_mapping = load_mappings(mappings_file, '|')

    # Construct the replacement string pattern using only the replacement strings
    replacement_strings = [value[0] for value in replacement_mapping.values()]
    escaped_replacement_strings = [re.escape(string) for string in replacement_strings]
    #replacement_string_pattern = "|".join(f"{escaped_string}" for escaped_string in escaped_replacement_strings)
    replacement_string_pattern = "|".join(escaped_replacement_strings)

    # Define a function to replace replacement strings with their corresponding numeric sequences
    def replace_replacement_string(match):
        matched_string = match.group(0)
        #return next((key for key, value in replacement_mapping.items() if value[0].rstrip('|') == matched_string), matched_string)
        return next(key for key, value in replacement_mapping.items() if value[0] == matched_string)

    # Read the original file, apply replacements, and remove newlines
    with open(filename, 'r') as infile, open(temp_filename, 'w') as outfile:
        content = infile.read()
        modified_content = re.sub(replacement_string_pattern, replace_replacement_string, content)
        modified_content_without_newlines = modified_content.replace('\n', '')
        outfile.write(modified_content_without_newlines)

    # Replace the original file with the temporary file (atomic operation)
    os.replace(temp_filename, filename)


def encode_gs4_script(input_file, output_file, target_encoding="utf-16le"):
  with open(input_file, "r") as f_in, open(output_file, "wb") as f_out:
    text = f_in.read()

    # Define a regular expression to match control characters
    #controlchar_pattern = r"\\x([0-9a-fA-F]{2,4})\|"
    controlchar_pattern = r"\\L?(\d+)\|"

    def replace_decimal(match):
      decimal_value = int(match.group(1))
      if 32 <= decimal_value <= 126:  # Convert to symbol, if the number is in ASCII 32-126 range
        ascii_symbol = convert_decimal_to_ascii(decimal_value)
        hex_code = hex(ord(ascii_symbol))[2:].upper().zfill(4)
        return f"[U+{hex_code}]"
      else:
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
            print(f'After you encode the file, please fix the {num} error(s) in the "{output_file}" with the "--fix" flag or a hex editor.')
        elif not fix:
            print('')
            print('No discrepancies were found.')


def rename_decoded_file(output_file):
  final_name = os.path.splitext(output_file)[0]
  os.rename(output_file, final_name)


def main():
    # Define the mappings text file
    mappings = "ajaat-gs4-script-mappings.txt"

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Convert AJ:AA Trilogy's GS4 (Apollo Justice) scripts")
    subparsers = parser.add_subparsers(title="Main Commands", dest="command")

    # Subparser for decoding
    decode_parser = subparsers.add_parser("decode", help="Decode GS4 scripts to readable format")
    decode_parser.add_argument("input_file", type=str, help="Path to the input binary file or wildcard pattern (mandatory)")
    decode_parser.add_argument("output_file", type=str, nargs='?', default=None, help="Path to the output text file (optional)")

    # Subparser for encoding
    encode_parser = subparsers.add_parser("encode", help="Encode readable GS4 scripts back to binary")
    encode_parser.add_argument("input_file", type=str, help="Path to the input text file or wildcard pattern (mandatory)")
    encode_parser.add_argument("output_file", type=str, nargs='?', default=None, help="Path to the output binary file (optional)")

    # Subparser for comparison
    compare_parser = subparsers.add_parser("compare", help="Compare the original and modified binary (only do this with the original and unmodified binary)")
    compare_parser.add_argument("file1", type=str, help="Path to one (original or edited) binary file (mandatory)")
    compare_parser.add_argument("file2", type=str, help="Path to the other (original or edited) binary file (mandatory)")
    compare_parser.add_argument("--fix", action="store_true", help="Attempt to fix the UTF-16LE's byte discrepancies, always use the original file first (optional)")

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
            decode_gs4_script(input_file, output_file, mappings)

            # Fix the first line of the file (removing the L chars and converting ASCII symbols to decimals)
            fix_first_line(output_file, f"{output_file}.2")

            # Remove temporary output file if it exists
            try:
                os.remove(output_file)
            except FileNotFoundError:
                pass

            # Rename the final file to the original output file
            rename_decoded_file(f"{output_file}.2")
            
            print(f'Converted "{input_file}" to readable format: "{output_file}"')

    # Encode argument
    elif args.command == "encode":
        input_files = glob.glob(args.input_file)
        for input_file in input_files:
            output_file = args.output_file if args.output_file else f"{os.path.splitext(input_file)[0]}.encoded.bin"
            remove_newlines_and_replace_inplace(input_file, mappings)
            encode_gs4_script(input_file, output_file)
            print(f'Converted "{input_file}" back to binary format: "{output_file}"')

    # Compare argument
    elif args.command == "compare":
        compare_files(args.file1, args.file2, fix=args.fix)

if __name__ == "__main__":
  main()
