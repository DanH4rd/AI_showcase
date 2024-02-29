import pandas as pd
import os
import numpy as np
import json
import yaml
import spacy

source_path = './data/source/'

files = os.listdir(source_path)

preprocessed_path = './data/preprocessed data/'

df = pd.DataFrame()

for file in files:
     if len(os.path.splitext(file)) > 1:
        if os.path.splitext(file)[1] == '.json':
            file_path = os.path.join(source_path, file).replace('\\', '/')
            df_buffer = pd.read_json(file_path, lines=True)
            df_buffer['category'] = os.path.splitext(os.path.basename(file_path))[0]
            # df_buffer['overall'] = df_buffer['overall'].apply(lambda x: 'negative' if x < 3 else "neutral" if x < 5 else "positive")
            df = pd.concat([df, df_buffer], ignore_index=True)

df = df.rename(columns={'style' : 'aaa'})

new_attrs = set([elem[0] for elem in [list(item.keys()) for item in df['aaa'].values if isinstance(item, dict)]])

for attr in new_attrs:
    df[(attr[0:-1]).lower()] = [item.get(attr, np.nan) if isinstance(item, dict) else np.nan for item in df['aaa'].values]

# df = df.drop(columns='aaa')
df = df.rename(columns={'aaa' : 'style_list'})

nlp = spacy.load("en_core_web_sm")

non_emotional = ["DET", "PRON", "CCONJ", "PUNCT", "SYM", "NUM"]

def preprocess_text(text):
    doc = nlp(text)
    tokens = [token.lemma_ for token in doc if not token.is_stop and token.pos_ not in non_emotional]
    preprocessed_text = " ".join(tokens)
    return preprocessed_text

df['summary'] = df['summary'].to_frame().apply(lambda x: preprocess_text(x[0].lower()) if isinstance(x[0], str) else x[0], axis = 1)

df['reviewText'] = df['reviewText'].to_frame().apply(lambda x: preprocess_text(x[0].lower()) if isinstance(x[0], str) else x[0], axis = 1)

df.to_json(os.path.join(preprocessed_path, 'Amazon.json'))
