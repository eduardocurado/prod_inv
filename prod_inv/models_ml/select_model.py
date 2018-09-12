import math
import pickle

import numpy as np
from imblearn.over_sampling import SMOTE
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score
from sklearn.naive_bayes import GaussianNB
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from prod_inv.app import db
from prod_inv.models.ml_model import MLModel


def train_model(filter_df, coin, date_reference, targe_value = 0.01, period=14400, window_model = 400):
    filter_df['target_log_return_1'] = np.log(filter_df.close.shift(-1) / filter_df.close)
    filter_df['target_log_return_2'] = np.log(filter_df.close.shift(-2) / filter_df.close)
    filter_df['target_log_return_3'] = np.log(filter_df.close.shift(-3) / filter_df.close)
    filter_df['target_log_return_4'] = np.log(filter_df.close.shift(-4) / filter_df.close)
    filter_df['target_log_return_5'] = np.log(filter_df.close.shift(-5) / filter_df.close)
    filter_df['target_log_return_6'] = np.log(filter_df.close.shift(-6) / filter_df.close)

    mask = (
        (filter_df['target_log_return_1'] > targe_value)
        | (filter_df['target_log_return_2'] > targe_value)
        | (filter_df['target_log_return_3'] > targe_value)
        | (filter_df['target_log_return_4'] > targe_value)
        | (filter_df['target_log_return_5'] > targe_value)
        | (filter_df['target_log_return_6'] > targe_value)
    )
    filter_df.loc[mask, 'target_sign'] = 1
    filter_df.loc[~mask, 'target_sign'] = 0

    drop_columns = ['close',
                    'target_log_return_1', 'target_log_return_2', 'target_log_return_3',
                    'target_log_return_4', 'target_log_return_5', 'target_log_return_6'
                    ]

    #create two models: bull and bear
    market = ['bull', 'bear']
    for m in market:
        if m == 'bull':
            clean_df = filter_df.dropna().loc[(filter_df['slope_short'] > 0)].drop(drop_columns,axis=1)
        elif m == 'bear':
            clean_df = filter_df.dropna().loc[(filter_df['slope_short'] <= 0)].drop(drop_columns, axis=1)
        print(coin)
        print(m)
        size_model = math.floor((3600 * 24 * window_model) / period)
        window_df = clean_df.iloc[-size_model:]

        X = window_df.drop(['target_sign'], axis=1)
        y = window_df[['target_sign']]

        scaler = StandardScaler().fit(X)
        X = scaler.transform(X)

        X_train, X_test = X[:math.floor(len(X) * 0.7)], X[math.ceil(len(X) * 0.7):]
        y_train, y_test = y.iloc[:math.floor(len(y) * 0.7)], y.iloc[math.ceil(len(y) * 0.7):]

        oversampler = SMOTE(random_state=42)
        X_train, y_train = oversampler.fit_sample(X_train, y_train)

        models = [RandomForestClassifier(random_state=42), ExtraTreesClassifier(random_state=42),
                  DecisionTreeClassifier(random_state=42), GradientBoostingClassifier(random_state=42),
                  GaussianNB()
                  ]
        names_models = ['Random Forest', 'Extra Tree', 'Decision Tree', 'Gradient Boost', 'GaussianNB']

        precisions = []
        threshold = 0.8
        for i in range(len(models)):
            print('---------------------------------------------------')
            print(names_models[i])
            models[i].fit(X_train, y_train)
            predicted_proba = models[i].predict_proba(X_test)
            predicted = (predicted_proba[:, 1] >= threshold).astype('int')
            precision = precision_score(y_test, predicted)
            print('Precision')
            print(precision)
            train_acc = accuracy_score(y_test, predicted)
            print('Accuracy')
            print(train_acc)
            print(np.sum(predicted))
            precisions.append({
                # 'Model': names_models[i],
                'Precision': precision,
                'Accuracy': train_acc,
                'Trades': np.sum(predicted),
                'Real Profits': np.sum(y_test)[0],
                'Model_model': models[i],
                'Target': targe_value,
                'Scaler': scaler
            })

        best_model = sorted(precisions, key=lambda k: k['Precision'], reverse=True)[0]
        filename = m + '_' + coin + '_model.sav'
        pickle.dump(best_model, open(filename, 'wb'))

        try:
            model_entity = MLModel(date_reference, period, coin, filename, best_model['Precision'])
            db.session.add(model_entity)
            db.session.commit()

        except Exception:
            db.session.rollback()
            print('Already has value Model ' + str(date_reference))

    return precisions