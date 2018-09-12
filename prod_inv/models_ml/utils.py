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