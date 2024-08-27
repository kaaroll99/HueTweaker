from msgspec import json, yaml


def load_yml(path):
    with open(path, 'rb') as file:
        output = yaml.decode(file.read())
    return output


def load_json(path):
    with open(path, 'rb') as file:
        output = json.decode(file.read())
    return output
