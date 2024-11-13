import fsb5
import os
import sys
import subprocess
import shutil

# Check if ffmpeg is in the PATH
if shutil.which("ffmpeg") is None:
    print('"ffmpeg" is not found in your PATH! Please install ffmpeg and add it to your PATH (or this directory).')
    sys.exit(1)

# Function to create an audio file with loop metadata using ffmpeg without intermediate files
def create_audio_with_loop_metadata(sample_data, sample_rate, channels, output_filename, loop_start=None, loop_end=None, sample_format='wav', quality='10', quiet=False):
    # Determine input format for ffmpeg
    if sample_format in ('ogg', 'vorbis'):
        input_format = 'ogg'
        ffmpeg_command = [
            'ffmpeg', '-y', '-f', input_format, '-i', 'pipe:0',
            '-acodec', 'libvorbis', '-q:a', quality, '-f', 'ogg', '-fflags', '+genpts'
        ]
    else:
        input_format = 'wav'  # Default for raw PCM data
        ffmpeg_command = [
            'ffmpeg', '-y', '-f', input_format, '-ar', str(sample_rate), '-ac', str(channels), '-i', 'pipe:0',
            '-acodec', 'libvorbis', '-q:a', quality, '-f', 'ogg', '-fflags', '+genpts'
        ]
    
    if quiet:
        ffmpeg_command.insert(1, '-loglevel')
        ffmpeg_command.insert(2, 'quiet')

    # Add loop metadata if loop points are provided
    if loop_start is not None and loop_end is not None:
        ffmpeg_command += [
            '-metadata', f'LoopStart={loop_start}',
            '-metadata', f'LoopEnd={loop_end}'
        ]

    ffmpeg_command.append(output_filename)

    # Run ffmpeg and send the sample data through the pipeline
    process = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE)
    process.communicate(input=sample_data)
    process.wait()

# Main function to process all .fsb files in the input directory
def process_fsb_directory(input_directory, output_directory, quality='10', quiet=False):
    os.makedirs(output_directory, exist_ok=True)

    for fsb_filename in os.listdir(input_directory):
        if fsb_filename.endswith('.fsb') or fsb_filename.endswith('.resource'):
            fsb_path = os.path.join(input_directory, fsb_filename)
            if not quiet:
                print(f"Processing file: {fsb_path}")

            with open(fsb_path, 'rb') as f:
                fsb = fsb5.FSB5(f.read())

            for sample in fsb.samples:

                # Get sample data and rebuild the sample directly in memory
                rebuilt_sample = fsb.rebuild_sample(sample)
                loop_start = loop_end = None

                # Determine the sample format and extension using get_sample_extension()
                sample_format = fsb.get_sample_extension()

                # Extract loop points if available
                if sample.metadata:
                    for chunk_type, chunk_data in sample.metadata.items():
                        if chunk_type == fsb5.MetadataChunkType.LOOP:
                            loop_start, loop_end = chunk_data

                # Generate the output filename with the detected extension
                output_filename = os.path.join(output_directory, f'{os.path.splitext(fsb_filename)[0]}.{sample_format}')

                # Create the audio file using ffmpeg and add the loop metadata
                create_audio_with_loop_metadata(
                    rebuilt_sample, sample.frequency, sample.channels, output_filename,
                    loop_start, loop_end, sample_format, quality, quiet
                )
                if not quiet:
                    print(f"Created audio file: {output_filename}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python convert_fsb_to_audio.py <input_directory> <output_directory> [quality] [--quiet]")
        sys.exit(1)

    input_directory = sys.argv[1]
    output_directory = sys.argv[2]
    quality = '10'  # Default quality level
    quiet = False   # Default verbosity

    # Parse additional arguments for quality and quiet mode
    for arg in sys.argv[3:]:
        if arg.startswith("--quiet"):
            quiet = True
        else:
            quality = arg  # Assume any other argument is the quality level

    process_fsb_directory(input_directory, output_directory, quality, quiet)
