"""
Minimal stub package for `mistral_common`.

The upstream llama.cpp conversion script imports `mistral_common` to support
advanced tokenizer workflows. Our DPO deployment pipeline targets standard
LLaMA-style models, so the heavy dependency is not required.  The stub keeps a
compatible module layout so imports succeed without pulling the real package.

If a conversion path really needs the original features, raise a clear error to
guide the user to install the official library.
"""

