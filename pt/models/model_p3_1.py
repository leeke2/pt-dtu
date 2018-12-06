import os

from pt import viz
from pt.models import BaseModel
from pt.models import Helper, linex
from plotly.offline import iplot, plot
import time
from itertools import combinations
import numpy as np

class Model_P3_1(BaseModel):

	def __init__(self, *args, **kwargs):
		BaseModel.__init__(self, *args, **kwargs)

		self.options = dict(
			max_transfer_waiting_time_constraint=False,
			waiting_time_objective_coefficient='demand'
		)

		self.customOptions = False

	def generate_variables(self):
		r_max = 1
		candidate_stops = [#[55.785470, 12.523041],
						   [55.786239, 12.522234],
						   [55.786541, 12.526961],
						   [55.789277, 12.523946],
						   [55.786431, 12.521428],
						   [55.785898, 12.520618],
						   [55.785138, 12.520728],
						   [55.784637, 12.520459],
						   [55.782099, 12.514132],
						   [55.782460, 12.519244],
						   [55.782226, 12.520035]]
		demand_centroids = [[55.786344,12.524316],[55.786344,12.524316],[55.786872,12.5259],[55.78944,12.525146],[55.786745,12.520469],[55.787486,12.518472],[55.787911,12.518621],[55.785438,12.519377],[55.785154,12.520434],[55.785241,12.518699],[55.783,12.512931],[55.781929,12.521461]]
		n_candidate_stops = len(candidate_stops)
		demands = [[0, 100, 3, 36, 0, 14, 13, 19, 42, 55, 5, 20],
			 [190, 0, 2, 25, 0, 18, 6, 8, 40, 37, 5, 4],
			 [13, 10, 0, 3, 0, 3, 0, 1, 5, 3, 0, 0],
			 [137, 1, 0, 0, 0, 10, 4, 1, 17, 34, 1, 1],
			 [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
			 [47, 9, 2, 4, 0, 0, 63, 0, 0, 6, 2, 0],
			 [46, 4, 0, 0, 0, 173, 0, 0, 0, 2, 2, 1],
			 [61, 2, 0, 1, 0, 1, 0, 0, 78, 116, 0, 0],
			 [116, 13, 1, 5, 0, 8, 0, 52, 0, 84, 16, 8],
			 [167, 6, 0, 6, 0, 33, 13, 52, 230, 0, 23, 6],
			 [1, 1, 0, 0, 0, 1, 0, 0, 7, 1, 0, 1],
			 [97, 55, 0, 6, 0, 3, 2, 2, 47, 39, 9, 0]]


		walkcosts = []

		for p in range(len(demands)):
			for q in range(len(demands)):
				for o in range(len(candidate_stops)):
					for d in range(len(candidate_stops)):
						wt = walktime(candidate_stops[o], demand_centroids[p]) + walktime(candidate_stops[d], demand_centroids[q])

						if wt <= 10:
							walkcosts.append(demands[p][q] * wt)
						else:
							walkcosts.append(0)

		self.vars.register('x', Helper.g('x_{},{},{}', 'B', 0, r_max, n_candidate_stops+1, n_candidate_stops+2))
		self.vars.register('xf', Helper.g('xf_{},{},{}', 'C', 0, r_max, n_candidate_stops+1, n_candidate_stops+1))
		self.vars.register('zxf', Helper.g('zxf_{},{},{}', 'C', 0, r_max, n_candidate_stops+1, n_candidate_stops+1))
		self.vars.register('zzxf', Helper.g('zzxf_{},{},{}', 'C', 0, r_max, n_candidate_stops+1, n_candidate_stops+1))

		# Frequency
		self.vars.register('f', Helper.g('f_{}', 'C', 0, r_max))

		# Route length (temporal length)
		self.vars.register('T', Helper.g('T_{}', 'C', 0, r_max))

		self.vars.register('s', Helper.g('s_{},{},{},{}', 'B', walkcosts, len(demands), len(demands), n_candidate_stops, n_candidate_stops))

		self.vars.register('q', Helper.g('q_{},{}', 'C', 0, r_max, n_candidate_stops))

		self.vars.register('delta', Helper.g('delta_{},{}', 'B', 0, r_max, n_candidate_stops))
		self.vars.register('deltaf', Helper.g('deltaf_{},{}', 'C', 0, r_max, n_candidate_stops))

		# 11*11*1*11*11
		self.vars.register('st', Helper.g('st_{},{},{},{}', 'C', np.repeat(np.array(demands).flatten(), n_candidate_stops * n_candidate_stops).tolist(), len(demands), len(demands), n_candidate_stops, n_candidate_stops))
		self.vars.register('t', Helper.g('t_{},{}', 'C', 0, n_candidate_stops, n_candidate_stops))
		self.vars.register('xs', Helper.g('xs_{},{},{},{},{}', 'B', 0, n_candidate_stops, n_candidate_stops, r_max, n_candidate_stops+1, n_candidate_stops+2))

	def generate_constraints(self):
		r_max = 1

		candidate_stops = [#[55.785470, 12.523041],
				   [55.786239, 12.522234],
				   [55.786541, 12.526961],
				   [55.789277, 12.523946],
				   [55.786431, 12.521428],
				   [55.785898, 12.520618],
				   [55.785138, 12.520728],
				   [55.784637, 12.520459],
				   [55.782099, 12.514132],
				   [55.782460, 12.519244],
				   [55.782226, 12.520035]]
		demand_centroids = [[55.786344,12.524316],[55.786344,12.524316],[55.786872,12.5259],[55.78944,12.525146],[55.786745,12.520469],[55.787486,12.518472],[55.787911,12.518621],[55.785438,12.519377],[55.785154,12.520434],[55.785241,12.518699],[55.783,12.512931],[55.781929,12.521461]]
		demands = [[0, 100, 3, 36, 0, 14, 13, 19, 42, 55, 5, 20],
					 [190, 0, 2, 25, 0, 18, 6, 8, 40, 37, 5, 4],
					 [13, 10, 0, 3, 0, 3, 0, 1, 5, 3, 0, 0],
					 [137, 1, 0, 0, 0, 10, 4, 1, 17, 34, 1, 1],
					 [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
					 [47, 9, 2, 4, 0, 0, 63, 0, 0, 6, 2, 0],
					 [46, 4, 0, 0, 0, 173, 0, 0, 0, 2, 2, 1],
					 [61, 2, 0, 1, 0, 1, 0, 0, 78, 116, 0, 0],
					 [116, 13, 1, 5, 0, 8, 0, 52, 0, 84, 16, 8],
					 [167, 6, 0, 6, 0, 33, 13, 52, 230, 0, 23, 6],
					 [1, 1, 0, 0, 0, 1, 0, 0, 7, 1, 0, 1],
					 [97, 55, 0, 6, 0, 3, 2, 2, 47, 39, 9, 0]]

		n_candidate_stops = len(candidate_stops)
		n_buses = 20

		costs = []

		for i1, (stop_x1, stop_y1) in enumerate([[0,0]] + candidate_stops):
			costs.append([])

			for i2, (stop_x2, stop_y2) in enumerate([[0,0]] + candidate_stops):
				costs[i1].append(275 * (abs(stop_x1 - stop_x2) + abs(stop_y1 - stop_y2)))

		vars = self.vars

		cs = []
		cns = []

		idx = 0
		for r in range(r_max):
			for i in range(n_candidate_stops + 1):
				for j in range(n_candidate_stops + 1):
					cns.append('XF1(%d)' % idx)
					cs.append((
						linex([(vars.xf[r][i][j],  1),
							   (vars.f[r],        -1)]),
						'L', 0, 0))

					cns.append('XF2(%d)' % idx)
					cs.append((
						linex([(vars.xf[r][i][j],   1),
							   (vars.x[r][i][j],  -60)]),
						'L', 0, 0))

					cns.append('XF3(%d)' % idx)
					cs.append((
						linex([(vars.xf[r][i][j],   1),
							   (vars.f[r],         -1),
							   (vars.x[r][i][j],  -60)]),
						'G', -60, 0))

					idx += 1

		for r in range(r_max):
			cns.append('C1(%d)' % r)
			cs.append((
				linex([(vars.x[r][0][j], 1)
					   for j in range(n_candidate_stops+1)]),
				'E', 1, 0))

		for r in range(r_max):
			cns.append('C2(%d)' % r)
			cs.append((
				linex([(vars.x[r][i][0], 1)
					   for i in range(n_candidate_stops+1)]),
				'L', 1, 0))

		idx = 0
		for r in range(r_max):
			for j in range(n_candidate_stops):
				cns.append('C3(%d)' % idx)
				cs.append((
					linex([(vars.x[r][i][j+1],  1)
						   for i in range(n_candidate_stops + 1)
						   if i != (j+1)] + 
						  [(vars.x[r][j+1][i], -1)
						   for i in range(n_candidate_stops + 2)
						   if i != (j+1)]),
					'E', 0, 0))

				idx += 1

		idx = 0
		for r in range(r_max):
			for j in range(n_candidate_stops + 1):
				cns.append('C4(%d)' % idx)
				cs.append((
					linex([(vars.x[r][i][j+1], 1)
						   for i in range(n_candidate_stops + 1)
						   if i != (j+1)]),
					'L', 1, 0))

		idx = 0
		for r in range(r_max):
			for i in range(n_candidate_stops):
				cns.append('C5(%d)' % idx)
				cs.append((
					linex([(vars.x[r][i+1][j], 1)
						   for j in range(n_candidate_stops + 1)
						   if (i+1) != j]),
					'L', 1, 0))

		idx = 0
		for r in range(r_max):
			cns.append('C7a(%d)' % idx)
			cs.append((
				linex([(vars.x[r][i+1][n_candidate_stops + 1], 1)
					   for i in range(n_candidate_stops)]),
				'L', 1, 0))

			cns.append('C7b(%d)' % idx)
			cs.append((
				linex([(vars.x[r][i+1][n_candidate_stops + 1], 1)
					   for i in range(n_candidate_stops)] +
					  [(vars.x[r][i][0], 1)
					   for i in range(n_candidate_stops + 1)]),
				'E', 1, 0))

		idx = 0
		for r in range(r_max):
			for i in range(n_candidate_stops):
				cns.append('C6(%d)' % idx)
				cs.append((linex([(vars.x[r][i+1][i+1], 1)]), 'E', 0, 0))

		idx = 0
		for r in range(r_max):
			for i in range(n_candidate_stops + 1):
				for j in range(n_candidate_stops + 1):
					cns.append('C7-1(%d)' % idx)
					cs.append((
						linex([(vars.zxf[r][i][j],  1),
							   (vars.xf[r][i][j],  -1)]),
						'L', 0, 0))

					cns.append('C7-2(%d)' % idx)
					cs.append((
						linex([(vars.zxf[r][i][j],  1),
							   (vars.x[r][0][0],   60)]),
						'L', 60, 0))

					cns.append('C7-3(%d)' % idx)
					cs.append((
						linex([(vars.zxf[r][i][j],  1),
							   (vars.xf[r][i][j],  -1),
							   (vars.x[r][0][0],   60)]),
						'G', 0, 0))

					idx += 1

		idx = 0
		for r in range(r_max):
			for i in range(n_candidate_stops + 1):
				for j in range(n_candidate_stops + 1):
					cns.append('zzxf1(%d)' % idx)
					cs.append((
						linex([(vars.zzxf[r][i][j],  1),
							   (vars.zxf[r][i][j],  -1)]),
						'L', 0, 0))

					cns.append('zzxf2(%d)' % idx)
					cs.append((
						linex([(vars.zzxf[r][i][j],  1)] +
							  [(vars.x[r][i+1][n_candidate_stops + 1], -60)
							   for i in range(n_candidate_stops)]),
						'L', 0, 0))

					cns.append('zzxf3(%d)' % idx)
					cs.append((
						linex([(vars.zzxf[r][i][j],  1),
							   (vars.zxf[r][i][j],  -1)] +
							  [(vars.x[r][i+1][n_candidate_stops + 1], -60)
							   for i in range(n_candidate_stops)]),
						'G', -60, 0))

					idx += 1

		cns.append('C8')
		cs.append((
			linex([(vars.zxf[r][i+1][j+1], costs[i+1][j+1])
				   for r in range(r_max)
				   for i in range(n_candidate_stops)
				   for j in range(n_candidate_stops)] +
				  [(vars.zzxf[r][i+1][j+1], costs[i+1][j+1])
				   for r in range(r_max)
				   for i in range(n_candidate_stops)
				   for j in range(n_candidate_stops)]),
			'L', n_buses, 0, 0))

		for r in range(r_max):
			cns.append('C9(%d)' % r)
			cs.append((
				linex([(vars.x[r][i+1][j+1], costs[i+1][j+1])
					   for i in range(n_candidate_stops)
					   for j in range(n_candidate_stops)
					   if i != j] + 
					  # [(vars.cxx[r][i][j], costs[i+1][j+1])
					  #  for i in range(n_candidate_stops)
					  #  for j in range(n_candidate_stops)
					  #  if i != j] +
					  [(vars.T[r], -1)]),
				'E', 0, 0))

		idx = 0
		for p in range(len(demands)):
			for o in range(len(candidate_stops)):
				if walktime(candidate_stops[o], demand_centroids[p]) >= 5:
					for q in range(len(demands)):
						for d in range(len(candidate_stops)):
							cns.append('FILTER(%d)' % idx)
							cs.append((linex([(vars.s[p][q][o][d], 1)]), 'E', 0, 0))

							idx += 1

		for q in range(len(demands)):
			for d in range(len(candidate_stops)):
				if walktime(candidate_stops[d], demand_centroids[q]) >= 5:
					for p in range(len(demands)):
						for o in range(len(candidate_stops)):
							cns.append('FILTER(%d)' % idx)
							cs.append((linex([(vars.s[p][q][o][d], 1)]), 'E', 0, 0))

							idx += 1
						

		idx = 0
		for p in range(len(demands)):
			for q in range(len(demands)):
				if demands[p][q] != 0:
					cns.append('S2(%d)' % idx)		
					cs.append((
						linex([(vars.s[p][q][c1][c2], 1)
							   for c1 in range(n_candidate_stops)
							   for c2 in range(n_candidate_stops)]),
						'E', 1, 0))

					idx += 1
				else:
					for c1 in range(n_candidate_stops):
					   	for c2 in range(n_candidate_stops):
							cns.append('S2N(%d)' % idx)	
							cs.append((linex([(vars.s[p][q][c1][c2], 1)]), 'E', 0, 0))
							idx += 1

				for c in range(n_candidate_stops):
					cns.append('S2N2(%d)' % idx)	
					cs.append((linex([(vars.s[p][q][c][c], 1)]), 'E', 0, 0))
					idx += 1

		# Sub tour elimination
		idx = 0
		for r in range(r_max):
			for i in range(n_candidate_stops):
				for j in range(n_candidate_stops):
					if i != j:
						cns.append('SUB(%d)' % idx)
						cs.append((
							linex([(vars.q[r][i],            1),
								   (vars.q[r][j],           -1),
								   (vars.x[r][i+1][j+1], 1000)]),
							'L', 999, 0))

						idx += 1

		idx = 0
		for r in range(r_max):
			for c2 in range(n_candidate_stops):
				cns.append("DEL(%d)" % idx)
				cs.append((
					linex([(vars.delta[r][c2],     1)] + 
						  [(vars.x[r][i+1][c2+1], -1)
						   for i in range(n_candidate_stops)]),
					'E', 0, 0))

				idx += 1

		idx = 0
		for r in range(r_max):
			for c2 in range(n_candidate_stops):
				cns.append("DELF1(%d)" % idx)
				cs.append((
					linex([(vars.deltaf[r][c2],  1),
						   (vars.f[r],          -1)]),
					'L', 0, 0))

				cns.append("DELF2(%d)" % idx)
				cs.append((
					linex([(vars.deltaf[r][c2],   1), 
						   (vars.delta[r][c2],  -60)]),
					'L', 0, 0))

				cns.append("DELF3(%d)" % idx)
				cs.append((
					linex([(vars.deltaf[r][c2],   1),
						   (vars.f[r],           -1),
						   (vars.delta[r][c2],  -60)]),
					'G', -60, 0))

				idx += 1

		idx = 0
		for c in range(n_candidate_stops):
			cns.append("CAP(%d)" % idx)
			cs.append((
				linex([(vars.deltaf[r][c],            40)
					   for r in range(r_max)] + 
					  [(vars.s[p][q][c1][c], -demands[p][q]/15.0)
					   for c1 in range(n_candidate_stops)
					   for p in range(len(demands))
					   for q in range(len(demands[0]))]),
				'G', 0, 0))

			idx += 1

		############################################################
		# Shortest path constraints
		############################################################
		idx = 0
		for o in range(n_candidate_stops):
			for d in range(n_candidate_stops):
				if o != d:
					cns.append('SP1(%d)' % idx)
					cs.append((
						linex([(vars.t[o][d], 1)] + 
							  [(vars.xs[o][d][r][i][j], -ridecost(i,j))
							   for r in range(r_max)
							   for i in range(n_candidate_stops+1)
							   for j in range(n_candidate_stops+2)]),
						'E', 0, 0))
				else:
					cns.append('SP1(%d)' % idx)
					cs.append((linex([(vars.t[o][d], 1)]), 'E', 0, 0))

				idx += 1



		idx = 0
		for o in range(n_candidate_stops):
			for d in range(n_candidate_stops):
				for r in range(r_max):
					for i in range(n_candidate_stops+1):
						for j in range(n_candidate_stops+2):
							if o != d:
								cns.append('SP2(%d)' % idx)
								cs.append((
									linex([(vars.xs[o][d][r][i][j],  1),
										   (vars.x[r][i][j],        -1)]),
									'L', 0, 0))
							else:
								cns.append('SP2(%d)' % idx)
								cs.append((
									linex([(vars.xs[o][d][r][i][j],  1)]), 'E', 0, 0))

							idx += 1


		idx = 0
		for o in range(n_candidate_stops):
			for d in range(n_candidate_stops):
				if o != d:
					for i in range(n_candidate_stops):
						rhs = 0

						if i == o:
							rhs = 1
						elif i == d:
							rhs = -1

						cns.append('SP3(%d)' % idx)
						cs.append((
							linex([(vars.xs[o][d][r][i+1][j],  1)
								   for r in range(r_max)
								   for j in range(n_candidate_stops + 2)
								   if j != (i+1)] + 
								  [(vars.xs[o][d][r][j][i+1], -1)
								   for r in range(r_max)
								   for j in range(n_candidate_stops + 1)
								   if j != (i+1)]),
							'E', rhs, 0))

						idx += 1

		idx = 0
		for p in range(len(demands)):
			for q in range(len(demands)):
				if demands[p][q] != 0:
					for o in range(n_candidate_stops):
						for d in range(n_candidate_stops):
							cns.append('ST1(%d)' % idx)		
							cs.append((
								linex([(vars.st[p][q][o][d],  1),
									   (vars.s[p][q][o][d],  -3*60)]),
								'L', 0, 0))

							cns.append('ST2(%d)' % idx)		
							cs.append((
								linex([(vars.st[p][q][o][d],  1),
									   (vars.t[o][d],        -1)]),
								'L', 0, 0))

							cns.append('ST3(%d)' % idx)		
							cs.append((
								linex([(vars.st[p][q][o][d],   1),
									   (vars.t[o][d],         -1),
									   (vars.s[p][q][o][d], -180)]),
								'G', -180, 0))

							idx += 1

				else:
					for o in range(n_candidate_stops):
						for d in range(n_candidate_stops):
							cns.append('STN(%d)' % idx)		
							cs.append((linex([(vars.st[p][q][o][d],  1)]), 'E', 0, 0))

							idx += 1




		idx = 0
		for p in range(len(demands)):
			for q in range(len(demands)):
				for o in range(len(candidate_stops)):
					for d in range(len(candidate_stops)):
						cns.append('FILT2-1(%d)' % idx)
						cs.append((
							linex([(vars.s[p][q][o][d], 1)] + 
								  [(vars.delta[r][o], -1)
								   for r in range(r_max)]),
							'L', 0, 0))
						idx += 1

						cns.append('FILT2-2(%d)' % idx)
						cs.append((
							linex([(vars.s[p][q][o][d], 1)] + 
								  [(vars.delta[r][d], -1)
								   for r in range(r_max)]),
							'L', 0, 0))

						idx += 1

		cs = zip(*cs)

		self._cp.linear_constraints.add(
            lin_expr=cs[0],
            senses=cs[1],
            rhs=cs[2],
            range_values=cs[3])

		self._cp.linear_constraints.set_names(enumerate(cns))


def walktime(x, y):
	return 1100 * (abs(x[0] - y[0]) + abs(x[1] - y[1]))

def ridetime(x, y, speed=20.0):
	dists = [[0, 142, 401, 496, 200, 160, 741, 683, 1161, 518, 475],
			 [142, 0, 543, 354, 191, 152, 733, 675, 1153, 510, 467],
			 [401, 543, 0, 855, 600, 561, 1142, 1084, 1552, 919, 876],
			 [496, 354, 855, 0, 545, 506, 1087, 1029, 1507, 864, 821],
			 [200, 191, 600, 545, 0, 102, 790, 732, 1210, 567, 524],
			 [160, 152, 561, 506, 102, 0, 751, 693, 1171, 528, 485],
			 [741, 733, 1142, 1087, 790, 751, 0, 58, 949, 312, 378],
			 [683, 675, 1084, 1029, 732, 693, 58, 0, 890, 254, 320],
			 [1161, 1153, 1552, 1507, 1404, 1302, 949, 890, 0, 637, 685],
			 [518, 510, 919, 864, 567, 528, 312, 254, 637, 0, 155],
			 [475, 467, 876, 821, 524, 485, 378, 320, 685, 155, 0]]

	return float(dists[x][y]) / speed / 1000.0 * 60.0

	# return 275 * (abs(x[0] - y[0]) + abs(x[1] - y[1]))

def ridecost(x, y, n_candidate_stops=11):
	if x == 0 or y == 0 or x == n_candidate_stops+1 or y == n_candidate_stops+1:
		return 0

	return ridetime(x-1,y-1)