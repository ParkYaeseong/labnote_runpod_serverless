def adjust_tokenizer_levels(*args, **kwargs):
    raise RuntimeError(
        "'mistral_common' optional dependency required for adjust_tokenizer_levels. "
        "Install the official mistral-common package to enable this feature."
    )


def filter_valid_tokenizer_files(*args, **kwargs):
    raise RuntimeError(
        "'mistral_common' optional dependency required for filter_valid_tokenizer_files. "
        "Install the official mistral-common package to enable this feature."
    )

