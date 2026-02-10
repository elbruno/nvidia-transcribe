"""Stub pynini package for Windows.

pynini depends on OpenFst C++ libraries that do not compile on Windows.
This stub satisfies the pip dependency so nemo_toolkit can be installed.
Text normalization features (nemo_text_processing) that rely on pynini
will raise an ImportError at runtime, but ASR and TTS work fine without it.
"""

from setuptools import setup, find_packages

setup(
    name="pynini",
    version="2.1.6.post1",
    description="Stub for pynini on Windows (OpenFst unavailable)",
    packages=find_packages(),
    python_requires=">=3.8",
)
