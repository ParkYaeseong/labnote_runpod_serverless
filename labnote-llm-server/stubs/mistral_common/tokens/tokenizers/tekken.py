def _missing(name: str) -> None:
    raise RuntimeError(
        f"'mistral_common' optional dependency required for {name}. "
        "Install the official mistral-common package to enable this feature."
    )


class Tekkenizer:
    def __init__(self, *args, **kwargs):
        _missing("Tekkenizer")

