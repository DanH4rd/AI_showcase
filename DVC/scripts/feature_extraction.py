import pandas as pd
import os
import numpy as np
import time
import datetime
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

import yaml

split_path = './data/split/'
features_path = './data/features/'

files = os.listdir(split_path)

for file in files:
    if len(os.path.splitext(file)) > 1:
        if os.path.splitext(file)[1] == '.json':
            df = pd.read_json(os.path.join(split_path, file))

            df['summary_length'] = df['summary'].apply(lambda x: len(x) if x != None else 0)

            df['reviewText_length'] = df['reviewText'].apply(lambda x: len(x) if x != None else 0)


            df['year_period'] = df['reviewTime'].apply(lambda x: int(x.split(' ')[0]) if x != None else None)
            df['year_period'] = df['year_period'].apply(lambda x: None if x == None 
                                                        else 1 if (x >= 3 and x <=5) #spring
                                                        else 2 if (x >= 6 and x <=8) # summer
                                                        else 3 if (x >= 9 and x <=11) # autumn
                                                        else 4) # winter
            
            df['season_spring'] = df['year_period']
            df['season_spring'] = df['season_spring'].apply(lambda x: 1 if x == 1 else 0)

            df['season_summer'] = df['year_period']
            df['season_summer'] = df['season_summer'].apply(lambda x: 1 if x == 2 else 0)

            df['season_autumn'] = df['year_period']
            df['season_autumn'] = df['season_autumn'].apply(lambda x: 1 if x == 3 else 0)

            df['season_winter'] = df['year_period']
            df['season_winter'] = df['season_winter'].apply(lambda x: 1 if x == 4 else 0)

            df = df.drop(columns=['year_period'])

            df['category'] = df['category'].apply(lambda x: None if x == None 
                                                        else 1 if x == 'Software_5'
                                                        else 2 if x == 'All_Beauty_5'
                                                        else 3 if x == 'AMAZON_FASHION_5'
                                                        else 4) # Appliances_5
            
            df['cat_software'] = df['category']
            df['cat_software'] = df['cat_software'].apply(lambda x: 1 if x == 1 else 0)

            df['cat_beauty'] = df['category']
            df['cat_beauty'] = df['cat_beauty'].apply(lambda x: 1 if x == 2 else 0)

            df['cat_fashion'] = df['category']
            df['cat_fashion'] = df['cat_fashion'].apply(lambda x: 1 if x == 3 else 0)

            df['cat_appliances'] = df['category']
            df['cat_appliances'] = df['cat_appliances'].apply(lambda x: 1 if x == 4 else 0)

            df = df.drop(columns=['category'])
             
            drop_list = df.isna().sum(axis=0).to_frame().transpose() / df.shape[0] * 100 < 25
            notna_columns = drop_list[drop_list].dropna(axis=1).columns

            df = df[notna_columns]
            df = df.dropna()
            df = df.drop(columns=['reviewTime', 'reviewerID', 'asin', 'reviewerName', 'verified'])

            # df['unixReviewTime'] = (df['unixReviewTime'] - df['unixReviewTime'].mean()) / df['unixReviewTime'].std()
            # df['summary_length'] = (df['summary_length'] - df['summary_length'].mean()) / df['summary_length'].std()
            # df['reviewText_length'] = (df['reviewText_length'] - df['reviewText_length'].mean()) / df['reviewText_length'].std()

            df['text_data'] = df['summary'] + ' ' + df['reviewText']

            df = df.drop(columns=['summary', 'reviewText'])
     
            df.to_json(os.path.join(features_path, file))
