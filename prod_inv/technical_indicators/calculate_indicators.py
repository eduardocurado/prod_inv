from prod_inv.fixtures import mas
from prod_inv.technical_indicators.adx import calculate_adx
from prod_inv.technical_indicators.atr import calculate_atr
from prod_inv.technical_indicators.boillinger import calculate_boillinger_bands
from prod_inv.technical_indicators.google_trends import calculate_sum_google_trends
from prod_inv.technical_indicators.ma import calculate_ma
from prod_inv.technical_indicators.macd import calculate_macd
from prod_inv.technical_indicators.momentum import calculate_momentum
from prod_inv.technical_indicators.obv import calculate_obv
from prod_inv.technical_indicators.rsi import calculate_rsi
from prod_inv.technical_indicators.williams import calculate_williams


def calculate_indicators(d, period, c):

    for m in mas:
        # SIMPLE MOVING AVERAGES
        calculate_ma(m, period, d.date, coins=[c], _type='SMA')

        # EWMA MOVING AVERAGES
        calculate_ma(m, period, d.date, coins=[c], _type='EMA')

    # Boilinger Bands
    calculate_boillinger_bands(m, period, d.date, coins=[c])

    # RSI
    calculate_rsi(14, period,  d.date, coins=[c],)

    # OBV
    calculate_obv(period, d.date, coins=[c])

    # MACD
    calculate_macd(period, d.date, 12, 26, 9, coins=[c])

    # Momentum
    calculate_momentum(period, d.date, 6, coins=[c])

    # ADX
    calculate_adx(period, d.date, 14, coins=[c])

    # ATR
    calculate_atr(period, d.date, 14, coins=[c])

    # WILLIAMS R
    calculate_williams(period, d.date, 14, coins=[c])

    # Google Trends
    calculate_sum_google_trends(period, d.date, 45, coins=[c])
