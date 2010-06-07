# Koen Bollen <meneer koenbollen nl>
# 2010 GPL

from uuid import uuid1 as uuid
import base64
import re
import struct

def objectid( opaque=None ):
    if opaque is None:
        id = uuid()
        opaque = id.bytes
    else:
        opaque = str(opaque)
    length = 8+len(opaque)
    rawr = struct.pack( "!IxBH%ds" % len(opaque), 20846, length, 0, opaque )
    assert len(rawr) == length
    csum = CRC16()
    csum.update( rawr )
    rawr = rawr[:6] + struct.pack("!H",csum.value) + rawr[8:]
    return base64.b64encode( rawr )


rx_bytes = re.compile( r"bytes=(\d*)-(\d*)" )
def byterange( s, length=None ):
    """Return the byte range (start, end-inclusive).

    RFC2616 14.35.1

    >>> byterange( "bytes=0-499", 10000 )
    (0, 500)
    >>> byterange( "bytes=500-999" )
    (500, 1000)
    >>> byterange( "bytes=-500", 10000 )
    (9500, 10000)
    >>> byterange( "bytes=9500-", 10000 )
    (9500, 10000)
    """
    if not s:
        return None, None
    result = rx_bytes.match( s )
    if not result:
        return None, None
    try:
        start = int(result.group(1))
    except ValueError:
        start = None
    try:
        end = int(result.group(2))
    except ValueError:
        end = None
    if length:
        if start is None:
            start = length-end
            end = length-1
        if end is None:
            end = length-1
    if end is None:
        return start, end
    return start, end+1


class CRC16( object ):
    """
    Object for CRC checksum calculations.

    CRC Parameters:
    Width        = 16
    Poly         = 0x8005
    XorIn        = 0x0000
    ReflectIn    = True
    XorOut       = 0x0000
    ReflectOut   = True
    Algorithm    = bit-by-bit-fast
    Direct       = True
    Check        = 0xbb3d

    Example usage:
    >>> csum = CRC16()
    >>> csum.update( "123456789" )
    >>> print "%0#x" % csum.value
    0xbb3d
    """

    def __init__(self, data=None ):
        self.crc = 0x0000
        if data and len(data) > 0:
            self.update(data)

    def __reflect(self ):
        data = self.crc
        ret = data & 0x01
        for i in xrange( 1 ,16 ):
            data >>= 1
            ret = (ret << 1) | (data & 0x01)
        return ret & 0xffff

    @property
    def value(self ):
        """The resulting value, by calling finalize()."""
        return self.finalize()

    def update(self, data ):
        """Update the crc value with new data."""
        crc = self.crc
        for c in data:
            c = ord(c)
            i = 0x01
            while i & 0xff:
                bit = crc & 0x8000
                if c & i == i:
                    bit = not bit
                crc <<= 1
                if bit != 0:
                    crc ^= 0x8005
                i <<= 1
            crc &= 0xffff
        self.crc = crc & 0xffff

    def finalize(self ):
        """Calculate the final crc value."""
        return self.__reflect() ^ 0x0000;

# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=79:

