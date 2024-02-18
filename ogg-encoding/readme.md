Here is how you can convert your WAV (or other audio) files into OGG files (this will use the exact library version, like in the "Apollo Justice: Ace Attorney Trilogy" and "Ghost Trick: Phantom Detective" games):

`oggenc.exe -c LoopStart=-1 -c LoopEnd=-1 -q10 <YOUR_SOURCE_AUDIO>.wav -o <YOUR_CONVERTED_AUDIO>.ogg`

However, always study your source OGG files, since not every OGG file may use -1 for LoopStart and LoopEnd (an OGG file may also set the actual loop points here).

You can use this command to convert all WAV files to OGG in the current directory:

`for /r %f in (*.wav) do oggenc.exe -c LoopStart=-1 -c LoopEnd=-1 -q10 %f -o "%~nf".ogg`
