from googletrans import Translator as gtran


def translate(text, to_lang, from_lang=None):
    translator = gtran()
    diff_lang = False
    for word in text.split():
        if translator.detect(word).lang != from_lang:
            diff_lang = True
            break
    
    if from_lang is None or diff_lang:
        return translator.translate(text, dest=to_lang).text
    else:
        return translator.translate(text, dest=to_lang, src=from_lang).text