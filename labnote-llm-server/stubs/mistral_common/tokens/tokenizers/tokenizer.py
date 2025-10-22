def merge_tokenizer_configs(*args, **kwargs):
    raise RuntimeError(
        "'mistral_common' optional dependency required for merge_tokenizer_configs. "
        "Install the official mistral-common package to enable this feature."
    )


def tokenizer_train_and_save_from_config(*args, **kwargs):
    raise RuntimeError(
        "'mistral_common' optional dependency required for tokenizer_train_and_save_from_config. "
        "Install the official mistral-common package to enable this feature."
    )

