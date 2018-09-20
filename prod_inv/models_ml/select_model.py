import math
import pickle

import numpy as np
import pandas as pd
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


target_values = [0, 0.005, 0.01, 0.015, 0.02, 0.025, 0.03]

threshold = 0.80


models = {
    'Random Forest': RandomForestClassifier(random_state=42),
    'Extra Tree': ExtraTreesClassifier(random_state=42),
    'Decision Tree': DecisionTreeClassifier(random_state=42),
    'Gradient Boost': GradientBoostingClassifier(random_state=42)
}


def run_model(X_sample, y_sample, target_value, models=models):
    scaler = MinMaxScaler().fit(X_sample)
    X_sample = scaler.transform(X_sample)
    # Split Train, Test
    X_train, X_test = X_sample[:math.floor(len(X_sample) * 0.75)], X_sample[math.ceil(len(X_sample) * 0.75):]
    y_train, y_test = y_sample.iloc[:math.floor(len(y_sample) * 0.75)], y_sample.iloc[math.ceil(len(y_sample) * 0.75):]

    # Rebalance Samples

    oversampler = SMOTE(random_state=42)
    X_train, y_train = oversampler.fit_sample(X_train, y_train.target_sign)
    # (Re) define Models
    precisions = []

    # Run Models

    for k, v in models.items():
        v.fit(X_train, y_train)
        predicted_proba = v.predict_proba(X_test)
        predicted = (predicted_proba[:, 1] >= threshold).astype('int')
        precision = precision_score(y_test, predicted)
        train_acc = accuracy_score(y_test, predicted)
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

    return precisions


def select_model(quality_models, features_df):
    targets = ['target_log_return_1', 'target_log_return_2', 'target_log_return_3',
               'target_log_return_4', 'target_log_return_5', 'target_log_return_6', ]
    risk_free = ((1 + 0.065) ** (1 / 252) - 1)
    simulations = []

    for index, row in quality_models.iterrows():
        TP = row['Target']
        P = row['Precision']
        mask = (
            ((features_df['target_log_return_1'] >= TP)
             | (features_df['target_log_return_2'] >= TP)
             | (features_df['target_log_return_3'] >= TP)
             | (features_df['target_log_return_4'] >= TP)
             | (features_df['target_log_return_5'] >= TP)
             | (features_df['target_log_return_6'] >= TP))
        )
        features_df.loc[mask, 'target_sign'] = 1
        features_df.loc[~mask, 'target_sign'] = 0

        drop_columns = ['close']

        # Preparing dataframe
        clean_df = features_df.drop(drop_columns, axis=1).copy()


        returns = []
        for t in targets:
            returns.append(clean_df.loc[clean_df['target_sign'] == 0][t].values)

        flat_missed_list = [item for sublist in returns for item in sublist if not math.isnan(item)]

        returns = []
        for t in targets:
            returns.append(clean_df.loc[clean_df['target_sign'] == 1][t].values)

        flat_list = [item for sublist in returns for item in sublist if not math.isnan(item)]

        ps = 0.05
        while ps < 1:
            SL = np.percentile(flat_missed_list, ps * 100)
            if SL < -3 * TP or SL > -0.01:
                ps += 0.05
                continue
            P_stop_loss_right = len([f for f in flat_list if f <= SL]) / len(flat_list)
            Mean_return_wrong = np.percentile(flat_missed_list, 40)
            ER = P * (1 - P_stop_loss_right) * TP + P * P_stop_loss_right * SL + (1 - P) * (
            1 - ps) * Mean_return_wrong + (1 - P) * ps * SL
            simulations.append({
                'ER': ER,
                'Probability Stop Loss Miss': ps,
                'Probability Stop Loss Right': P_stop_loss_right,
                'Stop Loss': SL,
                'Multiple': ER / risk_free,
                'Model': row['Model'],
                'Precision': row['Precision'],
                'Take_profit': TP,
                'Mean Return Wrong': Mean_return_wrong
            })
            ps += 0.05

    col_order = ['Model', 'Take_profit', 'Stop Loss', 'Precision', 'Probability Stop Loss Miss',
                     'Probability Stop Loss Right', 'Mean Return Wrong', 'ER', 'Multiple']
    if not simulations:
        return None
    return pd.DataFrame.from_records(simulations).sort_values(['Multiple', 'Precision'], ascending=False)[col_order].iloc[0]


def train_model(filter_df, coin, date_reference, period=14400):
    filter_df['target_log_return_1'] = np.log(filter_df.close.shift(-1) / filter_df.close)
    filter_df['target_log_return_2'] = np.log(filter_df.close.shift(-2) / filter_df.close)
    filter_df['target_log_return_3'] = np.log(filter_df.close.shift(-3) / filter_df.close)
    filter_df['target_log_return_4'] = np.log(filter_df.close.shift(-4) / filter_df.close)
    filter_df['target_log_return_5'] = np.log(filter_df.close.shift(-5) / filter_df.close)
    filter_df['target_log_return_6'] = np.log(filter_df.close.shift(-6) / filter_df.close)
    results_target = []
    for target_value in target_values:
        # Setting up target values
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

        # Preparing dataframe
        clean_df = filter_df.drop(drop_columns, axis=1).copy()
        # Defining Features (X) and Target Variable (y)


        X = clean_df.drop(['target_sign'], axis=1)
        y = clean_df[['target_sign']]

        p_sample = []
        end_sample = 0
        base_sample = 0
        n_samples = 3
        p = 1 / n_samples
        for p_i in range(1, n_samples + 1):
            end_sample = p_i * p * len(X)
            # Slicing Folders
            X_sample = X[base_sample:math.floor(end_sample)]
            y_sample = y.iloc[base_sample:math.floor(end_sample)]
            base_sample = math.floor(end_sample)
            p_sample.append(run_model(X_sample, y_sample, target_value))

        # Getting Average From Each Model Performance
        avg_models = []
        for nm in models.keys():
            avg_precision = np.mean([p['Precision'] for ps in p_sample for p in ps if p['Model'] == nm])
            avg_models.append({
                'Model': nm,
                'Precision': avg_precision,
                'Target': target_value

            })
        for r in avg_models:
            results_target.append(r)

    models_results_df = pd.DataFrame.from_records(results_target)
    quality_models = models_results_df.loc[models_results_df['Precision'] > 0.5].copy()
    quality_models['Mult'] = quality_models['Precision'] * quality_models['Target']

    best_model = select_model(quality_models, filter_df)

    numbers_model = {
        'Model': None,
        'Precision': 0,
        'Model_model': None,
        'Target': None,
        'Scaler': None,
        'Stop loss': None,
        'Expected Return': None
    }

    if not best_model.empty:
        n_samples = 3
        target_value = best_model['Take_profit']
        stop_loss = best_model['Stop Loss']

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

        # Preparing dataframe
        clean_df = filter_df.drop(drop_columns, axis=1).copy()
        # Defining Features (X) and Target Variable (y)


        X = clean_df.drop(['target_sign'], axis=1)
        y = clean_df[['target_sign']]

        # Slicing Folders
        base_sample = (2 / n_samples) * len(X)
        X_sample = X[math.floor(base_sample):]
        y_sample = y.iloc[math.floor(base_sample):]


        model = run_model(X_sample, y_sample, target_value, {best_model['Model']: models[best_model['Model']]})
        if model and base_sample > 300:
            model = model[0]
            p = model['Precision']
            p_stop_loss_right = best_model['Probability Stop Loss Right']
            ps = best_model['Probability Stop Loss Miss']
            mean_return_wrong = best_model['Mean Return Wrong']
            ER = p * (1 - p_stop_loss_right) * target_value + p * p_stop_loss_right * stop_loss + (1 - p) * (
                1 - ps) * mean_return_wrong + (1 - p) * ps * stop_loss
            if ER > 0:
                numbers_model = {
                    'Model': model['Model'],
                    'Precision': p,
                    'Model_model': model['Model_model'],
                    'Target': target_value,
                    'Scaler': model['Scaler'],
                    'Stop loss': stop_loss,
                    'Expected Return': ER
                }

    filename = coin + '_model.sav'
    pickle.dump(numbers_model, open(filename, 'wb'))

    try:
        model_entity = MLModel(date_reference, period, coin, filename, numbers_model['Precision'])
        db.session.add(model_entity)
        db.session.commit()

    except Exception:
        db.session.rollback()
        print('Already has value Model ' + str(date_reference))

    return numbers_model['Expected Return']