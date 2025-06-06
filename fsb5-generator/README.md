# FSB5 resource and asset generator
These scripts can help you create FSB .resource files, with the potential to add a loop point and to generate an asset text dump for it. Then you can use [UABE](https://github.com/SeriousCache/UABE) (older Unity versions) or [UABEA](https://github.com/nesrak1/UABEA) (newer Unity versions) to replace existing asset data and resource files, when it comes to game music/sound.

**Main benefit:** It's no longer necessary to use the `tidalwav WAV Loop Editor` plugin in Unity, or to have WAV files as source material, in order to set the loop point. It's still recommended to use 320 kbps MP3, at least. First, convert them to `-q 9` quality OGG files. Unity, by default, sets the OGG audio quality to 100 (which is okay if the source is a WAV or FLAC file). But if you use a converted 320 kbps MP3 that is a `-q 9` OGG file, then set the quality to 90.

## Generate .resource files

Put all your audio files into the `Input` directory then run the `01generate-ogg-fsb-resource.bat` (for OGG audio files) or `01generate-wav-fsb-resource.bat` (for WAV audio files) script. Before execution, you should take a look inside the batch file and change the Unity Editor's version (folder) for what the game used (if possible). The generated ".resource" file should be the same as if you'd do it from Unity, byte to byte equivalent.

At first, I tried to use the [FMOD Studio API](https://www.fmod.com/download) which includes `fsbankcl.exe` to generate FSB5 files from the command-line. Then I quickly realized that that's not going to work, as the file size was notably different from what Unity generated (due to compression and possibly other tweaks). You must use what's bundled with the Unity editor. To do this, you can simply install Unity, then remove/uninstall it after you get the `FSBTool`, which is located at: `<path to Unity folder>\Editor\Data\Tools\FSBTool\x64\`

## Generate asset info (text dump)

You can use the Python scripts `02generate-ogg-fsb-assetinfo.py` or `02generate-wav-fsb-assetinfo.py` to generate the asset info text dump for the .resource files. (Use the "wav" if your source files are WAV, or the other for OGGs). Do note that this script requires `ffprobe` to be available in your PATH (environment variables), or you can also put it into this directory, next to the script, if you don't want that. Also don't change or remove the `asset-dump.txt` file, which is used to replace the needed fields.

*Note:* The `m_Length` may not always be the same as what Unity would generate there. This is the only minor difference that can happen.

If that's not good enough, you can keep using the Unity editor to individually export the ".resource" and its ".assets" file (though this is a bit more tedious and time-consuming) and just add the loop to it manually, later.

## Looping

### Add a new loop

To add a loop point for a file that doesn't have one, you can use the script called `add_fsb_loop.py`.
For a simple example: `python add_fsb_loop.py sharedassets0.resource 7800 56000`

`7800` is the loop start (sample), and `56000` is the loop end (sample). Change to whatever values you need. It's important to cut your audio file near the end of the loop point, so that it shouldn't have a very long duration after the loop, or there may not be enough empty bytes (space) left to make way for the loop data (otherwise you may have to manually remove the relevant bytes with a hex editor and keep testing until it works and can be extracted successfully).

After you have the .resource files ready in the `Output` folder, you can run the `03filenames-for-loop.bat` to generate their file path and empty loop points as a basis for a new batch file. Then you can remove lines that do not need to loop, etc.

### Change an existing loop

If you want to change the existing "loop start" and "loop end" sample values, the following script does it. Make sure to run this script only if you have a loop set already:

`python update_fsb_loop.py sharedassets0.resource 12007 64103`

### Read loop data

If you want to know if a .resource file has a loop, you can use the script:

`python read_fsb_loop.py sharedassets0.resource`

### To remove the loop

You are not going to have a problem with files that don't loop (this is the default behaviour), but if you want to get rid of the existing looping, regenerate the .resource file.

## To convert the FSB into an OGG file

The folder `python-fsb5` is an included GitHub repo, taken from: [python-fsb5](https://github.com/HearthSim/python-fsb5) (I also merged all the proposed fixes or pull requests).

For checking FSB info and simple extracting, you can mess around with the `test.py` file in there. The main point of interest is a script called: `convert_fsb_to_ogg.py`, which can extract the FSB .resource files into OGG audio files. If a loop point exists, the OGG file will also make use of it with "LoopStart" and "LoopEnd". If the quality level for the OGG is not given, it will default to "10" (highest), so you can simply omit "9" in the following:

`python convert_fsb_to_ogg.py .\in .\out 9 --quiet`

It processes all the .fsb files from the `in` directory (placed in the same folder as the script) into the `out` folder, as OGG "-q 9", in quiet mode. Without `--quiet`, you will see the conversion process and some extra info. Make sure that the input file extension is `.fsb` or `.resource`

Be aware that `convert_fsb_to_ogg.py` requires the `ffmpeg` binary to be available in your local path (environment variable), or you can also put it into the same directory as the Python script itself.
