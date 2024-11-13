import fsb5

# read the file into a FSB5 object
with open('sharedassets0.resource', 'rb') as f:
    fsb = fsb5.FSB5(f.read())

print(fsb.header)

# get the extension of samples based off the sound format specified in the header
ext = fsb.get_sample_extension()

# iterate over samples
for sample in fsb.samples:
    # print sample properties
    print(f'''{sample.name}.{ext}:
    Frequency: {sample.frequency}
    Channels: {sample.channels}
    Samples: {sample.samples}''')

    # print metadata if available
    if sample.metadata:
        print("\tMetadata:")
        for chunk_type, chunk_data in sample.metadata.items():
            if chunk_type == fsb5.MetadataChunkType.CHANNELS:
                print(f"\t\tCHANNELS: {chunk_data[0]}")
            elif chunk_type == fsb5.MetadataChunkType.FREQUENCY:
                print(f"\t\tFREQUENCY: {chunk_data[0]}")
            elif chunk_type == fsb5.MetadataChunkType.LOOP:
                loop_start, loop_end = chunk_data
                print(f"\t\tLOOP: Start={loop_start}, End={loop_end}")
            elif chunk_type == fsb5.MetadataChunkType.VORBISDATA:
                crc32, unknown = chunk_data
                print(f"\t\tVORBISDATA: crc32={crc32}, unknown={unknown}")
            elif chunk_type == fsb5.MetadataChunkType.XMASEEK:
                print(f"\t\tXMASEEK: {chunk_data}")
            elif chunk_type == fsb5.MetadataChunkType.DSPCOEFF:
                print(f"\t\tDSPCOEFF: {chunk_data}")
            elif chunk_type == fsb5.MetadataChunkType.XWMADATA:
                print(f"\t\tXWMADATA: {chunk_data}")
            else:
                # For unrecognized chunks, print the chunk type and raw data
                print(f"\t\t{chunk_type}: {chunk_data}")

    # rebuild the sample and save
    with open(f'{sample.name}.{ext}', 'wb') as f:
        rebuilt_sample = fsb.rebuild_sample(sample)
        f.write(rebuilt_sample)