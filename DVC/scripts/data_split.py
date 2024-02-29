import pandas as pd
import os
from sklearn.model_selection import train_test_split

import yaml

params = yaml.safe_load(open("params.yaml"))["split_and_vocab"]

test_size = params['test_size']
random_state = params['random_state']
stratification = params['stratification']

preprocessed_path = './data/preprocessed data/'
split_path = './data/split/'
data_path = './data/'

file_name = 'Amazon.json'

train_file_name = 'Amazon_train.json'
test_file_name = 'Amazon_test.json'

df = pd.read_json(os.path.join(preprocessed_path, file_name))

df_train, df_test = train_test_split(df, test_size=test_size, random_state=random_state, stratify= df.iloc[:, 0] if stratification else None)

df_train.to_json(os.path.join(split_path, train_file_name))
df_test.to_json(os.path.join(split_path, test_file_name))
