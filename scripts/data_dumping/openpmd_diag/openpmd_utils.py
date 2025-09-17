"""
Utility methods for the openPMD standard
"""
from __future__ import annotations
from typing import Literal, Any
import numpy as np

def openpmd_encode(
    string: str | bytes | Any,
    /,
    encoding: Literal['ascii', 'utf-8'] = 'ascii'
) -> np.bytes_:
    """
    Encode to fixed-length character arrays with specified encoding.
    Defaults to ASCII encoding, as specified in the openPMD standard.
    If the input is bytes, it will first be decoded with UTF-8 before
    being re-encoded with the specified encoding.
    """
    # Convert input to str, decoding if necessary.
    val_str = openpmd_decode(string)
    # Encode string to ASCII byte array
    result = bytes(val_str, encoding=encoding)
    # Convert to numpy.bytes_
    result = np.bytes_(result)
    return result

def openpmd_decode(val: str | bytes | Any, /) -> str:
    """
    Convert to string, decoding from bytes if necessary.
    Uses UTF-8 for decoding as this will cover ASCII encoded inputs.
    """
    if isinstance(val, str):
        return val
    try:
        return str(val, encoding='utf-8')
    except:
        try:
            return bytes(val).decode('utf-8')
        except:
            return str(val)
