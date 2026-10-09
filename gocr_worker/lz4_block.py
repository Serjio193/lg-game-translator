"""Bounded lossless block codec using native LZ4, with reusable buffers."""
import ctypes as C


class Lz4Block:
    def __init__(self, library="liblz4.so.1", size=2764828):
        self.lib = C.CDLL(str(library))
        self.size = size
        self.lib.LZ4_compressBound.argtypes = [C.c_int]
        self.lib.LZ4_compressBound.restype = C.c_int
        self.bound = self.lib.LZ4_compressBound(size)
        self.lib.LZ4_sizeofState.argtypes = []
        self.lib.LZ4_sizeofState.restype = C.c_int
        self.lib.LZ4_compress_fast_extState.argtypes = [C.c_void_p, C.c_void_p,
                                                     C.c_void_p, C.c_int, C.c_int, C.c_int]
        self.lib.LZ4_compress_fast_extState.restype = C.c_int
        self.lib.LZ4_decompress_safe.argtypes = [C.c_void_p, C.c_void_p, C.c_int, C.c_int]
        self.lib.LZ4_decompress_safe.restype = C.c_int
        # ctypes buffers/state are private to one request owner; no shared thread use.
        self.state = C.create_string_buffer(self.lib.LZ4_sizeofState())
        self.compressed = C.create_string_buffer(self.bound)
        self.decoded = C.create_string_buffer(size)

    def compress(self, raw, acceleration=1):
        if len(raw) != self.size or not 1 <= acceleration <= 16:
            raise ValueError("Invalid block size or acceleration")
        n = self.lib.LZ4_compress_fast_extState(self.state, raw, self.compressed,
                                              len(raw), self.bound, acceleration)
        if n <= 0:
            raise ValueError("LZ4 compression failed")
        return C.string_at(self.compressed, n)

    def decompress(self, raw):
        if not 0 < len(raw) <= self.bound:
            raise ValueError("Compressed block exceeds budget")
        n = self.lib.LZ4_decompress_safe(raw, self.decoded, len(raw), self.size)
        if n != self.size:
            raise ValueError("Invalid or truncated LZ4 frame block")
        return self.decoded.raw
