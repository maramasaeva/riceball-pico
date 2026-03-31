# Memory-efficient frame storage - reads from binary file
# Total frames: 21
# Bytes per frame: 1024

NUM_FRAMES = 21
BYTES_PER_FRAME = 1024
BINARY_FILE = 'riceball_frames.bin'

def get_frame(frame_index):
    """Get frame data as bytearray. frame_index: 0 to 20"""
    with open(BINARY_FILE, 'rb') as f:
        f.seek(frame_index * BYTES_PER_FRAME)
        return bytearray(f.read(BYTES_PER_FRAME))

class FrameList:
    def __getitem__(self, index):
        return get_frame(index)
    def __len__(self):
        return NUM_FRAMES
    def __iter__(self):
        for i in range(NUM_FRAMES):
            yield get_frame(i)

FRAMES = FrameList()
