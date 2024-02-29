from scipy import spatial
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


class RecommendationSystem:

    def __init__(self, usr_repr, obj_metadata, usr_metadata, obj_embeds) -> None:
        self.usr_repr = usr_repr
        self.obj_metadata = obj_metadata
        self.usr_metadata = usr_metadata
        self.obj_embeds = obj_embeds

        self.usr_metadata = self.usr_metadata[self.usr_metadata['reviewerID'].isin(self.usr_repr.index)]

        self.usr_obj_mat = self.usr_metadata.pivot_table(index='reviewerID', columns='asin', values='overall')
        self.usr_obj_mat =  self.usr_obj_mat.fillna(0)

    def getTopObjects(self, matrix_df) -> list:
        return matrix_df.sum().to_frame().sort_values(by=0, ascending=False).index.to_list()

    def recommend(self, usersers, n, user_prod_matrix = False, metric = spatial.distance.cosine, contentFilter = False, similarityLimit = 0., date = None):

        season = None

        if date:
            season = get_season(date)

        ranking = self.getObjectRanking(usersers, metric, contentFilter, season)

        if similarityLimit == 0.:
            return ranking[:n]
        
        diverse_ranking = [ranking[0]]
        pointer = 1
        while len(diverse_ranking) < n and pointer < len(ranking):
            next_obj = ranking[pointer]
            diff = metric(self.obj_embeds[diverse_ranking[-1]], self.obj_embeds[next_obj])
            if diff < similarityLimit:
                diverse_ranking.append(next_obj)

            pointer = pointer + 1
        
        return diverse_ranking
    

    def getObjectRanking(self, usersers, metric, contentFilter, season):
        if usersers.sum() == 0:
            return self.getTopObjects(self.usr_obj_mat)
        
        usr_obj_matrix = None

        if contentFilter:
            user_cats = self.getUserCategories(usersers)
            cat_objects = self.getCatObjects(user_cats)
            cat_objects_in_matrix = [obj for obj in cat_objects if obj in self.usr_obj_mat.columns]
            usr_obj_matrix = self.usr_obj_mat[cat_objects_in_matrix]
        else:
            usr_obj_matrix = self.usr_obj_mat

            
        users_matrix = None


        if season:
            timestanp1 = season[0].timestamp()
            timestanp2 = season[1].timestamp()

            season_df = self.usr_metadata[self.usr_metadata['unixReviewTime'] >= timestanp1]
            season_df = season_df[season_df['unixReviewTime'] <= timestanp2]

            picked_columns = [a for a in season_df['asin'] if a in usr_obj_matrix.columns]
            picked_index = [a for a in season_df['reviewerID'] if a in usr_obj_matrix.index]

            picked_columns = np.unique(picked_columns)
            picked_index = np.unique(picked_index)

            usr_obj_matrix = usr_obj_matrix[picked_columns].loc[picked_index]

            users_matrix = self.usr_repr.loc[picked_index]
        else:            
            users_matrix = self.usr_repr

            

        if len(usr_obj_matrix) == 0:
            raise Exception('No data for the season')
        

        matrix_columns = usr_obj_matrix.columns.tolist()

        song_scores = np.array([0] * len(matrix_columns))

        for i in range(len(users_matrix)):
            user = users_matrix.iloc[i]
            if user.values.sum() != 0:
                closeness = metric(user.values, usersers.values)
                scoring = self.getOneZeroNumpyArrFromSerName(user, usr_obj_matrix) * closeness
                song_scores = song_scores + scoring


        top_songs_arg = np.argsort(- song_scores)

        ranking =  [matrix_columns[ind] for ind in top_songs_arg]

        return ranking
            
            
    def getObjectCat(self, obj) -> list:
        return self.obj_metadata[self.obj_metadata.index.isin([obj])]['sub_cat'].values.tolist()[0]
    
    def getCatObjects(self, cat_list) -> list:
        cat_objects = list(self.obj_metadata[self.obj_metadata['sub_cat'].isin(cat_list)].index)
        return cat_objects

    def getUserCategories(self, userseries):
        user_objs = self.getUserObjects(userseries)
        return self.obj_metadata[self.obj_metadata.index.isin(user_objs)]['sub_cat'].values.tolist()

    def getUserObjects(self, userseries) -> list:
        user_name = userseries.name
        return self.usr_metadata[self.usr_metadata['reviewerID'] == user_name]['asin'].values.tolist()
        # return userseries[userseries > 0].index.tolist() # get from OG sim_matrix

    def getOneZeroNumpyArr(self, userseries):
        answer = userseries.copy()
        answer[answer > 0] = 1
        return answer.values
    
    def getOneZeroNumpyArrFromSerName(self, userseries, usr_obj_matrix):
        user_name = userseries.name
        user_ser = usr_obj_matrix.loc[user_name].copy()
        user_ser[user_ser > 0] = 1
        return user_ser.values

class RecommendationSystemMatrix(RecommendationSystem):
    def __init__(self, usr_repr, obj_metadata, usr_metadata, obj_embeds) -> None:
            self.usr_repr = usr_repr
            self.obj_metadata = obj_metadata
            self.usr_metadata = usr_metadata
            self.obj_embeds = obj_embeds
    
    def getObjectRanking(self, usersers, metric, contentFilter):
        if usersers.sum() == 0:
            print("returning top objects")
            return self.getTopObjects(self.usr_repr)
        
        users_matrix = None

        if contentFilter:
            user_cats = self.getUserCategories(usersers)
            cat_objects = self.getCatObjects(user_cats)
            # get object from users_matrix that are in cat_objects (some may not be in users_matrix)
            cat_objects_in_matrix = [obj for obj in cat_objects if obj in self.usr_repr.columns]
            users_matrix = self.usr_repr[cat_objects_in_matrix]
        else:
            users_matrix = self.usr_repr

        matrix_columns = users_matrix.columns.tolist()

        userseries = usersers.copy()

        userseries = pd.Series(userseries, index=matrix_columns).fillna(0)

        song_scores = [0] * len(users_matrix.columns)

        for i in range(len(users_matrix)):
            user = users_matrix.iloc[i]
            if user.values.sum() > 0:
                closeness = metric(user.values, userseries.values)
                scoring = self.getOneZeroNumpyArr(user) * closeness
                song_scores = song_scores + scoring

        top_songs_arg = np.argsort(- song_scores)

        return [users_matrix.columns.to_list()[ind] for ind in top_songs_arg]
    

def get_season(input_date):
    # Calculate the year of the input date
    year = input_date.year

    # Determine the start and end dates of the seasons based on astronomical events
    spring_start = datetime(year, 3, 1)
    summer_start = datetime(year, 6, 1)
    autumn_start = datetime(year, 9, 1)
    winter_start = datetime(year, 12, 1)

    # Define the season names and corresponding dates
    seasons = {
        'Winter_1': (winter_start.replace(year=year-1), spring_start - timedelta(days=1)),
        'Spring': (spring_start, summer_start - timedelta(days=1)),
        'Summer': (summer_start, autumn_start - timedelta(days=1)),
        'Autumn': (autumn_start, winter_start - timedelta(days=1)),
        'Winter_2': (winter_start, spring_start.replace(year=year+1) - timedelta(days=1)),
    }

    # Determine the season for the input date
    season = None
    for name, (start, end) in seasons.items():
        if start <= input_date <= end:
            season = name
            break

    if season is None:
        return "Invalid date"

    # Return the start and end dates of the season
    return seasons[season]