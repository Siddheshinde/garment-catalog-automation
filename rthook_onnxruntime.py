import os
import sys
import ctypes

if hasattr(sys, "_MEIPASS"):
    meipass = sys._MEIPASS
    ort_capi = os.path.join(meipass, "onnxruntime", "capi")

    # Add every relevant dir to the DLL search path
    for d in [meipass, ort_capi]:
        if os.path.isdir(d):
            os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")
            if hasattr(os, "add_dll_directory"):
                os.add_dll_directory(d)

    # Pre-load in dependency order so Windows finds them before onnxruntime's
    # pybind extension tries to implicitly link against them
    for dll in ["onnxruntime_providers_shared.dll", "onnxruntime.dll"]:
        dll_path = os.path.join(ort_capi, dll)
        if os.path.isfile(dll_path):
            try:
                ctypes.CDLL(dll_path)
            except OSError:
                pass
