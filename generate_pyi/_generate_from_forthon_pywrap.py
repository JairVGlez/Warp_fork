"""
Generate stub files by scanning .v files using the PyWrap class from Forthon.
Has the advantage of not needing warp to built first, along with more information
and tools from the PyWrap class such as function arguments.
"""
from __future__ import annotations
import os
import sys

if len(sys.argv) <= 1:
    sys.argv.append("scan_v_file")
from Forthon.wrappergenerator import PyWrap
from Forthon.fvars import Fvars, Ftype, Fargs

import generate_allpyi as glib
from generate_allpyi import (
    PKGNAME, t, PkgInfo,
    scalar_getset_type_names,
    array_getset_type_names,
    format_Forthon_class_name,
    _pywarp90_path,
    format_docstring,
    format_attribute_as_field,
    format_attribute_as_property,
)

all_pywraps: dict[PKGNAME, PyWrap] = {}
all_slists: dict[PKGNAME, dict[str, Fvars]] = {}
all_alists: dict[PKGNAME, dict[str, Fvars]] = {}
all_flists: dict[PKGNAME, dict[str, Fvars]] = {}
all_typelists: dict[PKGNAME, dict[str, Ftype]] = {}

def scan_v_file(pkg_name: PKGNAME, info: PkgInfo):
    """
    Scan the {pkg_name}.v file to get the documentation and typing for the Forthon variables, classes, and functions.
    For functions, the improvement would be explicitly documenting their typed arguments.
    Currently the Forthon function arguments are simply hinted in .pyi files as *args,
    and the argument types are only given by the documentation.
    """
    varfile = os.path.join(_pywarp90_path(), f"{pkg_name}.v")

    pywrap = PyWrap(
        varfile=varfile,
        pkgname=pkg_name,
        pkgsuffix="",
        pkgbase="wrap",
    )

    all_pywraps[pkg_name] = pywrap
    all_slists[pkg_name] = { v.name: v for v in pywrap.slist }
    all_alists[pkg_name] = { v.name: v for v in pywrap.alist }
    all_flists[pkg_name] = { v.name: v for v in pywrap.flist }
    all_typelists[pkg_name] = { t.name: t for t in pywrap.typelist }

    info.pkg_typelist_dict[pkg_name] = [ t.name for t in pywrap.typelist ]

def write_package_from_v_file(
    pkg_name: PKGNAME,
    info: PkgInfo,
):
    pkg_import_dict = info.pkg_import_dict

    pywrap: PyWrap = all_pywraps[pkg_name]
    pkgmod_scalars: dict[str, Fvars] = all_slists[pkg_name]
    pkgmod_arrays: dict[str, Fvars] = all_alists[pkg_name]
    pkgmod_functions: dict[str, Fvars] = all_flists[pkg_name]
    pkgmod_forthon_types: dict[str, Ftype] = all_typelists[pkg_name]

    pkg_import_list: list[str] = []

    # Start .pyi text string
    txt: str = ""
    txt += glib.doc_and_imports_for_pkg_module(pkg_name, pkg_suffix='py').strip()
    txt += '\n'

    # Package module Forthon object
    txt += glib.txt_for_pkg_forthon_object(pkg_name)
    pkg_import_list.append(pkg_name)

    # Package module variables
    txt += "\nfcompname: str"
    pkg_import_list.append("fcompname")
    txt += "\nrealsize: int"
    pkg_import_list.append("realsize")
    txt += '\n'

    # Package module functions
    for func_name, f in pkgmod_functions.items():
        # Get argument and function doc strings
        args_str, func_doc = make_args_str_and_func_docstring(f)
        # Write function
        txt += f"\ndef {func_name}{args_str}:"
        txt += format_docstring(func_doc, nt=t, attr_category='method')
        pkg_import_list.append(func_name)
    txt += '\n'

    # Package error class
    txt += f"\nclass {pkg_name}error(Exception): ..."
    pkg_import_list.append(f"{pkg_name}error")
    txt += '\n'

    # Constructors for extra Forthon types
    for fname, f in pkgmod_forthon_types.items():
        forthon_type_name = format_Forthon_class_name(fname)

        # Constructor function for derived Forthon type
        constructor_func_doc = f"Creates a new instance of fortran derived type {fname}"
        txt += f"\ndef {fname}() -> {forthon_type_name}:"
        txt += format_docstring(constructor_func_doc, nt=t, attr_category='method')
        pkg_import_list.append(fname)

        # Class for derived Forthon type
        txt += glib.start_class_for_constructed_forthon_type(constructor_name=fname)
        class_varlist: list[Fvars] = f.vlist
        class_slist: list[Fvars] = []
        class_alist: list[Fvars] = []
        for v in class_varlist:
            if v.array:
                class_alist.append(v)
            else:
                class_slist.append(v)
        txt += write_class_attributes_from_varlists(scalars=class_slist, arrays=class_alist)
        txt += '\n'

    # Main package Forthon type
    txt += glib.start_class_for_pkg_forthon_type(pkg_name)
    txt += write_class_attributes_from_varlists(
        scalars=list(pkgmod_scalars.values()),
        arrays=list(pkgmod_arrays.values())
    )
    txt += '\n'

    # Write .pyi files
    glib.write_pkg_stubfiles(pkg_name=pkg_name, txt=txt)

    pkg_import_dict[pkg_name] = pkg_import_list

def make_args_str_and_func_docstring(f: Fvars) -> tuple[str, str]:
    args_str: str
    docstring: str

    arg_list: list[Fargs] = f.args
    arg_argname_dict: dict[Fargs, str] = { arg: arg.name for arg in arg_list }

    # Adjust arg names to avoid python conflicts, such as with keywords
    if glib.lfunction_args_explicit:
        for arg, argname in arg_argname_dict.items():
            arg_argname_dict[arg] = glib.adjust_name_to_avoid_python_conflicts(argname)

    l_nonzero_args: bool = (len(f.args) != 0)

    ### Set function arguments string
    if l_nonzero_args:
        if glib.lfunction_args_explicit:
            args_joined: str = ','.join(arg_argname_dict.values())
            args_str = f"({args_joined},/)"
        else:
            # Use generic (*args) for nonzero arguments
            args_str = "(*args)"
    else:
        # No arguments
        args_str = '()'

    ### Set function docstring
    if l_nonzero_args:
        if glib.ldoc_numpy_style_parameters:
            name_type_dict: dict[str, str] = make_argname_typestr_dict(arg_argname_dict)
            docstring  = f.comment
            docstring += glib.txt_for_numpy_style_parameters(name_type_dict)
        else:
            docstring = f"{f.name}{f.dimstring}\n{f.comment}"
    else:
        docstring = f.comment

    docstring = docstring.strip() + '\n'

    return args_str, docstring

def make_argname_typestr_dict(arg_argname_dict: dict[Fargs, str]) -> dict[str, str]:
    argname_typestr_dict: dict[str, str] = {}
    for arg, argname in arg_argname_dict.items():
        argtype_str: str = arg.type
        if arg.dimstring != "":
            argtype_str = f"{arg.type} array of shape {arg.dimstring}"
        argname_typestr_dict[argname] = argtype_str
    return argname_typestr_dict

def write_class_attributes_from_varlists(
    scalars: list[Fvars],
    arrays: list[Fvars],
) -> str:
    result: str = ""
    for v in scalars:
        var_name = v.name
        var_doc = v.comment
        scalar_get_type, scalar_set_type = scalar_getset_type_names(v.type)
        result += format_attribute_as_field(
            var_name=var_name, nt=t, doc=var_doc,
            get_var_types=scalar_get_type,
            l_self_prefix=False,
        )
    for v in arrays:
        var_name = v.name
        var_doc = v.comment
        array_get_type, array_set_type = array_getset_type_names(v.type)
        result += format_attribute_as_property(
            var_name=var_name, nt=t, doc=var_doc,
            get_var_types=array_get_type,
            set_var_types=array_set_type,
        )
    return result
