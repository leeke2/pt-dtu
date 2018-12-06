# TODO: check vars.c

import os

from pt import viz
from pt.models import BaseModel
from pt.models import Helper, linex
from plotly.offline import iplot, plot
import time
from itertools import combinations, product
import numpy as np

class Model_P4(BaseModel):

	def __init__(self, *args, **kwargs):
		BaseModel.__init__(self, *args, **kwargs)

		self.options = dict(
			max_transfer_waiting_time_constraint=False,
			waiting_time_objective_coefficient='demand'
		)

		self.customOptions = False

	def generate_variables(self, **kwargs):
		r_max = kwargs['r_max']
		max_cap = kwargs['max_cap']
		candidate_stops = kwargs['candidate_stops']
		demand_centroids = kwargs['demand_centroids']
		demands = kwargs['demands']

		n_candidate_stops = len(candidate_stops)
		n_demands = len(demands)

		self.vars.register('x', Helper.g('x_{},{},{},{}', 'B', 0, n_demands, n_demands, n_candidate_stops+n_demands, n_candidate_stops+n_demands))
		self.vars.register('w', Helper.g('w_{},{}', 'C', 0, n_demands, n_demands))
		self.vars.register('r', Helper.g('r_{},{}', 'C', 0, n_demands, n_demands))

		# self.vars.register('w', Helper.g('w_{},{}', 'C', np.array(demands).flatten().tolist(), n_demands, n_demands))
		# self.vars.register('r', Helper.g('r_{},{}', 'C', np.array(demands).flatten().tolist(), n_demands, n_demands))

		self.vars.register('w', Helper.g('w_{},{}', 'C', 0, n_demands, n_demands))
		self.vars.register('r', Helper.g('r_{},{}', 'C', 0, n_demands, n_demands))

		# Route
		self.vars.register('rx', Helper.g('rx_{},{},{}', 'B', 0, r_max, n_candidate_stops+2, n_candidate_stops+2))
		self.vars.register('rx0', Helper.g('rx0_{},{},{}', 'B', 0, r_max, n_candidate_stops, n_candidate_stops))
		self.vars.register('rq', Helper.g('q_{},{}', 'C', 0, r_max, n_candidate_stops))

		self.vars.register('f', Helper.g('f_{}', 'C', 0, r_max))

		self.vars.register('c', Helper.g('c_{}', 'B', 0, r_max))
		self.vars.register('z1', Helper.g('z1_{},{},{}', 'C', 0, r_max, n_candidate_stops, n_candidate_stops))
		self.vars.register('z2', Helper.g('z2_{},{},{}', 'C', 0, r_max, n_candidate_stops, n_candidate_stops))
		self.vars.register('z3', Helper.g('z3_{},{},{}', 'C', 0, r_max, n_candidate_stops, n_candidate_stops))

		self.vars.register('s', Helper.g('s_{},{}', 'C', np.array(demands).flatten().tolist(), n_demands, n_demands))

		# self.vars.register('xx', Helper.g('xx_{},{},{},{},{}', 'B', 0, n_demands, n_demands, r_max, n_candidate_stops, n_candidate_stops))
		# self.vars.register('z3', Helper.g('z3_{},{},{},{}', 'B', 0, n_demands, n_demands, r_max, n_candidate_stops))
		# self.vars.register('z4', Helper.g('z4_{},{},{},{}', 'B', 0, n_demands, n_demands, r_max, n_candidate_stops))
		# self.vars.register('d', Helper.g('d_{},{}', 'C', 0, r_max, n_candidate_stops))

		# self.vars.register('fd', Helper.g('fd_{},{}', 'C', 0, r_max, n_candidate_stops))

		# self.vars.register('z3f', Helper.g('z3f_{},{},{},{}', 'C', 0, n_demands, n_demands, r_max, n_candidate_stops))
		# self.vars.register('z4f', Helper.g('z4f_{},{},{},{}', 'C', 0, n_demands, n_demands, r_max, n_candidate_stops))

	def generate_constraints(self, **kwargs):
		r_max = kwargs['r_max']
		max_cap = kwargs['max_cap']
		candidate_stops = kwargs['candidate_stops']
		demand_centroids = kwargs['demand_centroids']
		demands = kwargs['demands']
		n_buses = kwargs['n_buses']

		n_candidate_stops = len(candidate_stops)
		n_demands = len(demands)

		costs = []

		for i in range(n_demands + n_candidate_stops):
			costs.append([])

			for j in range(n_demands + n_candidate_stops):
				org = demand_centroids[i] if i < n_demands else candidate_stops[i-n_demands]
				des = demand_centroids[j] if j < n_demands else candidate_stops[j-n_demands]

				if i < n_demands or j < n_demands:
					costs[i].append(walktime(org, des))
				else:
					costs[i].append(ridetime(i - n_demands, j - n_demands))

		def it(spec):
			lengths = {'d': n_demands, 's': n_candidate_stops, 'n': n_demands+n_candidate_stops, 'r': r_max}

			if len(spec) == 1:
				return enumerate(range(lengths[spec]))

			return enumerate(product(*[range(lengths[x]) for x in spec]))

		vars = self.vars

		cs = []
		cns = []

		#///////////////////////////////////////////////////////////////////////
		#          Origin destination shortest path problem (ODSSP)             
		#///////////////////////////////////////////////////////////////////////

		for idx, (o, d) in it('dd'):
			if o != d:
				cns.append('A1(%d)' % idx)
				cs.append((
					linex([(vars.x[o][d][o][j], 1)
						   for j in range(n_demands + n_candidate_stops)
						   if j != o]),
					'E', 1, 0))
			else:
				cns.append('A1(%d)' % idx)
				cs.append((
					linex([(vars.x[o][d][o][j], 1)
						   for j in range(n_demands + n_candidate_stops)]),
					'E', 0, 0))

		for idx, (o, d) in it('dd'):
			if o != d:
				cns.append('A2(%d)' % idx)
				cs.append((
					linex([(vars.x[o][d][i][d], 1)
						   for i in range(n_demands + n_candidate_stops)
						   if i != d]),
					'E', 1, 0))
			else:
				cns.append('A2(%d)' % idx)
				cs.append((
					linex([(vars.x[o][d][i][d], 1)
						   for i in range(n_demands + n_candidate_stops)]),
					'E', 0, 0))


		for idx, (o, d, i) in it('ddn'):
			if o != d:
				rhs = 0

				if i == o:
					rhs = 1
				elif i == d:
					rhs = -1

				cns.append('A3(%d)' % idx)
				cs.append((
					linex([(vars.x[o][d][i][j], 1)
						   for j in range(n_demands + n_candidate_stops)
						   if j != i] + 
						  [(vars.x[o][d][j][i], -1)
						   for j in range(n_demands + n_candidate_stops)
						   if j != i]),
					'E', rhs, 0))

		for idx, (o,d,j) in it('dds'):
			cns.append('A4(%d)' % idx)
			cs.append((
				linex([(vars.x[o][d][i][j+n_demands], 1)
					   for i in range(n_demands)] +
					  [(vars.x[o][d][j+n_demands][i], 1)
					   for i in range(n_demands)]),
				'L', 1, 0))

		for idx, (o,d) in it('dd'):
			if o != d:
				cns.append('A5(%d)' % idx)
				cs.append((
					linex([(vars.w[o][d], 1)] + 
						  [(vars.x[o][d][i][j], -costs[i][j])
						   for i in range(n_demands + n_candidate_stops)
						   for j in range(n_demands + n_candidate_stops)
						   if i == o or j == d]),
					'E', 0, 0))

		for idx, (o,d) in it('dd'):
			if o != d:
				cns.append('A6(%d)' % idx)
				cs.append((
					linex([(vars.r[o][d], 1)] + 
						  [(vars.x[o][d][i+n_demands][j+n_demands], -costs[i+n_demands][j+n_demands])
						   for i in range(n_candidate_stops)
						   for j in range(n_candidate_stops)]),
					'E', 0, 0))

		for idx, (o,d,j) in it('dds'):
			if costs[o][j+n_demands] > 5:
				cns.append('A7(%d)' % idx)
				cs.append((linex([(vars.x[o][d][o][j+n_demands], 1)]), 'E', 0, 0))

		for idx, (o,d,i) in it('dds'):
			if costs[i+n_demands][d] > 5:
				cns.append('A8(%d)' % idx)
				cs.append((linex([(vars.x[o][d][i+n_demands][d], 1)]), 'E', 0, 0))

		for idx, (o,d,i,j) in it('ddnd'):
			if j != d:
				cns.append('A9(%d)' % idx)
				cs.append((linex([(vars.x[o][d][i][j], 1)]), 'E', 0, 0))

		for idx, (o,d,i,j) in it('dddn'):
			if i != o:
				cns.append('A10(%d)' % idx)
				cs.append((linex([(vars.x[o][d][i][j], 1)]), 'E', 0, 0))

		for idx, (o,d) in it('dd'):
			if o != d:
				if costs[o][d] == 0:
					f = 1
				else:
					f = 1.0/costs[o][d]

				cns.append(('A11-1(%d)' % idx))
				cs.append((
					linex([(vars.s[o][d], 1),
						   (vars.r[o][d], 1-f),
						   (vars.w[o][d], 1-f)]),
					'E', costs[o][d]*(1-f), 0))

				cns.append(('A12(%d)' % idx))
				cs.append((
					linex([(vars.r[o][d], 1),
						   (vars.w[o][d], 1)]),
					'L', costs[o][d], 0))
			else:
				cns.append(('A11-2(%d)' % idx))
				cs.append((linex([(vars.s[o][d], 1)]),'E', 0, 0))



		#///////////////////////////////////////////////////////////////////////
		#            Transit route network design problem (TRNDP)
		#///////////////////////////////////////////////////////////////////////

		for idx, (r,i,j) in it('rss'):
			cns.append('B1(%d)' % idx)
			cs.append((
				linex([(vars.rx0[r][i][j], 1),
					   (vars.c[r], 1)]),
				'L', 1, 0))

		for idx, (i,j) in it('ss'):
			cns.append('B2(%d)' % idx)
			cs.append((
				linex([(vars.rx[r][i][j], 1)
					   for r in range(r_max)] + 
					  [(vars.rx0[r][i][j], 1)
					   for r in range(r_max)] +
					  [(vars.x[o][d][i+n_demands][j+n_demands], -1.0/n_demands/n_demands)
					   for o in range(n_demands)
					   for d in range(n_demands)]),
				'G', 0, 0))

		for idx, (r) in it('r'):
			cns.append('B3(%d)' % idx)
			cs.append((
				linex([(vars.rx[r][n_candidate_stops][j], 1)
					   for j in range(n_candidate_stops+1)]),
				'E', 1, 0))

		for idx, (r) in it('r'):
			cns.append('B4(%d)' % idx)
			cs.append((
				linex([(vars.rx[r][i][n_candidate_stops], 1)
					   for i in range(n_candidate_stops+1)] +
					  [(vars.rx[r][i][n_candidate_stops+1], 1)
					   for i in range(n_candidate_stops)]),
				'E', 1, 0))

		for idx, (r,i) in it('rs'):
			cns.append('B5(%d)' % idx)
			cs.append((
				linex([(vars.rx[r][i][j],  1)
					   for j in range(n_candidate_stops+2)
					   if i != j] +
					  [(vars.rx[r][j][i], -1)
					   for j in range(n_candidate_stops+2)
					   if i != j]),
				'E', 0, 0))

		for idx, (r,i) in it('rs'):
			cns.append('B6(%d)' % idx)
			cs.append((
				linex([(vars.rx[r][j][i], 1)
					   for j in range(n_candidate_stops+2)]),
				'L', 1, 0))

		for idx, (r,i) in it('rs'):
			cns.append('B7(%d)' % idx)
			cs.append((
				linex([(vars.rx[r][i][j], 1)
					   for j in range(n_candidate_stops+2)]),
				'L', 1, 0))

		for idx, (r,i) in it('rs'):
			cns.append('B8(%d)' % idx)
			cs.append((linex([(vars.rx[r][i][i], 1)]), 'E', 0, 0))

		for idx, (r) in it('r'):
			cns.append('B9(%d)' % r)
			cs.append((linex([(vars.rx[r][n_candidate_stops][n_candidate_stops+1], 1)]), 'E', 0, 0))

		for idx, (r,i,j) in it('rss'):
			if i != j:
				cns.append('B10(%d)' % idx)
				cs.append((
					linex([(vars.rq[r][i],       1),
						   (vars.rq[r][j],      -1),
						   (vars.rx[r][i][j], 1000)]),
					'L', 999, 0))


		for idx, (r,i) in it('rs'):
			if i != 0:
				cns.append('B11-1(%d)' % idx)
				cs.append((
					linex([(vars.rx[r][i][n_candidate_stops], 1)] +
						  [(vars.rx[r][k][n_candidate_stops], 1)
						    for k in range(n_candidate_stops+1)
						    if k < i]),
					'L', 1, 0))

		for idx, (r,i) in it('rs'):
			if i != 0:
				cns.append('B11-2(%d)' % idx)
				cs.append((
					linex([(vars.rx[r][i][n_candidate_stops],  1)] +
						  [(vars.rx[r][j][i],                 -1)
						   for j in range(n_candidate_stops+1)]),
					'L', 0, 0))

		for idx, (r,i) in it('rs'):
			if i != 0:
				cns.append('B11-3(%d)' % idx)
				cs.append((
					linex([(vars.rx[r][i][n_candidate_stops], 1),
						   (vars.c[r],                        1)]),
					'L', 1, 0))

		for idx, (r,i) in it('rs'):
			if i != 0:
				cns.append('B11-4(%d)' % idx)
				cs.append((
					linex([(vars.rx[r][i][n_candidate_stops],  1),
						   (vars.c[r],                         1)] +
						  [(vars.rx[r][k][n_candidate_stops],  1)
						    for k in range(n_candidate_stops+1)
						    if k < i] +
						  [(vars.rx[r][j][i],                 -1)
						   for j in range(n_candidate_stops+1)]),
					'G', 0, 0))

		for idx, (r,i,j) in it('rss'):
			cns.append('B12-1(%d)' % idx)
			cs.append((
				linex([(vars.rx0[r][i][j],                 1),
					   (vars.rx[r][i][n_candidate_stops], -1),
					   (vars.rx[r][n_candidate_stops][j], -1)]),
				'G', -1, 0))

		for idx, (r,i,j) in it('rss'):
			cns.append('B12-2(%d)' % idx)
			cs.append((
				linex([(vars.rx0[r][i][j],                 1),
					   (vars.rx[r][i][n_candidate_stops], -1)]),
				'L', 0, 0))

		for idx, (r,i,j) in it('rss'):
			cns.append('B12-3(%d)' % idx)
			cs.append((
				linex([(vars.rx0[r][i][j],                 1),
					   (vars.rx[r][n_candidate_stops][j], -1)]),
				'L', 0, 0))

		for idx, (r,i,j) in it('rss'):
			cns.append('B13(%d)' % idx)
			cs.append((
				linex([(vars.rx[r][i][j],  1),
					   (vars.rx0[r][i][j], 1)]),
				'L', 1, 0))

		#///////////////////////////////////////////////////////////////////////
		#                Frequency determination problem (FDP)
		#///////////////////////////////////////////////////////////////////////

		for idx, (r) in it('r'):
			cns.append('C1(%d)' % r)
			cs.append((
				linex([(vars.c[r], 1)] +
					  [(vars.rx[r][i][n_candidate_stops+1], -1)
					   for i in range(n_candidate_stops)]),
				'E', 0, 0))

		for idx, (i,j) in it('ss'):
			if i != j:
				cns.append('C3-1(%d)' % idx)
				cs.append((
					linex([(vars.x[o][d][i+n_demands][j+n_demands], demands[o][d])
						   for o in range(n_demands)
						   for d in range(n_demands)] + 
						  [(vars.z1[r][i][j], -max_cap)
						   for r in range(r_max)] + 
						  [(vars.z3[r][i][j], -max_cap)
						   for r in range(r_max)]),
					'L', 0, 0))

		for idx, (r,i,j) in it('rss'):
			if i != j:
				cns.append('C3-2(%d)' % idx)
				cs.append((
					linex([(vars.z1[r][i][j],   1),
						   (vars.rx[r][i][j], -60)]),
					'L', 0, 0))

		for idx, (r,i,j) in it('rss'):
			if i != j:
				cns.append('C3-3(%d)' % idx)
				cs.append((
					linex([(vars.z1[r][i][j],  1),
						   (vars.f[r],        -1)]),
					'L', 0, 0))

		for idx, (r,i,j) in it('rss'):
			if i != j:
				cns.append('C3-4(%d)' % idx)
				cs.append((
					linex([(vars.z1[r][i][j],   1),
						   (vars.f[r],         -1),
						   (vars.rx[r][i][j], -60)]),
					'G', -60, 0))

		for idx, (r,i,j) in it('rss'):
			if i != j:
				cns.append('C3-5(%d)' % idx)
				cs.append((
					linex([(vars.z3[r][i][j],   1),
						   (vars.rx0[r][i][j], -60)]),
					'L', 0, 0))

		for idx, (r,i,j) in it('rss'):
			if i != j:
				cns.append('C3-6(%d)' % idx)
				cs.append((
					linex([(vars.z3[r][i][j],  1),
						   (vars.f[r],        -1)]),
					'L', 0, 0))

		for idx, (r,i,j) in it('rss'):
			if i != j:
				cns.append('C3-7(%d)' % idx)
				cs.append((
					linex([(vars.z3[r][i][j],   1),
						   (vars.f[r],         -1),
						   (vars.rx0[r][i][j], -60)]),
					'G', -60, 0))

		for idx, (r,i,j) in it('rss'):
			if i != j:
				cns.append('C3-8(%d)' % idx)
				cs.append((
					linex([(vars.z3[r][i][j], 1),
						   (vars.c[r],        1)]),
					'L', 1, 0))

		cns.append('C4-1')
		cs.append((
			linex([(vars.z1[r][i][j], 1)
				   for r in range(r_max)
				   for i in range(n_candidate_stops)
				   for j in range(n_candidate_stops)
				   if i != j] + 
				  [(vars.z2[r][i][j], 1)
				   for r in range(r_max)
				   for i in range(n_candidate_stops)
				   for j in range(n_candidate_stops)
				   if i != j]),
			'L', n_buses, 0))

		for idx, (r,i,j) in it('rss'):
			if i != j:
				cns.append('C4-2(%d)' % idx)
				cs.append((
					linex([(vars.z2[r][i][j],   1),
						   (vars.rx[r][i][j], -60)]),
					'L', 0, 0))

		for idx, (r,i,j) in it('rss'):
			if i != j:
				cns.append('C4-3(%d)' % idx)
				cs.append((
					linex([(vars.z2[r][i][j],   1),
						   (vars.c[r],        -60)]),
					'L', 0, 0))

		for idx, (r,i,j) in it('rss'):
			if i != j:
				cns.append('C4-4(%d)' % idx)
				cs.append((
					linex([(vars.z2[r][i][j],  1),
						   (vars.f[r],        -1)]),
					'L', 0, 0))

		for idx, (r,i,j) in it('rss'):
			if i != j:
				cns.append('C4-5(%d)' % idx)
				cs.append((
					linex([(vars.z2[r][i][j],   1),
						   (vars.f[r],         -1),
						   (vars.rx[r][i][j], -60),
						   (vars.c[r],        -60)]),
					'G', -120, 0))

		for idx, (r) in it('r'):
			cns.append('C5(%d)'  % idx)
			cs.append((linex([(vars.f[r], 1)]), 'G', 0.2, 0))

		cs = zip(*cs)

		self._cp.linear_constraints.add(
            lin_expr=cs[0],
            senses=cs[1],
            rhs=cs[2],
            range_values=cs[3])

		self._cp.linear_constraints.set_names(enumerate(cns))


def walktime(x, y):
	return 1100 * (abs(x[0] - y[0]) + abs(x[1] - y[1]))

def ridetime(x, y, speed=15.0):
	dists = [[0, 348, 650, 361, 212, 1032, 1167, 1130, 511, 784],
			 [348, 0, 998, 709, 560, 1380, 1515, 1478, 859, 1132],
			 [659, 1007, 0, 298, 447, 664, 799, 986, 952, 1225],
			 [361, 709, 289, 0, 149, 671, 806, 993, 654, 927],
			 [212, 560, 438, 149, 0, 820, 955, 1124, 505, 778],
			 [1016, 1364, 660, 655, 804, 0, 309, 323, 1309, 885],
			 [1151, 1499, 795, 790, 939, 309, 0, 632, 481, 576],
			 [1130, 1478, 983, 978, 1127, 323, 632, 0, 618, 893],
			 [511, 859, 943, 654, 505, 941, 481, 618, 0, 389],
			 [784, 1132, 1216, 927, 778, 1216, 576, 893, 389, 0]]
	# dists = [[0, 142, 401, 496, 200, 160, 741, 683, 1161, 518, 475],
	# 		 [142, 0, 543, 354, 191, 152, 733, 675, 1153, 510, 467],
	# 		 [401, 543, 0, 855, 600, 561, 1142, 1084, 1552, 919, 876],
	# 		 [496, 354, 855, 0, 545, 506, 1087, 1029, 1507, 864, 821],
	# 		 [200, 191, 600, 545, 0, 102, 790, 732, 1210, 567, 524],
	# 		 [160, 152, 561, 506, 102, 0, 751, 693, 1171, 528, 485],
	# 		 [741, 733, 1142, 1087, 790, 751, 0, 58, 949, 312, 378],
	# 		 [683, 675, 1084, 1029, 732, 693, 58, 0, 890, 254, 320],
	# 		 [1161, 1153, 1552, 1507, 1404, 1302, 949, 890, 0, 637, 685],
	# 		 [518, 510, 919, 864, 567, 528, 312, 254, 637, 0, 155],
	# 		 [475, 467, 876, 821, 524, 485, 378, 320, 685, 155, 0]]

	return float(dists[x][y]) / speed / 1000.0 * 60.0

	# return 275 * (abs(x[0] - y[0]) + abs(x[1] - y[1]))

def ridecost(x, y, n_candidate_stops=11):
	if x == 0 or y == 0 or x == n_candidate_stops+1 or y == n_candidate_stops+1:
		return 0

	return ridetime(x-1,y-1)