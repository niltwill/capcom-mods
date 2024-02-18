This is my compiled version of *libvorbis 1.3.6* ("libvorbis I 20180316") on Windows. As you can imagine, it's [not as straightforward](https://deltaepsilon.ca/posts/compiling-libogg-libvorbis-for-dummies) to get it compiled.
This version is a [lot](https://www.linuxfromscratch.org/blfs/view/9.1/multimedia/vorbistools.html) easier to compile on a Linux distro from scratch, locally
(to not pollute your existing system, you should keep the prefix to `/usr/local`, and you don't need to install the docs).
Or you can just try installing your distro's `vorbis-tools` package if you don't care about using the exact same version as the games. The newest works as well.

> Note: My commands below assume you're on a Windows system.

Here is how you can convert your WAV (or other audio) files into OGG files (this will use the exact library version, like in the "Apollo Justice: Ace Attorney Trilogy" and "Ghost Trick: Phantom Detective" games):

`oggenc.exe -c LoopStart=-1 -c LoopEnd=-1 -q10 <YOUR_SOURCE_AUDIO>.wav -o <YOUR_CONVERTED_AUDIO>.ogg`

Howver, always study your source OGG files, since not every OGG file may use -1 for LoopStart and LoopEnd (an OGG file may also set the actual loop points here).

You can use this command to convert all WAV files to OGG in the current directory:

`for /r %f in (*.wav) do oggenc.exe -c LoopStart=-1 -c LoopEnd=-1 -q10 %f -o "%~nf".ogg`
