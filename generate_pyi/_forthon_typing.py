"""
Forthon typing.

This module contains type definitions describing objects created by
compiled Forthon packages. The contents of this module are intended
for static type checking only.

If on Python versions < 3.10 and ``from __future__ import annotations``
is not used, types from this module may need to be quoted.
"""
from __future__ import annotations

import typing
from typing import Any, Literal, Protocol, Sequence, TypeAlias, TypeVar, Union
if typing.TYPE_CHECKING:
    from _typeshed import MaybeNone
import numpy as np
from numpy import intp
from numpy.typing import NDArray

__all__ = [
    "_ArrayBytes_co",
    "_ArrayLikeComplex_co",
    "_ArrayLikeFloat_co",
    "_ArrayLikeInt_co",
    "ForthonObject",
]

_T = TypeVar("_T")
_S_co = TypeVar("_S_co", bound=np.generic, covariant=True)
_DualArrayLike: TypeAlias = Union[
    _S_co,
    NDArray[_S_co],
    Sequence[_S_co],
    _T,
    Sequence[_T],
]

_ArrayBytes_co: TypeAlias = NDArray[np.bytes_] | bytes | str
_ArrayLikeComplex_co: TypeAlias = _DualArrayLike[np.bool_ | np.number[Any], complex]
_ArrayLikeFloat_co: TypeAlias = _DualArrayLike[np.bool_ | np.integer[Any] | np.floating[Any], float]
_ArrayLikeInt_co: TypeAlias = _DualArrayLike[np.bool_ | np.integer[Any], int]

class ForthonObject(Protocol):
    """
    Protocol for compiled Forthon package objects.
    """
    def addvarattr(self, var_name: str, attr: str, /) -> None:
        """Adds an attribute to a variable"""
        ...
    def allocated(self, var_name: str, /) -> Literal[0, 1]:
        """Checks whether a dynamic variable is allocated. If a static array or a scalar is passed, it just returns true."""
        ...
    def deprefix(self) -> None:
        """For each variable in the package, a python object is created which has the same name and same value. For arrays, the new objects points to the same memory location."""
        ...
    def forceassign(self, var_name: str, array: NDArray[Any], /) -> None:
        """Forces assignment to a dynamic array, resizing it if necessary"""
        ...
    def gallot(self, group_name: str = "*", iverbose: int = 0, /) -> Literal[0, 1]:
        """Allocates all dynamic arrays in a group"""
        ...
    def gchange(self, group_name: str = "*", iverbose: int = 0, /) -> None:
        """Changes allocation of all dynamic arrays in a group if needed"""
        ...
    def getdict(self, dict_: dict[str, Any] = ..., /) -> dict[str, Any]:
        """Builds a dictionary, including every variable in the package. For arrays, the dictionary value points to the same memory location as the fortran. If a dictionary is input, then that one is updated rather then creating a new one."""
        ...
    def getfobject(self) -> int:
        """Gets id to f object"""
        ...
    def getfunctions(self) -> list[str]:
        """Builds a list containing all of the function names in the package."""
        ...
    def getgroup(self, var_name: str, /) -> str:
        """Returns group that a variable is in."""
        ...
    def getpyobject(self, var_name: str, /) -> Any | None:
        """Returns the python object associated with a name, returns None is object is unallocated"""
        ...
    def gettypename(self) -> str:
        """Returns name of type of object."""
        ...
    def getvarattr(self, var_name: str, /) -> str:
        """Returns the attributes of a variable"""
        ...
    def setvarattr(self, var_name: str, attr: str, /) -> None:
        """Sets the attributes of a variable"""
        ...
    def delvarattr(self, var_name: str, attr: str, /) -> None:
        """Deletes the specified attributes of a variable"""
        ...
    def getvardoc(self, var_name: str, /) -> str | MaybeNone:
        """Gets the documentation for a variable"""
        ...
    def getvarunit(self, var_name: str, /) -> str | MaybeNone:
        """Gets the unit for a variable"""
        ...
    def gfree(self, group_name: str = "*", /) -> Literal[0, 1]:
        """Frees the memory of all dynamic arrays in a group"""
        ...
    def gsetdims(self, group_name: str = "*", iverbose: int = 0, /) -> None:
        """Sets the dimensions of dynamic arrays in the wrapper database"""
        ...
    def isdynamic(self, var_name: str, /) -> Literal[0, 1]:
        """Checks whether a variable is dynamic."""
        ...
    def getvartype(self, var_name: str, /) -> str | None:
        """Returns the fortran type of a variable"""
        ...
    def listvar(self, var_name: str, /) -> str | MaybeNone:
        """Returns information about a variable"""
        ...
    def name(self) -> str:
        """Returns the name of the package"""
        ...
    def reprefix(self) -> None:
        """For each variable in the main dictionary, if there is a package variable with the same name it is assigned to that value. For arrays, the data is copied."""
        ...
    def setdict(self, dict_: dict[str, Any], /) -> None:
        """For each variable in the main dictionary, if there is a package variable with the same name it is assigned to that value. For arrays, the data is copied."""
        ...
    def __setstate__(self, dict_: dict[str, Any], /) -> None:
        """For each variable in the main dictionary, if there is a package variable with the same name it is assigned to that value. For arrays, the data is copied."""
        ...
    def totmembytes(self) -> int:
        """Returns total number of bytes dynamically allocated for the object."""
        ...
    def varlist(self, attr_or_group_name: str = "*", /) -> list[str] | MaybeNone:
        """Returns a list of variables having either an attribute or in a group"""
        ...
    def getstrides(self, array: NDArray[Any], /) -> NDArray[intp]:
        """Returns the strides of the input array. The input must be an array (no lists or tuples)."""
        ...
    def printtypenum(self, array: NDArray[Any], /) -> None:
        """Prints the typenum of the array. The input must be an array (no lists or tuples)."""
        ...
    def feenableexcept(self, flag: bool | int, /) -> None:
        """Turns on or off trapping of floating point exceptions"""
        ...
