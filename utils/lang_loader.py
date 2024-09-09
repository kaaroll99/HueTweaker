from utils.data_loader import load_yml
from config import langs
import discord

def load_lang(locale: str):
    if locale in langs:
        return load_yml('lang/'+locale+'.yml')
    else:
        return load_yml('lang/en-US.yml')