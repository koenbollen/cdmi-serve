
import re

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
    if not end:
        return start, end
    return start, end+1

# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=79:

