import pickle


def predict_signal(X, coin, threshold=0.8):
    filename = coin + '_model.sav'
    precisions = pickle.load(open(filename, 'rb'))
    X = precisions['Scaler'].transform(X.ravel().reshape(1,-1))

    predicted_proba = precisions['Model_model'].predict_proba(X)
    signal = 0
    if predicted_proba[0][1] > threshold:
        signal = 1

    return signal, precisions['Precision'], precisions['Target']

