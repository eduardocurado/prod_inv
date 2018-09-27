import pickle


def predict_signal(X, coin, threshold=0.8):
    filename = coin + '_model.sav'
    signal = 0
    expected_value = 0
    precision = 0
    target_profit = 0
    stop_loss = 0

    try:
        precisions = pickle.load(open(filename, 'rb'))
        if precisions['Expected Return'] > 0:
            X = precisions['Scaler'].transform(X.ravel().reshape(1,-1))
            predicted_proba = precisions['Model_model'].predict_proba(X)
            if predicted_proba[0][1] > threshold:
                signal = 1
            precision = precisions['Precision']
            target_profit = precisions['Target']
            stop_loss = precisions['Stop loss']
            expected_value = precisions['Expected Return']
    except Exception as e:
        print('No model found')

    return signal, precision, target_profit, stop_loss, expected_value
