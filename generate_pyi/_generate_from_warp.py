"""
Generate stub files by importing warp and uses Forthon methods to extract info from the package objects.
This module is considered obselete and less than ideal as it requires warp to be compiled first.
"""
from __future__ import annotations
import typing
from typing import Any, Callable
import types
import re
import traceback

import generate_allpyi as glib
from generate_allpyi import (
    PKGNAME, t, PkgInfo,
    forthon_object_class_name,
    format_attribute_as_field,
    format_attribute_as_property,
    format_Forthon_class_name,
    format_docstring,
)

# Import warp
import warp

warpC_dict: dict[str, Any] = {}
all_functions: dict[PKGNAME, dict[str, Callable]] = {}
all_forthon_classes: dict[PKGNAME, dict[str, Callable]] = {}
all_othertypes: dict[PKGNAME, dict[str, type]] = {}
all_variables: dict[PKGNAME, dict[str, Any]] = {}

# Forthon typing
if typing.TYPE_CHECKING:
    from _forthon_typing import ForthonObject as ForthonObject

def format_pkg_var_attr(
    forthon_obj: 'ForthonObject',
    var_name: str,
    *,
    nt: str,
    module_name: PKGNAME,
    l_format_as_property: bool = False,
    l_self_prefix: bool = False,
) -> str:
    functionprintlabel = f"format_pkg_var_attr: forthon_obj = {forthon_obj.name()}, module_name = {module_name}, var_name = {var_name}"

    result: str = ''

    pkg_listvar: str = ""
    pkg_vartype: str | None = ""

    scalar_type_name: str = "Any"

    larray = False

    array_type_name: str = 'numpy.ndarray'
    array_set_types: str = 'Any'

    doc: str | None = ""

    try:
        pkg_listvar = forthon_obj.listvar(var_name)
        pkg_vartype = forthon_obj.getvartype(var_name)
        larray = "Dimension:" in pkg_listvar
        doc = forthon_obj.getvardoc(var_name)

    except Exception as e:
        print(f"Exception in {functionprintlabel} from listvar, getvartype, getvardoc:", e)
        traceback.print_exc()
        e_txt = repr(e)
        pkg_vartype = "Any"
        if "Array" in e_txt:
            scalar_type_name = "Any"
            larray = True
        elif "variable" in e_txt:
            scalar_type_name = "Any"
            larray = False

    if pkg_vartype is None:
        # forthon_obj.getvartype(var_name) returns None for callable objects such as classes and functions
        # print(f"{functionprintlabel}: pkg_vartype is None")

        scalar_type_name = forthon_object_class_name
        larray = False

        var_possible_classes: list[str] = []

        for other_mod_name, other_mod_class_dict in all_forthon_classes.items():
            for class_name, class_init in other_mod_class_dict.items():
                try:
                    setattr(forthon_obj, var_name, class_init())
                    forthon_class_name = format_Forthon_class_name(class_name)
                    var_possible_classes.append(forthon_class_name)
                    if other_mod_name != module_name:
                        print(f"{functionprintlabel}: need to import class {forthon_class_name} from module {other_mod_name}")
                except Exception as e:
                    pass

        if len(var_possible_classes) > 0:
            scalar_type_name = ' | '.join(var_possible_classes)

        if len(var_possible_classes) != 1:
            print(f"{functionprintlabel}: Could not find exactly 1 type, var_possible_classes = {var_possible_classes}")

    else:
        scalar_type_name, _, array_type_name, array_set_types = glib.var_getset_type_names(pkg_vartype)

    if larray:
        get_var_types = array_type_name
        set_var_types = array_set_types
    else:
        get_var_types = scalar_type_name
        set_var_types = scalar_type_name

    if l_format_as_property or larray:
        result += format_attribute_as_property(
            var_name=var_name, nt=nt, doc=doc,
            get_var_types=get_var_types, set_var_types=set_var_types,
        )
    else:
        result += format_attribute_as_field(
            var_name=var_name, nt=nt, doc=doc,
            get_var_types=get_var_types, l_self_prefix=l_self_prefix,
        )

    return result

def scan_warpC(info: PkgInfo):
    if warp.me != 0:
        return
    warpCmodule: types.ModuleType
    warpCmodule = warp.warpC if hasattr(warp, "warpC") else warp.warpCparallel
    warpC_dict = warpCmodule.__dict__
    for var_name, var_value in warpC_dict.items():
        if var_name.startswith('__'):
            continue
        info.warpC_variable_type_dict[var_name] = type(var_value).__name__

def write_package_from_warp_objects(
    pkg_name: PKGNAME,
    info: PkgInfo,
):
    pkg_import_dict: dict[PKGNAME, list[str]] = info.pkg_import_dict
    if warp.me != 0:
        return

    pkg_import_list: list[str] = []

    print(f"write_package({pkg_name}): start")

    pkg: 'ForthonObject' = getattr(warp, pkg_name)
    pkgmod: types.ModuleType
    if hasattr(warp, pkg_name+'py'):
        pkgmod = getattr(warp, pkg_name+'py')
    else:
        pkgmod = getattr(warp, pkg_name+'parallelpy')

    print(f"write_package({pkg_name}): pkgmod.__name__ = {pkgmod.__name__}")

    pkgmod_dict: dict[str, Any] = pkgmod.__dict__

    pkg_forthon_typename = f"_Forthon_{pkg_name}"

    pkgmod_functions: dict[str, Callable] = {}
    pkgmod_forthon_classes: dict[str, Callable] = {}
    pkgmod_othertypes: dict[str, type] = {}
    pkgmod_variables: dict[str, Any] = {}

    for attr_name, attr_obj in pkgmod_dict.items():
        if callable(attr_obj):
            func_doc = attr_obj.__doc__
            if func_doc is None:
                func_doc = ""
            m = re.search(r'Creates a new instance of fortran derived type (.*)', func_doc)
            if m:
                pkgmod_forthon_classes[attr_name] = attr_obj
            elif isinstance(attr_obj, type):
                pkgmod_othertypes[attr_name] = attr_obj
            else:
                pkgmod_functions[attr_name] = attr_obj
        else:
            pkgmod_variables[attr_name] = attr_obj

    all_functions[pkg_name] = pkgmod_functions
    all_forthon_classes[pkg_name] = pkgmod_forthon_classes
    all_othertypes[pkg_name] = pkgmod_othertypes
    all_variables[pkg_name] = pkgmod_variables

    # Start .pyi text string
    txt  = glib.doc_and_imports_for_pkg_module(pkg_name, pkg_suffix='py').strip()
    txt += '\n'

    # Package module Forthon object
    txt += glib.txt_for_pkg_forthon_object(pkg_name=pkg_name)
    pkg_import_list.append(pkg_name)

    # Package module variables
    for var_name, var_value in pkgmod_variables.items():
        if var_name.startswith('__'):
            continue
        if var_name == pkg_name:
            continue
        txt += f"\n{var_name}: {type(var_value).__name__}"
        pkg_import_list.append(var_name)
    txt += '\n'

    # Package module functions
    for func_name, func in pkgmod_functions.items():
        func_doc = func.__doc__

        txt += f"\ndef {func_name}(*args):"
        txt += format_docstring(func_doc, nt=t, attr_category='method')
        pkg_import_list.append(func_name)
    txt += '\n'

    # Package module other types:
    for type_name, type_obj in pkgmod_othertypes.items():
        inherit_str = ','.join(b.__name__ for b in type_obj.__bases__)
        if inherit_str != "":
            inherit_str = '('+inherit_str+')'
        txt += f"\nclass {type_name}{inherit_str}: ..."
    txt += '\n'

    # Constructors for extra Forthon types
    for construct_func_name, construct_func in pkgmod_forthon_classes.items():
        constructor_doc = construct_func.__doc__
        forthon_type_name = format_Forthon_class_name(construct_func_name)

        txt += f"\ndef {construct_func_name}() -> {forthon_type_name}:"
        txt += format_docstring(constructor_doc, nt=t, attr_category='method')
        pkg_import_list.append(construct_func_name)

        txt += f"\nclass {forthon_type_name}({forthon_object_class_name}):"
        try:
            obj_inst: 'ForthonObject' = construct_func()
            for var_name in obj_inst.varlist():
                txt += format_pkg_var_attr(obj_inst, var_name, nt=t, module_name=pkg_name)
            txt += '\n'
        except Exception as e:
            print(f"Exception for {pkg_name}.{construct_func_name}:", e)
            traceback.print_exc()
        continue

    # Main package Forthon type
    txt += glib.start_class_for_pkg_forthon_type(pkg_name)
    for var_name in pkg.varlist():
        txt += format_pkg_var_attr(pkg, var_name, nt=t, module_name=pkg_name)
    txt += '\n'

    # Write .pyi files
    glib.write_pkg_stubfiles(pkg_name=pkg_name, txt=txt)

    pkg_import_dict[pkg_name] = pkg_import_list
