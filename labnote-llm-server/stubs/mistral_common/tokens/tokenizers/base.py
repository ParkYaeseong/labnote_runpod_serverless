from enum import Enum


class TokenizerVersion(Enum):
    """
    Minimal enum that mirrors the identifiers accessed by llama.cpp.

    The conversion script only needs the enum values to exist; the actual
    implementation details live in the real mistral_common package.
    """

    v1 = 1
    v3 = 3
    v7 = 7
    v11 = 11
    v13 = 13

