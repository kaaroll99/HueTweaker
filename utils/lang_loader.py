from config import langs
from utils.data_loader import load_yml


def load_lang(locale: str):
    if locale in langs:
        return load_yml('lang/' + locale + '.yml')
    else:
        return
