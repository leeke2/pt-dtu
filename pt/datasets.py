import os
import pandas as pd
import re
import numpy as np
from enum import Enum

def __extract_gt_num_paths(path_to_directory, date=None, raw=False, permin=True):
	path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path_to_directory)
	regex = re.compile('paths_ts_from_g([0-9]{2})_to_g([0-9]{2})\.csv')
	files = os.listdir(path)

	data = []

	for file in files:
		if file.endswith('.csv'):
			res = regex.search(file)
			res = res.groups()

			df = pd.read_csv(path + '/%s' % file)
			df['from_dt'] = pd.to_datetime(df.from_dt)

			try:
				df['from_group'] = res[0]
				df['to_group'] = res[1]

				data.append(df)
			except:
				pass

	demands = pd.concat(data).reset_index(drop=True)
	demands.loc[demands.num_paths == 'None', 'num_paths'] = 0
	demands['from_group'] = demands.from_group.astype(int)
	demands['to_group'] = demands.to_group.astype(int)
	demands['num_paths'] = demands.num_paths.astype(float)

	# if raw:
	# 	return demands
	# else:
	# 	if date is None:
	# 		return demands.groupby(['from_group', 'to_group']).mean().reset_index().pivot(
	# 			index='from_group', columns='to_group', values='num_paths').fillna(0)
	# 	else:
	# 		return demands[demands.from_dt == date].pivot(
	# 			index='from_group', columns='to_group', values='num_paths').fillna(0)

	# 		if permin:
	# 			return od.index.values.tolist(), np.round(od.values/60.0, 2).tolist()
	# 		else:
	# 			return od.index.values.tolist(), np.round(od.values, 2).tolist()

	if raw:
		return demands
	else:
		if date is None:
			return demands[['from_dt', 'from_group', 'to_group', 'num_paths']]
		else:
			if permin:
				return np.round(demands.loc[demands.from_dt == date, ['from_group', 'to_group', column]].pivot(
					index='from_group', columns='to_group', values=column).fillna(0).values/60.0, 2).tolist()
			else:
				return np.round(demands.loc[demands.from_dt == date, ['from_group', 'to_group', column]].pivot(
					index='from_group', columns='to_group', values=column).fillna(0).values, 2).tolist()

def __extract_prediction_num_paths(path_to_directory, column='0.95', date=None, raw=False, permin=True):
	path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path_to_directory)
	regex = re.compile('predictions_from_g([0-9]{2})_to_g([0-9]{2})\.csv')
	files = os.listdir(path)

	data = []

	for file in files:
		if file.endswith('.csv'):
			res = regex.search(file)
			res = res.groups()

			df = pd.read_csv(path + '/%s' % file)
			df['from_dt'] = pd.to_datetime(df.t)

			try:
				df['from_group'] = res[0]
				df['to_group'] = res[1]

				data.append(df)
			except:
				pass

	demands = pd.concat(data).reset_index(drop=True)
	demands['from_group'] = demands.from_group.astype(int)
	demands['to_group'] = demands.to_group.astype(int)
	demands.drop(columns=['t'], inplace=True)
  
	if raw:
		return demands
	else:
		if date is None:
			return demands[['from_dt', 'from_group', 'to_group', column]]
		else:
			if permin:
				return np.round(demands.loc[demands.from_dt == date, ['from_group', 'to_group', column]].pivot(
					index='from_group', columns='to_group', values=column).fillna(0).values/60.0, 2).tolist()
			else:
				return np.round(demands.loc[demands.from_dt == date, ['from_group', 'to_group', column]].pivot(
					index='from_group', columns='to_group', values=column).fillna(0).values, 2).tolist()

class TS_CMX_AGG60(Enum):
	GT = "ground_truth_aggregated"
	P1 = "predictions1"
	P2 = "predictions2"
	P3 = "predictions3"
	P4 = "predictions4"

def load(dataset, date=None, array=True, column=0.95):
	if dataset == TS_CMX_AGG60.GT:
		data = __extract_gt_num_paths('data/aggregated/ground_truth_aggregated/ts_60')
	elif dataset == TS_CMX_AGG60.P1:
		data = __extract_prediction_num_paths('data/aggregated/predictions1', column=column)
	elif dataset == TS_CMX_AGG60.P2:
		data = __extract_prediction_num_paths('data/aggregated/predictions2', column=column)
	elif dataset == TS_CMX_AGG60.P3:
		data = __extract_prediction_num_paths('data/aggregated/predictions3', column=column)
	elif dataset == TS_CMX_AGG60.P4:
		data = __extract_prediction_num_paths('data/aggregated/predictions4', column=column)

	if date is not None:
		if dataset == TS_CMX_AGG60.GT:
			return np.round(data[data.from_dt == date].pivot(index='from_group', columns='to_group', values='num_paths').fillna(0).values/60.0, 2).tolist()
		else:
			return np.round(data[data.from_dt == date].pivot(index='from_group', columns='to_group', values=column).fillna(0).values/60.0, 2).tolist()
