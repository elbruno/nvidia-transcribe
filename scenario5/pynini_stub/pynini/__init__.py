"""Stub pynini module — pynini is not available on Windows.

The real pynini package wraps OpenFst and requires a C++ toolchain with
GCC/Clang flags that are incompatible with MSVC.  This stub lets
nemo_toolkit install successfully; text normalization features that
depend on pynini will raise an ImportError at runtime.
"""

raise ImportError(
    "pynini is not available on Windows. "
    "NeMo text normalization (ITN) features are disabled. "
    "ASR and TTS models work without it."
)
