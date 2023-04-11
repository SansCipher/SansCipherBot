import json


# _data() -> dict[str, str]
# This auxiliary function gets the contents of tokens.json as a dictionary


def _data() -> dict[str, str]:
    try:
        with open("tokens.json") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print("tokens.json file not found")
        raise


# get_tokens(keys: list[str]) -> list[str]
# This function takes a list of keys for tokens.json files and returns a list of values corresponding to those keys


def get_tokens(keys: list[str]) -> list[str]:
    data = _data()
    return [data.get(key, None) for key in keys]


# set_tokens(updates: dict[str, str]) -> None:
# This function takes a dict of key value pairs and sets the tokens.json file to be those values.


def set_tokens(updates: dict[str, str]) -> None:
    data = _data()
    data.update(updates)
    with open("tokens.json", "w") as f:
        json.dump(data, f, indent=4)
