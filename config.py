import json


def get_tokens(keys: list[str]) -> list[str | None]:
    """Reads the tokens from the file and returns the requested keys.

    Args:
        keys: The keys of the tokens to retrieve.

    Returns:
        The values of the requested keys, in the same order as the input list.
        Any keys that are not found in the file will be returned as None.
    """
    with open("tokens.json") as f:
        tokens: dict[str, str] = json.load(f)
    return [tokens.get(key) for key in keys]


def set_tokens(updates: dict[str, str]) -> None:
    """Sets the tokens in the file.

    Args:
        updates: The updates to the tokens.
    """
    with open("tokens.json") as f:
        data = json.load(f)
    data.update(updates)
    with open("tokens.json", "w") as f:
        json.dump(data, f, indent=4)
