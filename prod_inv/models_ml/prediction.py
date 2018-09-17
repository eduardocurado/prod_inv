import pickle

from prod_inv.models_ml.utils import get_expected_values


def predict_signal(X, coin, threshold=0.8):
    filename = coin + '_model.sav'
    precisions = pickle.load(open(filename, 'rb'))
    X = precisions['Scaler'].transform(X.ravel().reshape(1,-1))

    predicted_proba = precisions['Model_model'].predict_proba(X)
    signal = 0
    expected_value = 0

    if predicted_proba[0][1] > threshold:
        signal = 1
        get_expected_values(precisions['Precision'], precisions['Target'], precisions['Target_sample'])



    return signal, precisions['Precision'], precisions['Target'], expected_value, stop_loss

