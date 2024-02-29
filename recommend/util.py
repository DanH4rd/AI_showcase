from scipy import stats
import numpy as np
import random
from threading import Thread
from sklearn.model_selection import KFold
from scipy import spatial
import pandas as pd
import tqdm
from RecommendationSystem import RecommendationSystem, get_season

class ThreadWithReturnValue(Thread):
    
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args,
                                                **self._kwargs)
    def join(self, *args):
        Thread.join(self, *args)
        return self._return

def intersection(lst1, lst2):
    lst3 = [value for value in lst1 if value in lst2]
    return lst3

# straightforward
def precisionScore(pred, true):
    score = 0
    counter = 0

    for i in range(len(pred)):
        if pred[i] in true:
            counter = counter + 1
            score = score +  counter / (i + 1)
    if counter > 0:
        return score / counter
    else:
        return 0

# straightforward
def intersectionScore(pred, true):
    return len(intersection(pred, true)) / len(true)

# 1st relevant stuff
def reciprocalRank(pred, true):
    for p in pred:
        if p in true:
            return 1 / (pred.index(p) + 1) 
    return 0

def discountedGain(pred, true):
    score = 0
    perfectScore = 0
    counter = 0
    for p in pred:
        if p in true:
            counter = counter + 1
            score = score + 1 / np.emath.logn(2, (pred.index(p) + 1) + 1) 
            perfectScore = perfectScore + 1 / np.emath.logn(2, counter + 1) 
    if perfectScore > 0:
        return score / perfectScore
    else:
        return 0

# measures how order matches, ignores entries that are absent in both lists
def spearmanCoef(pred, true):
    return stats.spearmanr(pred, true).statistic

def fixLists(l1, l2):
    for i1 in l1:
        if not i1 in l2:
            l2.append(i1)

    for i2 in l2:
        if not i2 in l1:
            l1.append(i2)

    return(l1, l2)

def combine_results(results):
    combine = np.array(list(results[0].values()))
    for i in range(1, len(results)):
        combine = combine + np.array(list(results[i].values()))

    combine = combine / len(results)
    return dict(zip(results[0].keys(),combine.tolist()))

def evaluate(recommentation_sys, test_matrix, reviews_df,  n, metric = spatial.distance.cosine, contentFilter = False, similarityLimit = 0., date=None):
    intersection = 0
    reciprocal = 0
    spearman = 0
    precision = 0
    dcg = 0

    counter = 0
    total_users = len(test_matrix)

    tested_counter = 0

    for i in tqdm.tqdm(range(len(test_matrix))):
        userser = test_matrix.iloc[i]
        listened = reviews_df[reviews_df['reviewerID'] == userser.name]

        
        if date:
            seasons = get_season(date)
            
            timestanp1 = seasons[0].timestamp()
            timestanp2 = seasons[1].timestamp()

            listened = listened[listened['unixReviewTime'] >= timestanp1]
            listened = listened[listened['unixReviewTime'] <= timestanp2]

        listened = listened.sort_values(by='overall', ascending=False)['asin']

        true_labels = listened.unique().tolist()
        
        if true_labels != []:

            recommend = recommentation_sys.recommend(userser, n, 
                metric = metric, 
                contentFilter = contentFilter, 
                similarityLimit = similarityLimit,
                date = date
                )

            tested_counter = tested_counter + 1


            intersection = intersection + intersectionScore(recommend, true_labels)
            reciprocal = reciprocal + reciprocalRank(recommend, true_labels)
            precision = precision + precisionScore(recommend, true_labels)
            dcg = dcg + discountedGain(recommend, true_labels)
            


        counter = counter + 1
        # print('Evaluation Progress {:5d}/{:5d}'.format(counter, total_users), end='\r')

    # print('Evaluation Complete                ')
    return {
        'intersection': intersection / tested_counter if tested_counter > 0 else 0,
        'reciprocal': reciprocal / tested_counter if tested_counter > 0 else 0,
        'precision': precision / tested_counter if tested_counter > 0 else 0,
        'dcg': dcg / tested_counter if tested_counter > 0 else 0,
        'tested_users': tested_counter,
    }

def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))

def evaluate_k_fold(recommendSys, matrix_df, obj_metadata, usr_metadata, obj_embeds, folds = 5,
    n=5, metric = spatial.distance.cosine, contentFilter = False, similarityLimit = 0., date=None):
    kf = KFold(n_splits=folds)
    results = []
    for i, (train_index, test_index) in enumerate(kf.split(matrix_df.index)):
        train_users = matrix_df.loc[matrix_df.index[train_index].tolist()]
        test_users = matrix_df.loc[matrix_df.index[test_index].tolist()]

        model = recommendSys(train_users, obj_metadata, usr_metadata, obj_embeds)

        eval_res = evaluate(model, test_users, usr_metadata, n, metric, contentFilter, similarityLimit, date)

        results.append(eval_res)

    return results