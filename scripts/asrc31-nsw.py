import argparse
#import logging
import os
import shutil
import tempfile
import sys


try:
    import ffmpeg # ffmpeg is required for the OGG files (it's more precise than pydub)
except ImportError:
    print ('"ffmpeg" is not available! Install it: "pip install ffmpeg-python"')
    sys.exit(1)


DESCRIPTION = """Encode and decode RE Engine .asrc audio files.
Now with more confusion! For version 31 (AJ:AA Trilogy's Nintendo Switch port) only."""
SRCH_INFO = """srch (stub)
  id:        %d"""
SRCD_INFO = """srcd (data)
  id:        %d
  unk0:      %d
  unk1:      %d
  urate:     %d
  soff:      %s

  strm:      %s
  loop:      %s
  lps:       %d
  lpe:       %d
  mark:      %s

  channels:  %d
  duration:  %f (seconds)
  samples:   %d
  rate:      %d
  depth:     %d"""


read_u32 = lambda f: int.from_bytes(f.read(4), 'little')
write_u32 = lambda f, x: f.write(x.to_bytes(4, 'little'))


# Only used to capture the different total samples count (if any)
#logging.basicConfig(filename='warning_log.txt', level=logging.WARNING, format='%(message)s')


def format_marker_list(ml):
    if ml is None:
        return

    for i, m in enumerate(ml):
        if m[0] == 0xffffffff:
            ml[i] = (m[1],)

    return ','.join(':'.join(str(y) for y in x) for x in ml)


def parse_marker_list(ms):
    ml = []

    if ms is not None:
        for m in ms.split(','):
            try:
                mfields = tuple(int(x) for x in m.split(':', 2))
            except ValueError as e:
                raise ValueError("invalid marker list") from e

            if len(mfields) == 1:
                mfields = (0xffffffff, mfields[0])

            ml.append(mfields)

    return ml


def find_ogg_sync_code(file_name, value):
    sync_code = b'OggS'
    with open(file_name, 'rb') as file:
        while True:
            byte = file.read(1)
            if not byte:
                break
            if byte == sync_code[0].to_bytes(1, 'little'):
                remaining_bytes = file.read(3)
                if remaining_bytes == sync_code[1:]:
                    return file.tell() - 4 * value
    return None


"""
def asrc31_ogg_header_size(file_name): # it's easier to get this directly from the OGG file
    sync_code = b'OggS'
    with open(file_name, 'rb') as file:
        while True:
            byte = file.read(1)
            if not byte:
                break
            if byte == sync_code[0].to_bytes(1, 'little'):
                remaining_bytes = file.read(3)
                if remaining_bytes == sync_code[1:]:
                    file.seek(file.tell()+22)  # jump to the 'number_page_segments' byte
                    number_page_segments = int.from_bytes(file.read(1), 'little')
                    header_size = 27 + number_page_segments
                    return header_size
    return None
"""


def get_ogg_header_size(ogg_file): # should work for standard OGG audio files that follow the specifications
    with open(ogg_file, 'rb') as file:
        capture_pattern = file.read(4)
        if capture_pattern == b'OggS':
            file.seek(26) # jump to the 'number_page_segments' byte
            number_page_segments = file.read(1)[0]
            header_size = number_page_segments + 27
            return header_size
        else:
            return 0


def read_bytes_at_offset(file_name, target_offset, num_bytes):
    with open(file_name, 'rb') as bf:
        bf.seek(target_offset)
        bytes_values = [int.from_bytes(bf.read(1), 'little') for _ in range(num_bytes)]
        return bytes_values


def write_bytes_at_offset(file_name, target_offset, byte_values):
    with open(file_name, 'r+b') as of:
        of.seek(target_offset)
        for byte_value in byte_values:
            of.write(byte_value.to_bytes(1, 'little'))


def get_ogg_info(file):
    try:
        original_offset = find_ogg_sync_code(file.name, 1)
        file.seek(original_offset)
        data = file.read()
        file_directory = os.path.dirname(file.name)
        with tempfile.NamedTemporaryFile(delete=False, dir=file_directory, suffix=".tmp") as temp_file:
            temp_file.write(data)
        audio_info = ffmpeg.probe(temp_file.name, show_entries="format=sample_rate,channels,bit_rate,duration", v="quiet")

        if 'streams' in audio_info:
            stream_info = audio_info['streams'][0]
        elif 'format' in audio_info:
            stream_info = audio_info['format']
        else:
            raise ValueError("No audio streams or format information found.")

        sample_rate = int(stream_info['sample_rate'])
        channels = int(stream_info['channels'])
        duration = float(stream_info['duration'])
        bit_rate = int(stream_info['bit_rate'])
        sample_width = int(bit_rate / (sample_rate * channels))
        total_samples = round(duration * sample_rate)

        return {
            'sample_rate': sample_rate,
            'channels': channels,
            'duration': duration,
            'sample_width': sample_width,
            'total_samples': total_samples
        }

    except ffmpeg.Error as e:
        print(f"Error: {e.stderr.decode('utf-8')}")
    finally:
        try:
            os.remove(temp_file.name)
        except Exception as e:
            print(f"Error during cleanup: {e}")


def encode(args, pre=False):
    params = get_ogg_info(args.file)
    data_offset = 0 # temp zero, this is actually set at the end after everything's done

    args.file.seek(0, 2)
    file_size = args.file.tell()
    args.file.seek(0)

    if pre and args.cpb:
        loop = args.loop
    else:
        loop = not all(x is None for x in (args.lps, args.lpe))

    if args.lps is None:
        args.lps = 0
    if args.lpe is None:
        args.lpe = params['total_samples'] - 1

    if pre:
        mark = args.mark or []
    else:
        mark = parse_marker_list(args.mark)

    with open(args.out, 'wb') as of:
        of.write(b'srcd')
        write_u32(of, 0) # always 0
        write_u32(of, file_size)
        of.write(b'ogg ')

        write_u32(of, args.strm)
        write_u32(of, args.id)
        write_u32(of, args.unk0)

        write_u32(of, params['channels'])
        write_u32(of, params['total_samples'] * params['channels'] + args.soff)
        write_u32(of, args.urate)
        write_u32(of, params['sample_rate'])
        write_u32(of, 16) # lossless bit depth is not meaningful for OGGs, keep it 16

        write_u32(of, 1) # always 1

        of.write(bytes((loop,)))
        write_u32(of, args.lps)
        write_u32(of, args.lpe)

        write_u32(of, len(mark))
        for m in mark:
            write_u32(of, m[0])
            write_u32(of, m[1])

        of.write(b'\0' * 9) # always 0
        write_u32(of, args.unk1)

        write_u32(of, of.tell() + 8)
        write_u32(of, data_offset)

        shutil.copyfileobj(args.file, of)

    args.file.close()
    
    # Now to handle the "data_offset"
    # First check if the argument is from replace or encode function
    replace_def = hasattr(args, 'base')
    encode_def = hasattr(args, 'file')
    
    # My workaround for "data_offset", you can either keep it with the original WAV header size or try the (hopefully) correct OGG header size (usually 28)
    # I tested this and both of these work, so it doesn't matter too much
    # You can comment out one or the other and use what you prefer
    # To calculate the total OGG header size, the reference was this: https://www.loc.gov/preservation/digital/formats/fdd/fdd000026.shtml#notes
    
    # Capcom reused the typical WAV header size (usually 44) for OGG too (which should be incorrect, but nevermind)
    # 1. For replace: this is read from the base asrc.31 file and then applied to the output file
    # 2. For encode: without a base asrc.31 file, it's set to "44"
    # So to reuse the "old" WAV header, I recommend to use replace, which doesn't need a manual check afterwards (for the files below)!
    # These are the files that differ from "44" (probably because they have additional metadata):
    # natives\stm\streaming\sound\common\se\get_medal_1648.asrc.31
    # natives\stm\streaming\sound\gs4\stream\bgm\interactivemusic\bgm070_bass_1648.asrc.31
    # natives\stm\streaming\sound\gs4\stream\bgm\interactivemusic\bgm070_click_1648.asrc.31
    # natives\stm\streaming\sound\gs4\stream\bgm\interactivemusic\bgm070_drums_1648.asrc.31
    # natives\stm\streaming\sound\gs4\stream\bgm\interactivemusic\bgm070_keyboards_1648.asrc.31
    # natives\stm\streaming\sound\gs4\stream\bgm\interactivemusic\bgm070_leadguitar_1648.asrc.31
    # natives\stm\streaming\sound\gs4\stream\bgm\interactivemusic\bgm070_rhythmguitar_1648.asrc.31
    # natives\stm\streaming\sound\gs5\se\script_com\bikkuri.asrc.31
    # natives\stm\streaming\sound\gs5\se\se_cr003\kokone_pc_tap_flick.asrc.31
    # natives\stm\streaming\sound\gs5\se\se_cr203\biyoin_chakushin_both.asrc.31
    # natives\stm\streaming\sound\gs5\se\se_cr203\biyoin_chakushin_hidari.asrc.31
    # natives\stm\streaming\sound\gs5\se\se_cr203\biyoin_chakushin_migi.asrc.31
    # natives\stm\streaming\sound\gs5\se\se_cr207\shoko_performance_ken_hikaru.asrc.31
    # natives\stm\streaming\sound\gs6\se\yamashinop\yamashinop_coin_break_1648.asrc.31
    # natives\stm\streaming\sound\startupscreen\museum\animationstudio\se\close_anim_studio_1648.asrc.31
    # natives\stm\streaming\sound\startupscreen\museum\animationstudio\se\enter_anim_studio_1648.asrc.31
    # natives\stm\streaming\sound\startupscreen\museum\animationstudio\se\se_court_000.asrc.31
    # natives\stm\streaming\sound\startupscreen\museum\artlibrary\se\close_art_library_1648.asrc.31
    # natives\stm\streaming\sound\startupscreen\museum\artlibrary\se\enter_art_library_1648.asrc.31
    # natives\stm\streaming\sound\startupscreen\museum\artlibrary\se\paper_1648.asrc.31
    # natives\stm\streaming\sound\startupscreen\museum\artlibrary\se\screendown_1648.asrc.31
    # natives\stm\streaming\sound\startupscreen\museum\artlibrary\se\screenup_1648.asrc.31
    # natives\stm\streaming\sound\startupscreen\museum\orchestrahall\se\curtain_close_1648.asrc.31
    # natives\stm\streaming\sound\startupscreen\museum\orchestrahall\se\curtain_open_1648.asrc.31
    # natives\stm\streaming\sound\startupscreen\se\entering_titlesel_1648.asrc.31
    # natives\stm\streaming\sound\startupscreen\se\enter_startup_screen_1648.asrc.31
    # If you modify any of the files above, manually review them with a hex editor, if you want to keep it to the original
    
    # old - with reused WAV header (this is how the original files are)
    # """
    if replace_def: # replace
        original_offset = find_ogg_sync_code(args.base.name, 2)
        if original_offset is not None:
            byte_values = read_bytes_at_offset(args.base.name, original_offset, 4)
            write_bytes_at_offset(args.out, original_offset, byte_values)
    elif encode_def: # encode
        original_offset = find_ogg_sync_code(args.out, 2)
        if original_offset is not None:
            byte_values = [44];
            write_bytes_at_offset(args.out, original_offset, byte_values)
    # """

    # new - with OGG header (should be correct)
    """
    if replace_def: # replace
        original_offset = find_ogg_sync_code(args.base.name, 2)
    elif encode_def: # encode
        original_offset = find_ogg_sync_code(args.out, 2)
    header_size = get_ogg_header_size(args.file.name)
    if original_offset is not None:
        byte_values = [header_size];
        write_bytes_at_offset(args.out, original_offset, byte_values)
    """

def replace(args):
    mi = lambda: None

    mi.file = args.base
    mi = info(mi, prnt=False) 
    args.base.close()

    o = get_ogg_info(args.file)
    args.file.seek(0)

    if not args.cpb and bool(args.mark) != bool(mi.mark):
        raise ValueError("markers %srequired for this file" %
            ("not " if mi.mark is None else ""))

    for a in dir(mi):
        if not a.startswith('__'):
            if a in args and not args.cpb:
                continue
            setattr(args, a, getattr(mi, a))

    encode(args, pre=True)


def decode(args):
    # calling info will validate and seek to end of header
    info(args, prnt=False)

    with open(args.out, 'wb') as of:
        shutil.copyfileobj(args.file, of)

    args.file.close()


def info(args, prnt=True):
    f = args.file

    magic = f.read(4)
    if magic == b'srch':
        assert read_u32(f) == 8 # always 8
        sid = read_u32(f)
        assert read_u32(f) == 1 # always 1

        if prnt:
            print(SRCH_INFO % sid)
        else:
            raise ValueError("srch files contain no audio data")

        return
    elif magic != b'srcd':
        raise ValueError("not a valid asrc file")

    # mock object to pass to other funcs
    mi = lambda: None

    assert read_u32(f) == 0 # always 0
    file_size = read_u32(f)
    assert f.read(4) == b'ogg '

    mi.strm = read_u32(f)
    assert mi.strm <= 1
    mi.strm = bool(mi.strm)
    mi.id = read_u32(f)
    mi.unk0 = read_u32(f)

    mi.channels = read_u32(f)
    mi.samples = read_u32(f)
    mi.urate = read_u32(f)
    mi.rate = read_u32(f)
    mi.depth = read_u32(f)

    assert read_u32(f) == 1 # always 1

    mi.loop = ord(f.read(1))
    assert mi.loop <= 1
    mi.loop = bool(mi.loop)
    mi.lps = read_u32(f)
    mi.lpe = read_u32(f)

    mark_count = read_u32(f)
    if mark_count > 0:
        mi.mark = []
        for _ in range(mark_count):
            mi.mark.append((read_u32(f), read_u32(f)))
    else:
        mi.mark = None

    assert f.read(9) == b'\0' * 9 # always 0
    mi.unk1 = read_u32(f)

    header_size = read_u32(f)
    data_offset = read_u32(f)

    assert header_size == f.tell()

    f.seek(0, 2)
    assert file_size == f.tell() - header_size
    f.seek(header_size)
    
    params = get_ogg_info(args.file)
    header_full = data_offset + header_size # this is a workaround
    assert data_offset == header_full - header_size
    f.seek(header_size)

    mi.soff = mi.samples % mi.channels != 0
    if mi.soff:
        mi.samples -= 1

    assert mi.channels == params['channels']
    mi.duration = params['duration'] # extra duration info that doesn't hurt to have

    # It did occur before rounding the value that it did not always give the correct total samples count as in the original .asrc.31 files
    # Now it should, so this is not needed anymore
    #try:
    #    assert mi.samples == params['total_samples'] * params['channels']
    #except AssertionError as e:
    #    print(f"Warning: {args.file.name} - {mi.samples} was the original sample count, calculated is: {params['total_samples'] * params['channels']}")
    #    logging.warning(f"Warning: {args.file.name} - {mi.samples} was the original sample count, calculated is: {params['total_samples'] * params['channels']}")

    assert mi.samples == params['total_samples'] * params['channels']
    assert mi.rate == params['sample_rate']

    # OGG has no bit depth concept, so this check is useless
    # It's set this way anyway, since the sample width can change for OGGs
    assert mi.depth == params['sample_width'] + (mi.depth - params['sample_width'])

    if prnt:
        mi.mark = format_marker_list(mi.mark)
        print(SRCD_INFO % (mi.id, mi.unk0, mi.unk1, mi.urate,
            mi.soff, mi.strm, mi.loop, mi.lps, mi.lpe, mi.mark,
            mi.channels, mi.duration, mi.samples, mi.rate, mi.depth))

        f.close()

    return mi


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=DESCRIPTION,
        formatter_class=argparse.RawTextHelpFormatter)

    subparsers = parser.add_subparsers(dest='command',
        help="command (encode/replace/decode/info)")

    enc_parser = subparsers.add_parser('e')
    enc_parser.add_argument('-soff', action='store_true',
        help="offset sample count by one")
    enc_parser.add_argument('-strm', action='store_true',
        help="mark audio as streaming")
    enc_parser.add_argument('-lps', type=int, metavar='POS',
        help="loop start sample position")
    enc_parser.add_argument('-lpe', type=int, metavar='POS',
        help="loop end sample position")
    enc_parser.add_argument('-mark', type=str, metavar='LIST',
        help="comma-separated list of markers")
    enc_parser.add_argument('id', type=int,
        help="audio source id (check existing file using i command)")
    enc_parser.add_argument('unk0', type=int,
        help="unknown int (check existing file)")
    enc_parser.add_argument('unk1', type=int,
        help="unknown int (check existing file)")
    enc_parser.add_argument('urate', type=int,
        help="unknown sample rate (check existing file)")
    enc_parser.add_argument('file', type=argparse.FileType('rb'),
        help="path to input file")
    enc_parser.add_argument('out', type=str,
        help="path to output file")

    rep_parser = subparsers.add_parser('r')
    rep_parser.add_argument('-lps', type=int, metavar='POS',
        help="loop start sample position")
    rep_parser.add_argument('-lpe', type=int, metavar='POS',
        help="loop end sample position")
    rep_parser.add_argument('-mark', type=str, metavar='LIST',
        help="comma-separated list of markers")
    rep_parser.add_argument('-cpb', action='store_true',
        help="copy loop and markers from base")
    rep_parser.add_argument('file', type=argparse.FileType('rb'),
        help="path to input file")
    rep_parser.add_argument('base', type=argparse.FileType('rb'),
        help="path to base file")
    rep_parser.add_argument('out', type=str,
        help="path to output file")

    dec_parser = subparsers.add_parser('d')
    dec_parser.add_argument('file', type=argparse.FileType('rb'),
        help="path to input file")
    dec_parser.add_argument('out', type=str,
        help="path to output file")

    inf_parser = subparsers.add_parser('i')
    inf_parser.add_argument('file', type=argparse.FileType('rb'),
        help="path to input file")

    mappings = {'e': encode, 'r': replace, 'd': decode, 'i': info}
    args = parser.parse_args()

    if args.command in mappings:
        mappings[args.command](args)
    else:
        parser.print_help()
