from collections import defaultdict

import numpy as np
from scipy import stats
from sqlalchemy.inspection import inspect


def query_to_dict(rset):
    result = defaultdict(list)
    for obj in rset:
        instance = inspect(obj)
        for key, x in instance.attrs.items():
            result[key].append(x.value)
    return result


def get_slope(win, closes):
    seq = np.arange(0, win)
    di = []
    for i in range(win, len(closes)):
        v_closes = closes.iloc[i - win:i]
        base_date = v_closes.iloc[-1:][['date']].values[0][0]
        slope, intercept, r_value, p_value, std_err = stats.linregress(seq, v_closes['close'].values)
        di.append({
            'base_date': base_date,
            'slope': slope
        })
    return di


def get_multiple(Psl, P, TP, flat_list):
    SL = np.percentile(flat_list, Psl*100)
    mean_return = np.percentile(flat_list, 50)
    if SL < 0:
        ER = Psl * SL + (1-Psl) * P * TP #+ (1-Psl)*(1-P)*mean_return
        risk_free = ((1 + 0.065) ** (1/252) - 1)
        print(risk_free)
        print(ER)
        print(SL)
        print('----------')
        multiple = ER/risk_free
        return multiple

def get_expected_values(precision, target_value, flat_list):
    psls = [0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.11, 0.12, 0.15]
    simulations = []
    for ps in psls:
        simulations.append(get_multiple(ps, precision, target_value, flat_list))

    return simulations

