import numpy as np, pandas as pd, json, os, datetime, time
from xgboost import XGBClassifier, plot_importance
import multiprocessing as mp
import pickle

from sklearn.metrics import confusion_matrix
from sklearn.datasets import make_circles
from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import f1_score
from sklearn.metrics import fbeta_score
from sklearn.metrics import cohen_kappa_score
from sklearn.metrics import roc_auc_score
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import train_test_split, GridSearchCV

import random
from scipy import stats


class XGBoostManager():
    def __init__(self):

        # create folder 
        if 'results' not in os.listdir():
            os.mkdir('results')

        self.WEIGHT_MOD_optimal = 'optimal'

        self.EVAL_METRIC_f1score = 'f1-score'
        self.EVAL_METRIC_fbetascore = 'fbeta-score'
        self.EVAL_METRIC_accuracy = 'accuracy'

        self.set_default_config()


    def __repr__(self):
        return self.get_classification_model.coef_


    def set_default_config(self):
        self.CONFIG_DATA_test_size_over_all = 0.2
        self.CONFIG_DATA_val_size_over_train = 0.3
        self.CONFIG_DATA_shuffle = True

        
        self.CONFIG_MODEL_n_estimators = 300
        self.CONFIG_MODEL_max_depth = 9
        self.CONFIG_MODEL_learning_rate = 0.001
        self.CONFIG_MODEL_booster = 'gbtree'
        self.CONFIG_MODEL_tree_method = 'auto'
        self.CONFIG_MODEL_n_jobs = mp.cpu_count() - 1 
        self.CONFIG_MODEL_subsample = 0.5
        self.CONFIG_MODEL_colsample_bytree = 0.5

        self.CONFIG_TRAIN_mod_weight = "sqrt"
        self.CONFIG_TRAIN_early_stopping_rounds = 40
        self.CONFIG_TRAIN_verbose = 1

        self.CONFIG_SHOW_importance_type = "gain"
        self.CONFIG_SHOW_print_confusion_matrix = True

        

    def get_classification_model(self):
        classifier=XGBClassifier(n_estimators=self.CONFIG_MODEL_n_estimators,
                                max_depth=self.CONFIG_MODEL_max_depth,
                                learning_rate=self.CONFIG_MODEL_learning_rate,
                                booster=self.CONFIG_MODEL_booster,
                                tree_method=self.CONFIG_MODEL_tree_method,
                                n_jobs=self.CONFIG_MODEL_n_jobs,
                                subsample=self.CONFIG_MODEL_subsample,
                                colsample_bytree=self.CONFIG_MODEL_colsample_bytree)
        return classifier

    def train_classification(self, model, data):
        data=data.set_index('time')
        #Splitting train val and test sets
        Y=data.label.astype(int)
        X=data.drop('label',axis=1)
        X_train, X_test, y_train, y_test = train_test_split(X, Y, 
                                                            test_size = self.CONFIG_DATA_test_size_over_all, 
                                                            shuffle=self.CONFIG_SHOW_print_confusion_matrix)
        X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, 
                                                          test_size = self.CONFIG_DATA_val_size_over_train, 
                                                          shuffle=self.CONFIG_SHOW_print_confusion_matrix)

        # weight
        #model.scale_pos_weight = weight
        

        if len(np.unique(y_train)) > 2:
            classifier.objective = 'multi:softmax'
            classifier.n_classes_ = len(np.unique(y_train))
            y_train = y_train + 1 
            y_test = y_test + 1 
            y_val = y_val + 1

        # train model
        eval_set = [(X_train, y_train), (X_val, y_val)]
        trained_model = classifier.fit(X_train,y_train, 
                                        early_stopping_rounds=self.CONFIG_TRAIN_early_stopping_rounds, 
                                        eval_set=eval_set,
                                        verbose=self.CONFIG_TRAIN_verbose)

        #predicting test
        y_pred_val = self.predict(trained_model,X_val)
        y_pred_test = self.predict(trained_model,X_test)

        if print_confusion_matrix:
            self.show_confusion_matrix(y_val, y_pred_val, y_test, y_pred_test)

        #Metrics scrores
        metrics_df = self.get_df_metrics(y_val, y_pred_val, y_test, y_pred_test)

        return trained_model

    def opt_param_classification(self, model, data, list_max_depth, list_n_estimators, list_learning_rate):
        clf = GridSearchCV(model,
                   {'max_depth': list_max_depth,
                    'n_estimators': list_n_estimators,
                    'learning_rate': list_learning_rate}, verbose=1, n_jobs=mp.cpu_count()-1)
        trained_model = clf.fit(X, y)

        print(trained_model.best_score_)
        print(trained_model.best_params_)

        print(trained_model.cv_results_)

        return trained_model

    def save_model(self, model, path):
        pickle.dump(model, path)

    def plot_importance(self, model, importance_type='gain'):
        ax = plot_importance(classifier, height=0.9, importance_type=importance_type)
        return ax.figure

    def predict(self, model, X):
        return model.predict(X)

    def show_confusion_matrix(self, y_val, y_pred_val, y_test, y_pred_test):
            print('')
            print('Confusion matrix of validation:')
            print(confusion_matrix(y_val, y_pred_val))
            print('Confusion matrix of test:')
            print(confusion_matrix(y_test, y_pred_test))

    def get_df_metrics(self, y_val, y_pred_val, y_test, y_pred_test):
        return pd.DataFrame([[accuracy_score(y_val,y_pred_val),accuracy_score(y_test,y_pred_test)],
                                [precision_score(y_val,y_pred_val),precision_score(y_test,y_pred_test)],
                                [recall_score(y_val,y_pred_val),recall_score(y_test,y_pred_test)],
                                [f1_score(y_val,y_pred_val),f1_score(y_test,y_pred_test)]],
                                columns=['Validation','Test'],index=['Accuracy','Precision','Recall','F1-score'])


        