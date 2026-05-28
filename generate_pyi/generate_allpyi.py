"""
Generate stub files for Warp. Use by calling `python3 generate_allpyi.py`.
"""
from __future__ import annotations

from typing import Literal, Final
import os
import re
import keyword

forthon_typing_module_name = "_forthon_typing"
forthon_object_class_name = "ForthonObject"

# Directory paths
warp_repo_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Options
luse_lparallel_in_import_file: bool = False
luse_typing_TYPE_CHECKING_in_import_file: bool = True
lgenerate_parallel_pyi: bool = True
luse_v_files: bool = True # Using .v files is preferred
lfunction_args_explicit: bool = False
ldoc_numpy_style_parameters: bool = False
ldebug: bool = True

import_script_filename = "_fortran_imports.py"
warp_typing_dir_name = ""

# Constants
t: Final = "    " # single tab, use 4 spaces for indentation
PKGNAME = Literal[
    "top",
    "env",
    "w3d",
    "f3d",
    "fxy",
    "wxy",
    "frz",
    "wrz",
    "cir",
    "her",
    "cho",
    "em3d",
]
pkg_list: list[PKGNAME] = list(PKGNAME.__args__)

pkg_obj_docs: dict[PKGNAME, str] = {
    "top": "TOP - all variables and code which are needed by more than one package.\
        \nThese common blocks are available to all packages.",
    "env": "Envelope code.\
        \nEnvelope data generated from this package can be used in WARP3d.",
    "w3d": "PIC package of 3D particle code.",
    "wxy": "PIC package of XY particle code.",
    "wrz": "PIC package of RZ particle code.",
    "f3d": "3D fieldsolver package and test driver.",
    "fxy": "XY fieldsolver package and test driver.",
    "frz": "RZ fieldsolver package and test driver.",
    "cir": "CIRCE envelope/fluid model.",
    "her": "HERMES envelope/fluid model.",
    "cho": "Chombo/AMR fieldsolver interface.",
    "em3d": "3D EM solver.",
}

# Package information
class PkgInfo:
    pkg_import_dict: dict[PKGNAME, list[str]] = {}
    pkg_typelist_dict: dict[PKGNAME, list[str]] = {}
    warpC_import_list: list[str] = []
    warpC_variable_type_dict: dict[str, str] = {}

# Array get/set types
bytes_array_get_type = "NDArray[bytes_]"
complex_array_get_type = "NDArray[complex128]"
float_array_get_type = "NDArray[float64]"
int_array_get_type = "NDArray[int64]"

bytes_array_set_type = "_ArrayBytes_co"
complex_array_set_type = "_ArrayLikeComplex_co"
float_array_set_type = "_ArrayLikeFloat_co"
int_array_set_type = "_ArrayLikeInt_co"

# Paths
def _pywarp90_path():
    return os.path.join(warp_repo_path, "pywarp90")
def _scripts_path():
    return os.path.join(warp_repo_path, "scripts")
def _generate_pyi_path():
    return os.path.join(warp_repo_path, "generate_pyi")
def _debug_dirpath():
    return os.path.join(warp_repo_path, "..", "warp-pyi-debug")
def _scripts_typing_path():
    return os.path.join(_scripts_path(), warp_typing_dir_name)
def _typing_python_path_str():
    return "." if warp_typing_dir_name == "" else f".{warp_typing_dir_name}."

# Import text
def imports_for_pkg_module(pkg_name: PKGNAME):
    typing_python_path = _typing_python_path_str()
    forthon_typing_python_path = f"{typing_python_path}{forthon_typing_module_name}"

    txt: str = ""
    txt += "\n" + f"""
from typing import Any, type_check_only, TypeAlias
from numpy import bytes_, complex128, float64, int64
from numpy.typing import NDArray
from {forthon_typing_python_path} import (
    {forthon_object_class_name},
    {bytes_array_set_type},
    {complex_array_set_type},
    {float_array_set_type},
    {int_array_set_type},
)
    """.strip()
    if pkg_name == 'w3d':
        forthorn_particle_group = format_Forthon_class_name("ParticleGroup")
        txt += f"\nfrom .toppy import {forthorn_particle_group}"
    return txt

# Start text for pkg module stub file
def doc_and_imports_for_pkg_module(pkg_name: PKGNAME, pkg_suffix: str):
    txt: str = ""
    txt += doc_for_pkg_module(pkg_name, pkg_suffix=pkg_suffix)
    txt += imports_for_pkg_module(pkg_name)
    txt = txt.strip()
    return txt

def format_Forthon_class_name(class_name: str) -> str:
    return f"_Forthon_{class_name}"

def format_docstring(
    doc: str | None,
    *,
    nt: str,
    attr_category: Literal['method', 'property', 'field'],
    ladd_type_ignore: bool = False,
) -> str:
    """Format a docstring for use in python with consistent indentation and removing empty lines."""
    result: str = ''
    result_lines: list[str] = []

    if doc is None:
        doc = ""

    doc_striped = doc.strip()
    doc_lines: list[str] = doc_striped.splitlines()

    result_lines.append('')
    if len(doc_lines) == 0:
        pass
    elif len(doc_lines) == 1:
        # Use triple double quotes even for single line doc strings (PEP 257 - Docstring Conversions)
        result_lines.append(f'"""{doc_lines[0]}"""')
    elif len(doc_lines) > 1:
        result_lines.append('"""')
        result_lines.extend(doc_lines)
        result_lines.append('"""')

    if attr_category == 'method' or attr_category == 'property':
        # For methods and properties
        if len(doc_lines) == 0:
            result_lines[0] = ' ...'
        elif len(doc_lines) >= 1:
            result_lines.append('...')
    elif attr_category == 'field':
        # For field attributes
        pass

    # Add type ignore to first line
    if ladd_type_ignore:
        result_lines[0] += " # type: ignore"

    for i, line in enumerate(result_lines):
        if line.strip() == "":
            result_lines[i] = ""
        elif i > 0:
            # Indent non-empty lines
            result_lines[i] = nt + line.rstrip()

    result = ('\n').join(result_lines)

    return result

def var_getset_type_names(pkg_vartype: str):
    scalar_get_type: str
    scalar_set_type: str
    array_get_type: str
    array_set_type: str
    if pkg_vartype == "Any":
        scalar_get_type = "Any"
        scalar_set_type = "Any"
        array_get_type = "NDArray[Any]"
        array_set_type = "Any"
    elif pkg_vartype in ["integer", "logical", "int"]:
        scalar_get_type = 'int'
        scalar_set_type = 'int'
        array_get_type = str(int_array_get_type)
        array_set_type = str(int_array_set_type)
    elif pkg_vartype in ["double", "real", "float"]:
        scalar_get_type = 'float'
        scalar_set_type = 'float'
        array_get_type = str(float_array_get_type)
        array_set_type = str(float_array_set_type)
    elif "complex" in pkg_vartype:
        scalar_get_type = 'complex'
        scalar_set_type = 'complex'
        array_get_type = str(complex_array_get_type)
        array_set_type = str(complex_array_set_type)
    elif "character" in pkg_vartype:
        scalar_get_type = 'str'
        scalar_set_type = 'str'
        array_get_type = str(bytes_array_get_type)
        array_set_type = str(bytes_array_set_type)
    else:
        scalar_get_type = format_Forthon_class_name(pkg_vartype)
        scalar_set_type = scalar_get_type
        array_get_type = "NDArray[Any]"
        array_set_type = "Any"

    return scalar_get_type, scalar_set_type, array_get_type, array_set_type

def scalar_getset_type_names(pkg_vartype: str) -> tuple[str, str]:
    scalar_get_type, scalar_set_type, _1, _2 = var_getset_type_names(pkg_vartype)
    return scalar_get_type, scalar_set_type

def array_getset_type_names(pkg_vartype: str) -> tuple[str, str]:
    _1, _2, array_get_type, array_set_type = var_getset_type_names(pkg_vartype)
    return array_get_type, array_set_type

def format_attribute_as_property(
    var_name: str,
    *,
    nt: str,
    doc: str | None,
    get_var_types: str,
    set_var_types: str,
) -> str:
    ladd_type_ignore = get_var_types != set_var_types
    result: str = ""
    result += f"\n{nt}@property"
    result += f"\n{nt}def {var_name}(self) -> {get_var_types}: ..."
    result += f"\n{nt}@{var_name}.setter"
    result += f"\n{nt}def {var_name}(self, value: {set_var_types}) -> None:"
    result += format_docstring(doc, nt=nt+t, attr_category='property', ladd_type_ignore=ladd_type_ignore)
    return result

def format_attribute_as_field(
    var_name: str,
    *,
    nt: str,
    doc: str,
    get_var_types: str,
    l_self_prefix: bool = False,
) -> str:
    result: str = ""
    field_name = f"self.{var_name}" if l_self_prefix else var_name
    field_nt = t + nt if l_self_prefix else nt
    result += f"\n{field_nt}{field_name}: {get_var_types}"
    result += format_docstring(doc, nt=field_nt, attr_category='field')
    return result

def adjust_name_to_avoid_python_conflicts(name: str) -> str:
    # Avoid keywords
    l_keyword: bool = keyword.iskeyword(name)
    # Avoid other names
    other_names_to_avoid: list[str] = [""]
    l_other: bool = (name in other_names_to_avoid)
    # Rename argument name
    if l_keyword or l_other:
        name = f"{name}_"
    return name

def txt_for_numpy_style_parameters(name_type_dict: dict[str, str]):
    result: str = ""
    result += "\n"
    result += "\nParameters"
    result += "\n----------"
    for name, typestr in name_type_dict.items():
        result += f"\n{name} : {typestr}"
    return result

def doc_for_pkg_module(
    pkg_name: PKGNAME,
    pkg_suffix: str = '',
) -> str:
    """Get doc from .v file. Adapted from `Forthon.interfaceparser.processfile`."""
    result: str = ""
    result_lines: list[str] = []

    # Read in the whole thing
    # (Make sure that there is a newline character at the end)
    with open(os.path.join(_pywarp90_path(), f"{pkg_name}.v")) as varfile:
        text = varfile.read() + '\n'

    # Get the package name (first line of file) and strip it from the text
    m = re.search('[\n \t#]', text)
    i = m.start() if m else 0
    line = text[:i]
    text = text[i+1:].strip()

    # Check to make sure that the package name is correct
    if pkg_name != line:
        print("""

    Warning: the package name in the file does not agree
    with the file name. Make sure that the first line of the
    variable description file is the package name.
    file name = %r
    packagename = %r

    One possible reason this error is that the variable description
    file is in dos format. If this is so, change the format to match
    your system. (This can be done in vi by opening the file and
    typing ":set fileformat=unix" and then saving the file.)

    """%(pkg_name, line))
        return ""

    # Remove all line continuation marks
    text = re.sub('\\\\', '', text)

    # Get rid of any initial comments and blank lines
    while len(text) > 0 and text[0] == '#':
        m = re.search('\n', text)
        if m:
            i = m.start()
            # Remove # and whitespace from docline
            docline = text[0:i].strip('#').strip()
            result_lines.append(docline)
            # Remove docline from text
            text = text[i+1:].strip()
        else:
            break

    docstring  = f"{pkg_name}{pkg_suffix} module"
    docstring += "\n==="
    docstring += "\n" + "\n\n".join(result_lines)

    result = format_docstring(doc=docstring, nt='', attr_category='field')

    result = result.strip()

    return result

def txt_for_pkg_forthon_object(pkg_name: PKGNAME) -> str:
    result: str = ""
    pkg_forthon_type_name = format_Forthon_class_name(pkg_name)
    result = f"\n{pkg_name}: {pkg_forthon_type_name}"
    result += doc_for_pkg_forthon_object(pkg_name)
    return result

def doc_for_pkg_forthon_object(pkg_name: PKGNAME) -> str:
    docstring: str = ""
    # docstring += f"Forthon object warp.{pkg_name}: "
    docstring += f"{pkg_obj_docs[pkg_name]}"
    return format_docstring(doc=docstring, nt='', attr_category='field')

def start_class_for_constructed_forthon_type(constructor_name: str) -> str:
    class_name = format_Forthon_class_name(constructor_name)
    result: str = ""
    result += f"\n@type_check_only"
    result += f"\nclass {class_name}({forthon_object_class_name}):"
    result += format_docstring(doc=f"""\
Forthon derived type of instances made by the `{constructor_name}()` constructor.
This class is for type checking only.
""", nt=t, attr_category='field')
    return result

def start_class_for_pkg_forthon_type(pkg_name: PKGNAME) -> str:
    class_name = format_Forthon_class_name(pkg_name)
    result: str = ""
    result += f"\n@type_check_only"
    result += f"\nclass {class_name}({forthon_object_class_name}):"
    result += format_docstring(doc=f"""\
Forthon type of the singleton object `{pkg_name}`.
This class is for type checking only.
""", nt=t, attr_category='field')
    return result

def write_pkg_stubfiles(*, pkg_name: PKGNAME, txt: str) -> None:
    # print("")
    dirpath = _scripts_path()
    txt = txt.strip() + '\n'
    filename = f"{pkg_name}py.pyi"
    write_txt_to_file(txt=txt, dirpath=dirpath, filename=filename)
    if lgenerate_parallel_pyi:
        txt = doc_for_pkg_module(pkg_name, pkg_suffix='parallelpy')
        txt += f"\nfrom .{pkg_name}py import *"
        txt = txt.strip() + '\n'
        filename = f"{pkg_name}parallelpy.pyi"
        write_txt_to_file(txt=txt, dirpath=dirpath, filename=filename)
    # print("")

def doc_for_warpC(lparallel: bool) -> str:
    warpCname = "warpCparallel" if lparallel else "warpC"
    doc = f'"""{warpCname} module"""'
    return doc

def collect_warpC_info(info: PkgInfo):
    info.warpC_variable_type_dict = {
        "commithash": "str",
        "localdate": "str",
        "origindate": "str",
    }

def txt_for_warpC(info: PkgInfo, lparallel: bool) -> str:
    txt: str = ""
    # Documentation
    txt += doc_for_warpC(lparallel=lparallel)
    # Module variables
    for var_name, var_type in info.warpC_variable_type_dict.items():
        txt += f"\n{var_name}: {var_type}"
        info.warpC_import_list.append(var_name)
    # Error class
    txt += "\nclass error(Exception): ..."
    info.warpC_import_list.append("error")
    # Strip
    txt = txt.strip() + '\n'
    return txt

def write_warpC(info: PkgInfo) -> None:
    # print("")
    dirpath = _scripts_path()
    txt = txt_for_warpC(info, lparallel=False)
    write_txt_to_file(txt=txt, dirpath=dirpath, filename="warpC.pyi")
    if lgenerate_parallel_pyi:
        txt = ""
        txt += doc_for_warpC(lparallel=True)
        txt += f"\nfrom .warpC import *"
        txt = txt.strip() + '\n'
        write_txt_to_file(txt=txt, dirpath=dirpath, filename="warpCparallel.pyi")
    # print("")

def write_import_file(info: PkgInfo) -> None:
    pkg_import_dict = info.pkg_import_dict
    warpC_import_list = info.warpC_import_list
    dirpath = os.path.join(_scripts_path(), warp_typing_dir_name)
    forthon_pyi_relative_import_path = _typing_python_path_str()
    itxt = ""
    itxt += '"""Type checking only. Explicit imports from stub files to help type checkers."""'
    tTC = t if luse_typing_TYPE_CHECKING_in_import_file else ""
    tpy = t if luse_lparallel_in_import_file else ""
    if luse_lparallel_in_import_file:
        itxt += f"\nfrom warp_parallel import lparallel"
    if luse_typing_TYPE_CHECKING_in_import_file:
        itxt += f"\nimport typing"
        itxt += f"\nif typing.TYPE_CHECKING:"
    if luse_lparallel_in_import_file:
        itxt += f"\n"
        # if lparallel = True
        itxt += f"\n{tTC}if lparallel:"
        # Import from warpCparallel
        itxt += f"\n{tTC}{t}from {forthon_pyi_relative_import_path}warpCparallel import ("
        for var_name in warpC_import_list:
            itxt += f"\n{tTC}{t}{t}{var_name},"
        itxt += f"\n{tTC}{t})"
        # Import from {pkg}parallelpy
        for pkg_name in pkg_list:
            itxt += f"\n{tTC}{t}from {forthon_pyi_relative_import_path}{pkg_name}parallelpy import ("
            for var_name in pkg_import_dict[pkg_name]:
                itxt += f"\n{tTC}{t}{t}{var_name},"
            itxt += f"\n{tTC}{t})"
        # else lparallel = False
        itxt += f"\n{tTC}else:"
    # Import from warpC
    itxt += f"\n{tTC}{tpy}from {forthon_pyi_relative_import_path}warpC import ("
    for var_name in warpC_import_list:
        itxt += f"\n{tTC}{tpy}{t}{var_name},"
    itxt += f"\n{tTC}{tpy})"
    # Import from {pkg}py
    for pkg_name in pkg_list:
        itxt += f"\n{tTC}{tpy}from {forthon_pyi_relative_import_path}{pkg_name}py import ("
        for var_name in pkg_import_dict[pkg_name]:
            itxt += f"\n{tTC}{tpy}{t}{var_name},"
        itxt += f"\n{tTC}{tpy})"

    itxt = itxt.strip() + '\n'
    write_txt_to_file(txt=itxt, dirpath=dirpath, filename=import_script_filename)

def write_txt_to_file(*, txt: str, dirpath: str, filename: str) -> None:
    print(f"writing {filename}")
    # Write file to dirpath
    with open(os.path.join(dirpath, filename), 'w') as fw:
        fw.write(txt)
    if ldebug and os.path.exists(_debug_dirpath()):
        # Write copy of file for dev/debug purposes
        # print("Writing to debug path")
        with open(os.path.join(_debug_dirpath(), filename), 'w') as fw:
            fw.write(txt)

def copy_forthon_typing_file():
    filename = f"{forthon_typing_module_name}.py"
    src = os.path.join(_generate_pyi_path(), filename)
    dst = os.path.join(_scripts_typing_path(), filename)
    os.system(f'cp -f "{src}" "{dst}"')
    if ldebug:
        dst = os.path.join(_debug_dirpath(), filename)
        os.system(f'cp -f "{src}" "{dst}"')

def main():
    # print("")
    print("generating stub and type checking files")
    info = PkgInfo()
    # Write stub files
    if luse_v_files:
        import _generate_from_forthon_pywrap as _gf
        # Collect information
        collect_warpC_info(info)
        for pkg_name in pkg_list:
            _gf.scan_v_file(pkg_name, info)
        # Write packages
        write_warpC(info)
        for pkg_name in pkg_list:
            _gf.write_package_from_v_file(pkg_name, info)
    else:
        import _generate_from_warp as _gw
        # Collect information
        _gw.scan_warpC(info)
        # Write packages
        for pkg_name in pkg_list:
            _gw.write_package_from_warp_objects(pkg_name, info)
        write_warpC(info)
    # Write type checking files
    write_import_file(info)
    copy_forthon_typing_file()
    # print("")

if __name__ == '__main__':
    main()
