import pandas as pd
import os
from sklearn.dummy import DummyClassifier
from sklearn import svm
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score
from sklearn.metrics import classification_report
import json
import yaml
from sklearn.metrics import multilabel_confusion_matrix, ConfusionMatrixDisplay
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import StratifiedKFold
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import SelectPercentile, f_classif
from sklearn.decomposition import PCA
from sklearn.feature_selection import SequentialFeatureSelector
from time import time
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler
from sklearn.experimental import enable_halving_search_cv
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, HalvingGridSearchCV, HalvingRandomSearchCV
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.base import BaseEstimator, TransformerMixin
from gensim.models import KeyedVectors
import numpy as np
from sys import exit
import joblib

# metrics = {}
# with open("results.json", "w") as f:
#     json.dump(obj=metrics, fp=f)

# exit(0)

isMlFlow = False

class Word2VecTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, w2v_model):
        self.w2v_model = w2v_model

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        # Convert each document into a vector representation by averaging the word embeddings
        vectors = []
        for doc in X:
            words = doc.split(" ")
            vecs = []
            for word in words:
                if word in self.w2v_model:
                    vecs.append(self.w2v_model[word])
            if vecs:
                vectors.append(np.mean(vecs, axis=0))
            else:
                vectors.append(np.zeros(self.w2v_model.vector_size))
        return np.array(vectors)

def RunClassifier(clf, df_train, df_test):
    clf.fit(df_train.iloc[:, 1:], df_train.iloc[:, 0])

    y_true = df_test.iloc[:, 0]
    y_pred = clf.predict(df_test.iloc[:, 1:])
    return (y_true, y_pred)

params = yaml.safe_load(open("params.yaml"))["train"]

strategy = params["strategy"]

method = params["method"]

used_data = params["used_data"]

feature_selection = params['feature_selection']

feature_number = params['feature_number']
experiment = params['experiment']
hypparamselec = params['hypparamselec']

bow_feature_num = params['bow_feature_num']
text_encode_method = params['text_encode_method']

data_path = './data/'
split_path = './data/features/'
result_path = './'

train_file_name = 'Amazon_train.json'
test_file_name = 'Amazon_test.json'

df_train = pd.read_json(os.path.join(split_path, train_file_name))
df_test = pd.read_json(os.path.join(split_path, test_file_name))

if used_data == 'all':
    pass
elif used_data == 'bow':
    columns = ['overall'] + [colname for colname in df_test.columns if colname[:4] == 'bow_']
    df_train = df_train[columns]
    df_test = df_test[columns]

elif used_data == 'nobow':
    columns = [colname for colname in df_test.columns if colname[:4] != 'bow_']
    df_train = df_train[columns]
    df_test = df_test[columns]
else:
    raise Exception('Invalid data selection method')

y_true = []
y_pred = []

clf = None

param_dist = {}

text_encoder_step = []
if used_data != 'nobow':
    if text_encode_method == 'bow':
        text_encoder_step = [('text', CountVectorizer(ngram_range=(1,1), max_features = bow_feature_num), 'text_data')] 

    elif text_encode_method == 'tf-idf':
        text_encoder_step = [('text', TfidfVectorizer(ngram_range=(1,1), max_features = bow_feature_num), 'text_data')]

    elif text_encode_method == 'word2vec':
        model_name = 'word2vec-google-news-300'
        model_path = os.path.join(model_name, model_name + '.gz')
        w2v_model = KeyedVectors.load_word2vec_format(os.path.join(data_path, model_path), binary=True)
        text_encoder_step = [('text', Word2VecTransformer(w2v_model), 'text_data')] 

    else:
        raise Exception('Wrong text encoder method')
preprocessData = ColumnTransformer(
    transformers= ( text_encoder_step
                  + ([('num', StandardScaler(), ['unixReviewTime', 'summary_length', 'reviewText_length'])]  if used_data == 'all' or used_data == 'nobow' else [])
                  + ([('label', 'passthrough', [colname for colname in df_test.columns if colname[:4] == 'cat_' or colname[:7] == 'season_'])] if used_data == 'all' or used_data == 'nobow' else [])
                  )
                )

if method == "dummy":
    clf = DummyClassifier(strategy=strategy)

elif method == "svc":
    clf = svm.SVC()
    param_dist = {'clf__C': [0.1, 1, 10, 100],
              'clf__kernel': ['linear', 'poly', 'rbf', 'sigmoid'],
              'clf__gamma': ['scale', 'auto'],
              'clf__shrinking': [True, False]}

elif method == "random_forest":
    clf = RandomForestClassifier()
    param_dist = {'clf__n_estimators': [50, 100, 150, 200],
                'clf__max_features': ['sqrt', 'log2'],
                'clf__max_depth': [None, 5, 10, 20],
                'clf__bootstrap': [True, False]}

else: 
    raise Exception('Not valid classifier')

if feature_selection == 'none':
    pass

elif feature_selection == 'select':
    clf = Pipeline(
    [
        ("anova", SelectPercentile(f_classif, percentile = feature_number)),
        ("clf", clf),
    ])

elif feature_selection == 'reduce':
    clf = Pipeline(
    [
        ("pca", PCA(n_components = feature_number)),
        ("clf", clf),
    ]
    )

elif feature_selection == 'sequence':
    clf = Pipeline(
    [
        ("sequence", SequentialFeatureSelector(estimator=clf, n_features_to_select = 'auto')),
        ("clf", clf),
    ]
    )

else:
    raise Exception('Invalid feature selection/reduction method')

clf  = Pipeline(
    steps=[('preprocessor', preprocessData),
           ('clf', clf)]
           )

if experiment == 'none':
    y_true, y_pred = RunClassifier(clf, df_train, df_test)

    report = classification_report(
        y_pred=y_pred,
        y_true=y_true,
        output_dict=True,
    )

    strat_k_fold = StratifiedKFold(shuffle=True, random_state=42)
    k5_cross_val = cross_val_score(clf, df_test.iloc[:, 1:], df_test.iloc[:, 0], cv=strat_k_fold).mean() if clf != None else None

    metrics = {
                "f1-score": f1_score(y_true, y_pred, average='macro'),
                "k5_cross_val": k5_cross_val
            }
    
elif experiment == 'hyperpar':
    search = None

    if hypparamselec == 'none':
        raise Exception('hypparamselec required for this experiment')
    
    elif hypparamselec == 'randomsearch':
        search = RandomizedSearchCV(clf, param_distributions=param_dist, n_iter=50, cv=5, n_jobs=-1)

    elif hypparamselec == 'gridsearch':
        search = GridSearchCV(clf, param_grid=param_dist, cv=5, n_jobs=-1)

    elif hypparamselec == 'halvinggridsearch':
        search = HalvingGridSearchCV(clf, param_grid=param_dist, cv=5, factor=2, random_state=42)

    elif hypparamselec == 'halvingrandomsearch':
        search = HalvingRandomSearchCV(clf, param_distributions=param_dist, cv=5, factor=2, random_state=42)

    else:
        raise Exception('Wrong hyperpar selector')

    start = time()        
    search.fit(df_test.iloc[:, 1:], df_test.iloc[:, 0])
    exec_time = time() - start
    
    metrics = {
        "best_acc_score": search.best_score_,
        "time": round(exec_time, 2)
    }
else:
    raise Exception('Not valid experiment')

# if isMlFlow:

#     fig = plot_metrics_per_class(report, labels=y_true.values.tolist())
#     mlflow.log_metrics(metrics=metrics)

#     if method == "dummy":
#             mlflow.sklearn.eval_and_log_metrics(
#                 dummy_clf, X=df_train.iloc[:, 1:], y_true=df_train.iloc[:, 0], prefix="test_"
#             )

#     mlflow.log_figure(fig, artifact_file="metrics.png")

#     class_names = list(set(y_true.values.tolist()))

#     cm = multilabel_confusion_matrix(y_pred, y_true, labels= class_names)

#     for matid in range(0,3):
#         disp = ConfusionMatrixDisplay(confusion_matrix=cm[matid])
        
#         disp.plot()
#         plt.title((class_names[matid] + " confusion"))
#         mlflow.log_figure(plt.gcf(), artifact_file=(class_names[matid] + "_confusion.png"))

joblib.dump(clf, 'clf.joblib')

with open("results.json", "w") as f:
    json.dump(obj=metrics, fp=f)
