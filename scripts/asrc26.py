import argparse
import pathlib
import shutil
import wave


DESCRIPTION = """Encode and decode RE Engine .asrc audio files (srcd).
Only supports version 26 (Ghost Trick) at the moment."""
HEADER_SIZE = 78


splitext = lambda x: x.removesuffix(''.join(pathlib.Path(x).suffixes))
write_u32 = lambda f, x: f.write(x.to_bytes(4, 'little'))


def encode(args):
    with wave.open(args.file) as w:
        params = w.getparams()

    args.file.seek(0, 2)
    file_size = args.file.tell()
    args.file.seek(0)

    loop = args.ls is not None
    if not loop:
        args.ls = 0

    if args.out is None:
        args.out = splitext(args.file.name) + '.asrc.26'

    with open(args.out, 'wb') as of:
        of.write(b'srcd')
        write_u32(of, 0) # always 0
        write_u32(of, file_size)
        of.write(b'wav ')

        write_u32(of, args.bgm)
        write_u32(of, args.id)

        write_u32(of, params.nchannels)
        write_u32(of, params.nframes * params.nchannels)
        write_u32(of, params.framerate)
        write_u32(of, params.sampwidth * 8)

        write_u32(of, 1) # always 1

        of.write(bytes((loop,)))
        write_u32(of, args.ls)
        write_u32(of, params.nframes - 1)

        of.write(b'\0' * 17) # padding

        write_u32(of, HEADER_SIZE)
        write_u32(of, 44) # smpl chunk size

        shutil.copyfileobj(args.file, of)

    args.file.close()


def decode(args):
    magic = args.file.read(4)
    if magic == b'srch':
        raise ValueError("srch files do not contain audio")
    elif magic != b'srcd':
        raise ValueError("not a valid asrc file")

    args.file.seek(HEADER_SIZE)

    if args.out is None:
        args.out = splitext(args.file.name) + '.wav'

    with open(args.out, 'wb') as of:
        shutil.copyfileobj(args.file, of)

    args.file.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=DESCRIPTION,
        formatter_class=argparse.RawTextHelpFormatter)

    subparsers = parser.add_subparsers(dest='command',
        help="command (encode/decode)")

    enc_parser = subparsers.add_parser('e')
    enc_parser.add_argument('-bgm', action='store_true',
        help="mark audio as bgm/streaming")
    enc_parser.add_argument('-ls', type=int, metavar='POS',
        help="loop start position/sample")
    enc_parser.add_argument('id', type=int,
        help="audio source id")
    enc_parser.add_argument('file', type=argparse.FileType('rb'),
        help="path to input file")
    enc_parser.add_argument('out', type=str, nargs='?',
        help="path to output file")

    dec_parser = subparsers.add_parser('d')
    dec_parser.add_argument('file', type=argparse.FileType('rb'),
        help="path to input file")
    dec_parser.add_argument('out', type=str, nargs='?',
        help="path to output file")

    args = parser.parse_args()

    if args.command == 'e':
        encode(args)
    elif args.command == 'd':
        decode(args)
    else:
        parser.print_help()
