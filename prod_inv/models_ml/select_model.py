import math
import pickle

import numpy as np
from imblearn.over_sampling import SMOTE
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score
from sklearn.preprocessing import MinMaxScaler
from sklearn.tree import DecisionTreeClassifier

from prod_inv.app import db
from prod_inv.models.ml_model import MLModel


def train_model(filter_df, coin, date_reference, n_samples=1, target_value = 0.01, period=14400, window_model = 400):
    filter_df['target_log_return_1'] = np.log(filter_df.close.shift(-1) / filter_df.close)
    filter_df['target_log_return_2'] = np.log(filter_df.close.shift(-2) / filter_df.close)
    filter_df['target_log_return_3'] = np.log(filter_df.close.shift(-3) / filter_df.close)
    filter_df['target_log_return_4'] = np.log(filter_df.close.shift(-4) / filter_df.close)
    filter_df['target_log_return_5'] = np.log(filter_df.close.shift(-5) / filter_df.close)
    filter_df['target_log_return_6'] = np.log(filter_df.close.shift(-6) / filter_df.close)

    mask = (
        (filter_df['target_log_return_1'] > target_value)
        | (filter_df['target_log_return_2'] > target_value)
        | (filter_df['target_log_return_3'] > target_value)
        | (filter_df['target_log_return_4'] > target_value)
        | (filter_df['target_log_return_5'] > target_value)
        | (filter_df['target_log_return_6'] > target_value)
    )
    filter_df.loc[mask, 'target_sign'] = 1
    filter_df.loc[~mask, 'target_sign'] = 0

    drop_columns = ['close',
                    'target_log_return_1', 'target_log_return_2', 'target_log_return_3',
                    'target_log_return_4', 'target_log_return_5', 'target_log_return_6'
                    ]

    clean_df = filter_df.dropna().drop(drop_columns,axis=1)
    print(coin)
    size_model = math.floor((3600 * 24 * window_model) / period)
    window_df = clean_df.iloc[-size_model:]

    X = window_df.drop(['target_sign'], axis=1)
    y = window_df[['target_sign']]

    scaler = MinMaxScaler().fit(X)
    X = scaler.transform(X)

    p = 1 / n_samples
    p_sample = []
    end_sample = 0
    threshold = 0.8

    models = {
        'Random Forest': RandomForestClassifier(random_state=42),
        'Extra Tree':   ExtraTreesClassifier(random_state=42),
        'Decision Tree': DecisionTreeClassifier(random_state=42),
        'Gradient Boost': GradientBoostingClassifier(random_state=42)
    }

    for p_i in range(1, n_samples + 1):
        base_sample = math.floor(end_sample)
        end_sample = p_i * p * len(X)

        print('--------------')
        print(base_sample)
        print(end_sample)

        X_sample = X[base_sample:math.floor(end_sample)]
        y_sample = y.iloc[base_sample:math.floor(end_sample)]

        X_train, X_test = X_sample[:math.floor(len(X_sample) * 0.75)], X_sample[math.ceil(len(X_sample) * 0.75):]
        y_train, y_test = y_sample.iloc[:math.floor(len(y_sample) * 0.75)], y_sample.iloc[math.ceil(len(y_sample) * 0.75):]

        oversampler = SMOTE(random_state=42)
        X_train, y_train = oversampler.fit_sample(X_train, y_train)

        precisions = []

        for k,v in models.items():
            # print('---------------------------------------------------')
            # print(k)
            v.fit(X_train, y_train)
            predicted_proba = v.predict_proba(X_test)
            predicted = (predicted_proba[:, 1] >= threshold).astype('int')
            precision = precision_score(y_test, predicted)
            # print('Precision')
            # print(precision)
            train_acc = accuracy_score(y_test, predicted)
            # print('Accuracy')
            # print(train_acc)
            #print(np.sum(predicted))
            precisions.append({
                'Model': k,
                'Precision': precision,
                'Accuracy': train_acc,
                'Trades': np.sum(predicted),
                'Real Profits': np.sum(y_test)[0],
                'Model_model': v,
                'Target': target_value,
                'Scaler': scaler
            })

        p_sample.append(precisions)

    avg_models = []
    for nm in models.keys():
        avg_precision = np.mean([p['Precision'] for ps in p_sample for p in ps if p['Model'] == nm])
        avg_models.append({
            'Model': nm,
            'Precision': avg_precision
        })

    best_model = sorted(avg_models, key=lambda k: k['Precision'], reverse=True)[0]
    models = {
        'Random Forest': RandomForestClassifier(random_state=42),
        'Extra Tree': ExtraTreesClassifier(random_state=42),
        'Decision Tree': DecisionTreeClassifier(random_state=42),
        'Gradient Boost': GradientBoostingClassifier(random_state=42)
    }

    X_train, X_test = X[:math.floor(len(X) * 0.75)], X[math.ceil(len(X) * 0.75):]
    y_train, y_test = y.iloc[:math.floor(len(y) * 0.75)], y.iloc[math.ceil(len(y) * 0.75):]

    oversampler = SMOTE(random_state=42)
    X_train, y_train = oversampler.fit_sample(X_train, y_train)

    models[best_model['Model']].fit(X_train, y_train)


    predicted_proba = models[best_model['Model']].predict_proba(X_test)
    predicted = (predicted_proba[:, 1] >= threshold).astype('int')
    precision = precision_score(y_test, predicted)
    print('Precision')
    print(precision)
    train_acc = accuracy_score(y_test, predicted)
    print('Accuracy')
    print(train_acc)
    print(np.sum(predicted))

    targets = ['target_log_return_1', 'target_log_return_2', 'target_log_return_3',
               'target_log_return_4', 'target_log_return_5', 'target_log_return_6', ]

    returns = []
    for t in targets:
        returns.append(filter_df.loc[filter_df['target_sign'] == 0][t].values)

    flat_missed_list = [item for sublist in returns for item in sublist if not math.isnan(item)]


    returns = []
    for t in targets:
        returns.append(filter_df.loc[filter_df['target_sign'] == 1][t].values)

    flat_list = [item for sublist in returns for item in sublist if not math.isnan(item)]


    numbers_model = {
        'Model': best_model['Model'],
        'Precision': precision,
        'Accuracy': train_acc,
        'Trades': np.sum(predicted),
        'Model_model': models[best_model['Model']],
        'Target': target_value,
        'Scaler': scaler,
        'Target_sample': flat_list
    }

    filename = coin + '_model.sav'
    pickle.dump(numbers_model, open(filename, 'wb'))

    try:
        model_entity = MLModel(date_reference, period, coin, filename, precision)
        db.session.add(model_entity)
        db.session.commit()

    except Exception:
        db.session.rollback()
        print('Already has value Model ' + str(date_reference))

    return precision