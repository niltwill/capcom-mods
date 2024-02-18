import argparse
import shutil
import wave


DESCRIPTION = """Encode and decode RE Engine .asrc audio files.
Now with more confusion! For version 31 (AJ:AA Trilogy) only."""
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
  samples:   %d
  rate:      %d
  depth:     %d"""


read_u32 = lambda f: int.from_bytes(f.read(4), 'little')
write_u32 = lambda f, x: f.write(x.to_bytes(4, 'little'))


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


def encode(args, pre=False):
    with wave.open(args.file) as w:
        params = w.getparams()
    data_offset = args.file.tell()

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
        args.lpe = params.nframes - 1

    if pre:
        mark = args.mark or []
    else:
        mark = parse_marker_list(args.mark)

    with open(args.out, 'wb') as of:
        of.write(b'srcd')
        write_u32(of, 0) # always 0
        write_u32(of, file_size)
        of.write(b'wav ')

        write_u32(of, args.strm)
        write_u32(of, args.id)
        write_u32(of, args.unk0)

        write_u32(of, params.nchannels)
        write_u32(of, params.nframes * params.nchannels + args.soff)
        write_u32(of, args.urate)
        write_u32(of, params.framerate)
        write_u32(of, params.sampwidth * 8)

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


def replace(args):
    mi = lambda: None

    mi.file = args.base
    mi = info(mi, prnt=False)
    args.base.close()

    with wave.open(args.file) as w:
        params = w.getparams()
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
    assert f.read(4) == b'wav '

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
    
    with wave.open(f) as w:
        params = w.getparams()
    assert data_offset == f.tell() - header_size
    f.seek(header_size)

    mi.soff = mi.samples % mi.channels != 0
    if mi.soff:
        mi.samples -= 1

    assert mi.channels == params.nchannels
    assert mi.samples == params.nframes * params.nchannels
    assert mi.rate == params.framerate
    assert mi.depth == params.sampwidth * 8

    if prnt:
        mi.mark = format_marker_list(mi.mark)
        print(SRCD_INFO % (mi.id, mi.unk0, mi.unk1, mi.urate,
            mi.soff, mi.strm, mi.loop, mi.lps, mi.lpe, mi.mark,
            mi.channels, mi.samples, mi.rate, mi.depth))

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
