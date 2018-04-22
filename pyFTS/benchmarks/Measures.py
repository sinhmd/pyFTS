# -*- coding: utf8 -*-

"""
pyFTS module for common benchmark metrics
"""

import time
import numpy as np
import pandas as pd
from pyFTS.common import FuzzySet,SortedCollection
from pyFTS.probabilistic import ProbabilityDistribution


def acf(data, k):
    """
    Autocorrelation function estimative
    :param data: 
    :param k: 
    :return: 
    """
    mu = np.mean(data)
    sigma = np.var(data)
    n = len(data)
    s = 0
    for t in np.arange(0,n-k):
        s += (data[t]-mu) * (data[t+k] - mu)

    return 1/((n-k)*sigma)*s


def rmse(targets, forecasts):
    """
    Root Mean Squared Error
    :param targets: 
    :param forecasts: 
    :return: 
    """
    if isinstance(targets, list):
        targets = np.array(targets)
    if isinstance(forecasts, list):
        forecasts = np.array(forecasts)
    return np.sqrt(np.nanmean((targets - forecasts) ** 2))


def rmse_interval(targets, forecasts):
    """
    Root Mean Squared Error
    :param targets: 
    :param forecasts: 
    :return: 
    """
    fmean = [np.mean(i) for i in forecasts]
    return np.sqrt(np.nanmean((fmean - targets) ** 2))


def mape(targets, forecasts):
    """
    Mean Average Percentual Error
    :param targets: 
    :param forecasts: 
    :return: 
    """
    if isinstance(targets, list):
        targets = np.array(targets)
    if isinstance(forecasts, list):
        forecasts = np.array(forecasts)
    return np.mean(np.abs(targets - forecasts) / targets) * 100


def smape(targets, forecasts, type=2):
    """
    Symmetric Mean Average Percentual Error
    :param targets: 
    :param forecasts: 
    :param type: 
    :return: 
    """
    if isinstance(targets, list):
        targets = np.array(targets)
    if isinstance(forecasts, list):
        forecasts = np.array(forecasts)
    if type == 1:
        return np.mean(np.abs(forecasts - targets) / ((forecasts + targets)/2))
    elif type == 2:
        return np.mean(np.abs(forecasts - targets) / (abs(forecasts) + abs(targets)) )*100
    else:
        return sum(np.abs(forecasts - targets)) / sum(forecasts + targets)


def mape_interval(targets, forecasts):
    fmean = [np.mean(i) for i in forecasts]
    return np.mean(abs(fmean - targets) / fmean) * 100


def UStatistic(targets, forecasts):
    """
    Theil's U Statistic
    :param targets: 
    :param forecasts: 
    :return: 
    """
    l = len(targets)
    if isinstance(targets, list):
        targets = np.array(targets)
    if isinstance(forecasts, list):
        forecasts = np.array(forecasts)

    naive = []
    y = []
    for k in np.arange(0,l-1):
        y.append((forecasts[k ] - targets[k]) ** 2)
        naive.append((targets[k + 1] - targets[k]) ** 2)
    return np.sqrt(sum(y) / sum(naive))


def TheilsInequality(targets, forecasts):
    """
    Theil’s Inequality Coefficient
    :param targets: 
    :param forecasts: 
    :return: 
    """
    res = targets - forecasts
    t = len(res)
    us = np.sqrt(sum([u**2 for u in res]))
    ys = np.sqrt(sum([y**2 for y in targets]))
    fs = np.sqrt(sum([f**2 for f in forecasts]))
    return  us / (ys + fs)



def BoxPierceStatistic(data, h):
    """
    Q Statistic for Box-Pierce test
    :param data: 
    :param h: 
    :return: 
    """
    n = len(data)
    s = 0
    for k in np.arange(1,h+1):
        r = acf(data, k)
        s += r**2
    return n*s


def BoxLjungStatistic(data, h):
    """
    Q Statistic for Ljung–Box test
    :param data: 
    :param h: 
    :return: 
    """
    n = len(data)
    s = 0
    for k in np.arange(1,h+1):
        r = acf(data, k)
        s += r**2 / (n -k)
    return n*(n-2)*s


def sharpness(forecasts):
    """Sharpness - Mean size of the intervals"""
    tmp = [i[1] - i[0] for i in forecasts]
    return np.mean(tmp)


def resolution(forecasts):
    """Resolution - Standard deviation of the intervals"""
    shp = sharpness(forecasts)
    tmp = [abs((i[1] - i[0]) - shp) for i   in forecasts]
    return np.mean(tmp)


def coverage(targets, forecasts):
    """Percent of target values that fall inside forecasted interval"""
    preds = []
    for i in np.arange(0, len(forecasts)):
        if targets[i] >= forecasts[i][0] and targets[i] <= forecasts[i][1]:
            preds.append(1)
        else:
            preds.append(0)
    return np.mean(preds)


def pinball(tau, target, forecast):
    """
    Pinball loss function. Measure the distance of forecast to the tau-quantile of the target 
    :param tau: quantile value in the range (0,1)
    :param target: 
    :param forecast: 
    :return: float, distance of forecast to the tau-quantile of the target
    """
    if target >= forecast:
        return (target - forecast) * tau
    else:
        return (forecast - target) * (1 - tau)


def pinball_mean(tau, targets, forecasts):
    """
    Mean pinball loss value of the forecast for a given tau-quantile of the targets
    :param tau: quantile value in the range (0,1)
    :param targets: list of target values
    :param forecasts: list of prediction intervals
    :return: float, the pinball loss mean for tau quantile
    """
    try:
        if tau <= 0.5:
            preds = [pinball(tau, targets[i], forecasts[i][0]) for i in np.arange(0, len(forecasts))]
        else:
            preds = [pinball(tau, targets[i], forecasts[i][1]) for i in np.arange(0, len(forecasts))]
        return np.nanmean(preds)
    except Exception as ex:
        print(ex)


def pmf_to_cdf(density):
    ret = []
    for row in density.index:
        tmp = []
        prev = 0
        for col in density.columns:
            prev += density[col][row] if not np.isnan(density[col][row]) else 0
            tmp.append( prev )
        ret.append(tmp)
    df = pd.DataFrame(ret, columns=density.columns)
    return df


def heavyside_cdf(bins, targets):
    ret = []
    for t in targets:
        result = [1 if b >= t else 0 for b in bins]
        ret.append(result)
    df = pd.DataFrame(ret, columns=bins)
    return df


def crps(targets, densities):
    '''
    Continuous Ranked Probability Score
    :param targets: a list with the target values
    :param densities: a list with pyFTS.probabil objectsistic.ProbabilityDistribution
    :return: float
    '''
    _crps = float(0.0)
    if isinstance(densities, pd.DataFrame):
        l = len(densities.columns)
        n = len(densities.index)
        Ff = pmf_to_cdf(densities)
        Fa = heavyside_cdf(densities.columns, targets)
        for k in densities.index:
            _crps += sum([ (Ff[col][k]-Fa[col][k])**2 for col in densities.columns])
    elif isinstance(densities, ProbabilityDistribution.ProbabilityDistribution):
        l = len(densities.bins)
        n = 1
        Fa = heavyside_cdf(densities.bins, targets)
        _crps = sum([(densities.cummulative(val) - Fa[val][0]) ** 2 for val in densities.bins])
    elif isinstance(densities, list):
        l = len(densities[0].bins)
        n = len(densities)
        Fa = heavyside_cdf(densities[0].bins, targets)
        for df in densities:
            _crps += sum([(df.cummulative(val) - Fa[val][0]) ** 2 for val in df.bins])

    return _crps / float(l * n)


def get_point_statistics(data, model, **kwargs):
    '''
    Condensate all measures for point forecasters
    :param data: test data
    :param model: FTS model with point forecasting capability
    :param kwargs:
    :return: a list with the RMSE, SMAPE and U Statistic
    '''

    steps_ahead = kwargs.get('steps_ahead',1)

    indexer = kwargs.get('indexer', None)

    if indexer is not None:
        ndata = np.array(indexer.get_data(data))
    else:
        ndata = np.array(data[model.order:])

    ret = list()

    if steps_ahead == 1:
        forecasts = model.predict(data, **kwargs)
        if model.has_seasonality:
            nforecasts = np.array(forecasts)
        else:
            nforecasts = np.array(forecasts[:-1])
        ret.append(np.round(rmse(ndata, nforecasts), 2))
        ret.append(np.round(smape(ndata, nforecasts), 2))
        ret.append(np.round(UStatistic(ndata, nforecasts), 2))
    else:
        steps_ahead_sampler = kwargs.get('steps_ahead_sampler', 1)
        nforecasts = []
        for k in np.arange(model.order, len(ndata)-steps_ahead,steps_ahead_sampler):
            sample = ndata[k - model.order: k]
            tmp = model.forecast_ahead(sample, steps_ahead, **kwargs)
            nforecasts.append(tmp[-1])

        start = model.order + steps_ahead -1
        ret.append(np.round(rmse(ndata[start:-1:steps_ahead_sampler], nforecasts), 2))
        ret.append(np.round(smape(ndata[start:-1:steps_ahead_sampler], nforecasts), 2))
        ret.append(np.round(UStatistic(ndata[start:-1:steps_ahead_sampler], nforecasts), 2))

    return ret


def get_interval_statistics(data, model, **kwargs):
    '''
    Condensate all measures for point interval forecasters
    :param data: test data
    :param model: FTS model with interval forecasting capability
    :param kwargs:
    :return: a list with the sharpness, resolution, coverage, .05 pinball mean,
    .25 pinball mean, .75 pinball mean and .95 pinball mean.
    '''

    steps_ahead = kwargs.get('steps_ahead', 1)

    ret = list()

    if steps_ahead == 1:
        forecasts = model.predict(data, **kwargs)
        ret.append(round(sharpness(forecasts), 2))
        ret.append(round(resolution(forecasts), 2))
        ret.append(round(coverage(data[model.order:], forecasts[:-1]), 2))
        ret.append(round(pinball_mean(0.05, data[model.order:], forecasts[:-1]), 2))
        ret.append(round(pinball_mean(0.25, data[model.order:], forecasts[:-1]), 2))
        ret.append(round(pinball_mean(0.75, data[model.order:], forecasts[:-1]), 2))
        ret.append(round(pinball_mean(0.95, data[model.order:], forecasts[:-1]), 2))
    else:
        forecasts = []
        for k in np.arange(model.order, len(data) - steps_ahead):
            sample = data[k - model.order: k]
            tmp = model.predict(sample, steps_ahead, **kwargs)
            forecasts.append(tmp[-1])

        start = model.order + steps_ahead -1
        ret.append(round(sharpness(forecasts), 2))
        ret.append(round(resolution(forecasts), 2))
        ret.append(round(coverage(data[model.order:], forecasts), 2))
        ret.append(round(pinball_mean(0.05, data[start:], forecasts), 2))
        ret.append(round(pinball_mean(0.25, data[start:], forecasts), 2))
        ret.append(round(pinball_mean(0.75, data[start:], forecasts), 2))
        ret.append(round(pinball_mean(0.95, data[start:], forecasts), 2))
    return ret


def get_distribution_statistics(data, model, **kwargs):
    '''
    Get CRPS statistic and time for a forecasting model
    :param data: test data
    :param model: FTS model with probabilistic forecasting capability
    :param kwargs:
    :return: a list with the CRPS and execution time
    '''
    steps_ahead = kwargs.get('steps_ahead', 1)

    ret = list()

    if steps_ahead == 1:
        _s1 = time.time()
        forecasts = model.forecast_distribution(data, **kwargs)
        _e1 = time.time()
        ret.append(round(crps(data, forecasts), 3))
        ret.append(round(_e1 - _s1, 3))
    else:
        skip = kwargs.get('steps_ahead_sampler', 1)
        forecasts = []
        _s1 = time.time()
        for k in np.arange(model.order, len(data) - steps_ahead, skip):
            sample = data[k - model.order: k]
            tmp = model.forecast_ahead_distribution(sample, steps_ahead, **kwargs)
            forecasts.append(tmp[-1])
        _e1 = time.time()

        start = model.order + steps_ahead
        ret.append(round(crps(data[start:-1:skip], forecasts), 3))
        ret.append(round(_e1 - _s1, 3))
    return ret


