#!/usr/bin/env /cygdrive/c/Python34/python.exe
#!/usr/bin/env python3


import subprocess
import tempfile

import sys ; sys.path.append("..")
import fsb5
import fsb5.vorbis_headers

fsbtool_path = './FSBTool/FSBTool'
fsbtool_path = 'S:/Program Files/Unity/Editor/Data/Tools/FSBTool/FSBTool.exe'


def fsbtool(source, dest, quality=50, compression='vorbis', container='fsb'):
	subprocess.check_call([fsbtool_path, '-l', '.', '-c', compression, '-C', container, '-i', source, '-o', dest, '-q', str(quality)])

def main():
	with tempfile.NamedTemporaryFile('rb', delete=False) as f:
		temp = f.name
		print(temp)

	rates = [8000, 11000, 16000, 22050, 24000, 32000, 44100, 48000]
	for quality in range(1, 101): #, channels, rate in itertools.product(range(1, 101), range(1, 3), rates):
		print(quality, ': ', end='')
		fsbtool('../samples/AE_Holy_Cast_01.1.ogg', temp, quality=quality)
		with open(temp, 'rb') as f:
			fsb = fsb5.load(f.read())
			crc = fsb.samples[0].metadata[fsb5.MetadataChunkType.VORBISDATA].crc32
			print(crc, crc in fsb5.vorbis_headers.lookup)
			input()




if __name__ == '__main__':
	main()