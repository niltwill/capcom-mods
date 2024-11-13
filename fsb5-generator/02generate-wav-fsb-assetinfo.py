import os
import shutil
import subprocess

# Check if ffprobe is in the PATH
ffprobe_path = shutil.which("ffprobe")
if ffprobe_path is None:
    print('"ffprobe" is not found in your PATH! Please install ffprobe and add it to your PATH (or this directory).')
    sys.exit(1)

# Path to input folder containing .wav files
input_folder = './Input'

# Path to the template text file
template_file = 'asset-dump.txt'

# Output folder for the modified files
output_folder = './Output'

# Ensure the output folder exists
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Function to get the audio information using ffprobe
def get_audio_info(file_path):
    # Run ffprobe to get the audio information
    ffprobe_command = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', file_path
    ]
    try:
        result = subprocess.run(ffprobe_command, capture_output=True, text=True, check=True)
        data = result.stdout
        # Extract the necessary data from the json output
        import json
        info = json.loads(data)

        # Extract channels, frequency, duration
        channels = info['streams'][0]['channels']
        frequency = int(info['streams'][0]['sample_rate'])
        duration = float(info['format']['duration'])

        # Round the duration to 4 decimal places
        duration = round(duration, 4)

        return channels, frequency, duration
    except subprocess.CalledProcessError as e:
        print(f"Error processing file {file_path}: {e}")
        return None

# Function to modify the template and save to output folder
def process_file(input_file, output_dir):
    # Get audio info (channels, frequency, duration)
    channels, frequency, duration = get_audio_info(input_file)
    
    if channels is None:
        print(f"Skipping file {input_file} due to error.")
        return

    # Find the corresponding .resource file (assumes .resource file has the same base name as the .wav file)
    resource_filename = f"{os.path.splitext(os.path.basename(input_file))[0]}.resource"
    resource_file_path = os.path.join(output_folder, resource_filename)

    # Check if the .resource file exists
    if not os.path.exists(resource_file_path):
        print(f"Resource file not found for {input_file}, skipping.")
        return

    # Get the file size of the .resource file
    resource_size = os.path.getsize(resource_file_path)

    # Extract the base name (without extension) for m_Name
    file_base_name = os.path.splitext(os.path.basename(input_file))[0]

    # Read the template file and update values
    with open(template_file, 'r') as f:
        content = f.read()

    # Replace the template placeholders with actual values
    content = content.replace('m_Name = ""', f'm_Name = "{file_base_name}"')
    content = content.replace('m_Channels = 2', f'm_Channels = {channels}')
    content = content.replace('m_Frequency = 44100', f'm_Frequency = {frequency}')
    content = content.replace('m_Length = 1', f'm_Length = {duration}')
    content = content.replace('m_Source = "sharedassets0.resource"', f'm_Source = "{file_base_name}.resource"')
    content = content.replace('m_Size = 1000', f'm_Size = {resource_size}')

    # Create the output directory for the file (based on the filename)
    output_file_dir = os.path.join(output_folder, file_base_name)
    os.makedirs(output_file_dir, exist_ok=True)

    # Write the modified content to the output file
    output_txt_file = os.path.join(output_file_dir, f'{file_base_name}.txt')
    with open(output_txt_file, 'w') as f:
        f.write(content)

    # Copy the .resource file to the new folder
    output_resource_file = os.path.join(output_file_dir, f'{file_base_name}.resource')
    shutil.move(resource_file_path, output_resource_file)

    print(f"Processed and saved: {output_txt_file} and {output_resource_file}")

# Process all .wav files in the input folder
for filename in os.listdir(input_folder):
    if filename.endswith('.wav'):
        input_file = os.path.join(input_folder, filename)
        process_file(input_file, output_folder)
