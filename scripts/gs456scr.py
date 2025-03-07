# A backup copy of gs456scr, in case that gist would be removed
# https://gist.github.com/osyu/5bb86d49153edef5415a7aba09a48ca1

import argparse
import glob
import json
import os.path
import shutil
import traceback


DESCRIPTION = """Encode and decode GS456 (AJ:AA Trilogy) script files."""
USRHDR_SIZE = 48
CLASS_GS4 = (0xdaa48445, 0x5212daa2)
CLASS_GS56 = (0x83f3f042, 0x0b263156)
CLASS_NAME = (0xee933aa7, 0x1aa1a4ac)


read_int = lambda f, l: int.from_bytes(f.read(l), 'little')
write_int = lambda f, l, x: f.write(x.to_bytes(l, 'little'))
read_str = lambda f, l: f.read(l * 2).decode('utf-16le')[:-1]
write_str = lambda f, x: f.write((x + '\0').encode('utf-16le'))
round_up = lambda x, l: (x + l - 1) // l * l
seek_pad = lambda f, l: f.seek(round_up(f.tell(), l))


def encode(f):
    is_gs56 = False

    if f.name.endswith('.json'):
        is_gs56 = True
        data = json.load(f)

        try:
            assert isinstance(data['name'], str)
            assert isinstance(data['labels'], list)
            for l in data['labels']:
                assert isinstance(l, list)
                assert len(l) == 2
                assert all(isinstance(x, str) for x in l)
        except AssertionError as e:
            raise ValueError("incorrect json structure") from e
    elif not f.name.endswith('.bin'):
        raise ValueError(
            "unknown file extension (must be .bin or .json)")

    of = open(f.name.rsplit('.', 1)[0], 'wb')

    of.write(b'USR\0') # magic
    for i in range(3): # resource, userdata and info counts
        write_int(of, 4, 0) 
    for i in range(3): # resource, userdata and data offsets
        write_int(of, 8, USRHDR_SIZE)
    seek_pad(of, 16)

    of.write(b'RSZ\0') # magic
    write_int(of, 4, 16) # version
    write_int(of, 4, 1) # object count
    instance_count = len(data['labels']) + 1 if is_gs56 else 1
    write_int(of, 4, instance_count + 1)
    write_int(of, 4, 0) # userdata count
    write_int(of, 4, 0) # reserved
    write_int(of, 8, 52) # instance offset
    data_offset = round_up(52 + (8 * (instance_count + 1)), 16)
    write_int(of, 8, data_offset) # data offset
    write_int(of, 8, data_offset) # userdata offset

    write_int(of, 4, instance_count) # object table

    write_int(of, 8, 0) # null

    if is_gs56:
        for i in range(instance_count - 1):
            write_int(of, 4, CLASS_GS56[0])
            write_int(of, 4, CLASS_GS56[1])
        write_int(of, 4, CLASS_NAME[0])
        write_int(of, 4, CLASS_NAME[1])
    else:
        write_int(of, 4, CLASS_GS4[0])
        write_int(of, 4, CLASS_GS4[1])

    seek_pad(of, 16)

    if is_gs56:
        for l in data['labels']:
            write_int(of, 4, len(l[0]) + 1)
            write_str(of, l[0])
            seek_pad(of, 4)

            write_int(of, 4, len(l[1]) + 1)
            write_str(of, l[1])
            seek_pad(of, 4)

        write_int(of, 4, len(data['name']) + 1)
        write_str(of, data['name'])
        seek_pad(of, 4)

        write_int(of, 4, instance_count - 1)
        for i in range(instance_count - 1):
            write_int(of, 4, i + 1)
    else:
        f.seek(0, 2)
        size = f.tell()
        f.seek(0)

        write_int(of, 4, size)
        shutil.copyfileobj(f, of)

    of.close()
    f.close()


def decode(f):
    assert f.read(4) == b'USR\0' # magic
    for i in range(3): # resource, userdata and info counts
        assert read_int(f, 4) == 0
    for i in range(3): # resource, userdata and data offsets
        assert read_int(f, 8) == USRHDR_SIZE
    seek_pad(f, 16)
    assert f.tell() == USRHDR_SIZE

    assert f.read(4) == b'RSZ\0' # magic
    assert read_int(f, 4) == 16 # version
    assert read_int(f, 4) == 1 # object count
    instance_count = read_int(f, 4) - 1
    assert read_int(f, 4) == 0 # userdata count
    assert read_int(f, 4) == 0 # reserved
    instance_offset = read_int(f, 8)
    data_offset = read_int(f, 8)
    assert read_int(f, 8) == data_offset # userdata offset

    assert read_int(f, 4) == instance_count # object table

    assert f.tell() == USRHDR_SIZE + instance_offset
    assert instance_count != 0
    assert read_int(f, 8) == 0 # null

    is_gs56 = False

    for i in range(instance_count):
        type_id = read_int(f, 4)
        crc = read_int(f, 4)
        cls = (type_id, crc)

        if cls == CLASS_GS4:
            if instance_count != 1:
                raise ValueError("gs4 class when >1 instance")
        elif cls == CLASS_GS56:
            if i == instance_count - 1:
                raise ValueError("gs56 class at last instance")
            is_gs56 = True
        elif cls == CLASS_NAME:
            if i != instance_count - 1:
                raise ValueError("name class before last instance")
            is_gs56 = True
        else:
            raise ValueError("unknown class")

    seek_pad(f, 16)
    assert f.tell() == USRHDR_SIZE + data_offset

    out = f.name + ('.json' if is_gs56 else '.bin')

    if is_gs56:
        data = {'name': None, 'labels': []}

        for i in range(instance_count - 1):
            label_size = read_int(f, 4)
            label = read_str(f, label_size)
            seek_pad(f, 4)

            text_size = read_int(f, 4)
            text = read_str(f, text_size)
            seek_pad(f, 4)

            data['labels'].append((label, text))

        name_size = read_int(f, 4)
        data['name'] = read_str(f, name_size)
        seek_pad(f, 4)

        assert read_int(f, 4) == instance_count - 1
        for i in range(instance_count - 1):
            assert read_int(f, 4) == i + 1

        with open(out, 'w', encoding='utf-8', newline='\n') as of:
            json.dump(data, of, indent=2, ensure_ascii=False)
            of.write('\n')
    else:
        size = read_int(f, 4)
        cur = f.tell()
        f.seek(0, 2)
        assert size == f.tell() - cur
        f.seek(cur)

        with open(out, 'wb') as of:
            shutil.copyfileobj(f, of)

    f.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=DESCRIPTION,
        formatter_class=argparse.RawTextHelpFormatter)

    subparsers = parser.add_subparsers(dest='command',
        help="command (encode/decode)")

    enc_parser = subparsers.add_parser('e')
    enc_parser.add_argument('file', type=str,
        help="path to input file(s); accepts wildcard")

    dec_parser = subparsers.add_parser('d')
    dec_parser.add_argument('file', type=str,
        help="path to input file(s); accepts wildcard")

    mappings = {'e': encode, 'd': decode}
    args = parser.parse_args()

    if args.command in mappings:
        paths = glob.glob(args.file)

        if not paths:
            raise FileNotFoundError(
                'no such file %s' % repr(args.file))

        for p in paths:
            if os.path.isdir(p):
                continue

            try:
                mappings[args.command](open(p, 'rb'))
            except Exception as e:
                print("error with file %s:\n%s" % (
                    p, traceback.format_exc()))
    else:
        parser.print_help()
