# TODO: check vars.c

import os

from pt import viz
from pt.models import BaseModel
from pt.models import Helper, linex
from plotly.offline import iplot, plot
import time
from itertools import combinations
import numpy as np

class Model_P4(BaseModel):

	def __init__(self, *args, **kwargs):
		BaseModel.__init__(self, *args, **kwargs)

		self.options = dict(
			max_transfer_waiting_time_constraint=False,
			waiting_time_objective_coefficient='demand'
		)

		self.customOptions = False

	def generate_variables(self):
		r_max = 1
		max_cap = 30
		candidate_stops = [[55.785470, 12.523041],
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
		n_candidate_stops = len(candidate_stops)
		demand_centroids = [[55.786344,12.524316],[55.786344,12.524316],[55.786872,12.5259],[55.78944,12.525146],[55.786745,12.520469],[55.787486,12.518472],[55.787911,12.518621],[55.785438,12.519377],[55.785154,12.520434],[55.785241,12.518699],[55.782330, 12.513640],[55.781929,12.521461]]
		demands = [[0.0, 59.04, 20.34, 17.0, 0.0, 15.87, 8.27, 2.94, 23.92, 34.73, 1.91, 15.26],
				   [47.32, 0.0, 7.31, 8.7, 0.0, 8.66, 5.07, 1.23, 11.37, 14.67, 0.97, 6.27],
				   [14.09, 7.53, 0.0, 4.51, 0.0, 2.02, 1.23, 0.39, 3.78, 3.75, 0.24, 1.67],
				   [14.64, 8.1, 4.75, 0.0, 0.0, 1.13, 0.81, 0.4, 2.07, 2.76, 0.27, 1.53],
				   [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
				   [14.1, 8.61, 2.06, 1.38, 0.0, 0.0, 20.35, 1.28, 6.48, 16.1, 0.25, 1.72],
				   [7.06, 4.96, 1.13, 1.09, 0.0, 20.74, 0.0, 0.39, 2.31, 6.38, 0.15, 0.86],
				   [2.3, 1.03, 0.34, 0.23, 0.0, 0.99, 0.22, 0.0, 5.55, 5.08, 0.07, 0.37],
				   [19.67, 11.18, 3.53, 1.91, 0.0, 7.05, 2.24, 6.45, 0.0, 28.64, 0.82, 4.56],
				   [31.91, 14.58, 3.91, 2.84, 0.0, 17.88, 6.71, 7.28, 28.09, 0.0, 1.15, 7.68],
				   [1.72, 0.94, 0.23, 0.3, 0.0, 0.22, 0.12, 0.1, 0.83, 1.13, 0.0, 1.2],
				   [13.15, 5.68, 1.69, 1.78, 0.0, 1.63, 0.82, 0.4, 4.24, 7.15, 1.11, 0.0]]


		self.vars.register('x', Helper.g('x_{},{},{},{}', 'B', 1, len(demands), len(demands), n_candidate_stops+len(demands), n_candidate_stops+len(demands)))
		self.vars.register('w', Helper.g('w_{},{}', 'C', np.array(demands).flatten().tolist(), len(demands), len(demands)))
		self.vars.register('r', Helper.g('r_{},{}', 'C', np.array(demands).flatten().tolist(), len(demands), len(demands)))

		# Route
		self.vars.register('rx', Helper.g('rx_{},{},{}', 'B', 1, r_max, n_candidate_stops+2, n_candidate_stops+2))
		self.vars.register('rx0', Helper.g('rx0_{},{},{}', 'B', 1, r_max, n_candidate_stops, n_candidate_stops))
		self.vars.register('rq', Helper.g('q_{},{}', 'C', 0, r_max, n_candidate_stops))

		self.vars.register('f', Helper.g('f_{}', 'C', 0, r_max))

		self.vars.register('c', Helper.g('c_{}', 'B', 0, r_max))
		self.vars.register('z1', Helper.g('z1_{},{},{}', 'C', 1, r_max, n_candidate_stops, n_candidate_stops))
		self.vars.register('z2', Helper.g('z2_{},{},{}', 'C', 1, r_max, n_candidate_stops, n_candidate_stops))

	def generate_constraints(self):
		r_max = 1
		max_cap = 30
		n_buses = 5

		candidate_stops = [[55.785470, 12.523041],[55.786239, 12.522234],[55.786541, 12.526961],[55.789277, 12.523946],[55.786431, 12.521428],[55.785898, 12.520618],[55.785138, 12.520728],[55.784637, 12.520459],[55.782099, 12.514132],[55.782460, 12.519244],[55.782226, 12.520035]]
		demand_centroids = [[55.786344,12.524316],[55.786344,12.524316],[55.786872,12.5259],[55.78944,12.525146],[55.786745,12.520469],[55.787486,12.518472],[55.787911,12.518621],[55.785438,12.519377],[55.785154,12.520434],[55.785241,12.518699],[55.782330, 12.513640],[55.781929,12.521461]]
		demands = [[0.0, 59.04, 20.34, 17.0, 0.0, 15.87, 8.27, 2.94, 23.92, 34.73, 1.91, 15.26],[47.32, 0.0, 7.31, 8.7, 0.0, 8.66, 5.07, 1.23, 11.37, 14.67, 0.97, 6.27],[14.09, 7.53, 0.0, 4.51, 0.0, 2.02, 1.23, 0.39, 3.78, 3.75, 0.24, 1.67],[14.64, 8.1, 4.75, 0.0, 0.0, 1.13, 0.81, 0.4, 2.07, 2.76, 0.27, 1.53],[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],[14.1, 8.61, 2.06, 1.38, 0.0, 0.0, 20.35, 1.28, 6.48, 16.1, 0.25, 1.72],[7.06, 4.96, 1.13, 1.09, 0.0, 20.74, 0.0, 0.39, 2.31, 6.38, 0.15, 0.86],[2.3, 1.03, 0.34, 0.23, 0.0, 0.99, 0.22, 0.0, 5.55, 5.08, 0.07, 0.37],[19.67, 11.18, 3.53, 1.91, 0.0, 7.05, 2.24, 6.45, 0.0, 28.64, 0.82, 4.56],[31.91, 14.58, 3.91, 2.84, 0.0, 17.88, 6.71, 7.28, 28.09, 0.0, 1.15, 7.68],[1.72, 0.94, 0.23, 0.3, 0.0, 0.22, 0.12, 0.1, 0.83, 1.13, 0.0, 1.2],[13.15, 5.68, 1.69, 1.78, 0.0, 1.63, 0.82, 0.4, 4.24, 7.15, 1.11, 0.0]]
		
		# demands = [[0, 100, 3, 36, 0, 14, 13, 19, 42, 55, 5, 20], [190, 0, 2, 25, 0, 18, 6, 8, 40, 37, 5, 4], [13, 10, 0, 3, 0, 3, 0, 1, 5, 3, 0, 0], [137, 1, 0, 0, 0, 10, 4, 1, 17, 34, 1, 1], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [47, 9, 2, 4, 0, 0, 63, 0, 0, 6, 2, 0], [46, 4, 0, 0, 0, 173, 0, 0, 0, 2, 2, 1], [61, 2, 0, 1, 0, 1, 0, 0, 78, 116, 0, 0], [116, 13, 1, 5, 0, 8, 0, 52, 0, 84, 16, 8], [167, 6, 0, 6, 0, 33, 13, 52, 230, 0, 23, 6], [1, 1, 0, 0, 0, 1, 0, 0, 7, 1, 0, 1], [97, 55, 0, 6, 0, 3, 2, 2, 47, 39, 9, 0]]

		n_candidate_stops = len(candidate_stops)
		n_demands = len(demands)

		costs = []

		for i in range(len(demands) + n_candidate_stops):
			costs.append([])

			for j in range(len(demands) + n_candidate_stops):
				org = demand_centroids[i] if i < len(demands) else candidate_stops[i-len(demands)]
				des = demand_centroids[j] if j < len(demands) else candidate_stops[j-len(demands)]

				if i < len(demands) or j < len(demands):
					costs[i].append(walktime(org, des))
				else:
					costs[i].append(ridetime(i - len(demands), j - len(demands)))

		dd = enumerate([(x,y) for x in range(n_demands) for y in range(n_demands)])
		dd_neq = enumerate([(x,y) for x in range(n_demands) for y in range(n_demands) if x != y])
		dd_eq = enumerate([(x,x) for x in range(n_demands)])

		ddn = enumerate([(x,y,p) for x in range(n_demands) for y in range(n_demands) for p in range(n_demands + n_candidate_stops)])

		vars = self.vars

		cs = []
		cns = []

		for idx, (o, d) in dd:
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

		for idx, (o, d) in dd:
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


		# idx = 0
		# for o in range(n_demands):
		# 	for d in range(n_demands):
		# 		if o != d:
		# 			for i in range(n_demands + n_candidate_stops):
		for idx, (o, d, i) in ddn:
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
						   if i != j] + 
						  [(vars.x[o][d][j][i], -1)
						   for j in range(n_demands + n_candidate_stops)
						   if i != j]),
					'E', rhs, 0))

						# idx += 1

		idx = 0
		for o in range(n_demands):
			for d in range(n_demands):
				for j in range(n_candidate_stops):
					cns.append('A4(%d)' % idx)
					cs.append((
						linex([(vars.x[o][d][i][j+n_demands], 1)
							   for i in range(n_demands)] +
							  [(vars.x[o][d][j+n_demands][i], 1)
							   for i in range(n_demands)]),
						'L', 1, 0))

					idx += 1

		idx = 0
		for o in range(n_demands):
			for d in range(n_demands):
				if o != d:
					cns.append('A5(%d)' % idx)
					cs.append((
						linex([(vars.w[o][d], 1)] + 
							  [(vars.x[o][d][i][j], -costs[i][j])
							   for i in range(n_demands + n_candidate_stops)
							   for j in range(n_demands + n_candidate_stops)
							   if i == o or j == d]),
						'E', 0, 0))

					idx += 1

		idx = 0
		for o in range(n_demands):
			for d in range(n_demands):
				if o != d:
					cns.append('A6(%d)' % idx)
					cs.append((
						linex([(vars.r[o][d], 1)] + 
							  [(vars.x[o][d][i][j], -costs[i][j])
							   for i in range(n_demands + n_candidate_stops)
							   for j in range(n_demands + n_candidate_stops)
							   if i != o and j != d]),
						'E', 0, 0))

					idx += 1

		idx = 0
		for o in range(n_demands):
			for d in range(n_demands):
				# cns.append('TIMEGUARANTEE(%d)' % idx)
				# cs.append((
				# 	linex([(vars.r[o][d], 1),
				# 		   (vars.w[o][d], 1)]),
				# 	'L', 20, 0))

				# for j in range(n_demands):
				# 	cns.append('MAXWALK(%d)' % idx)
				# 	cs.append((linex([(vars.x[o][d][o][j], 1)]), 'E', 0, 0))

				# 	idx += 1

				# for i in range(n_demands):
				# 	cns.append('MAXWALK(%d)' % idx)
				# 	cs.append((linex([(vars.x[o][d][i][d], 1)]), 'E', 0, 0))
				# 	idx += 1

				for j in range(n_candidate_stops):
					if costs[o][j+n_demands] > 5:
						cns.append('A7(%d)' % idx)
						cs.append((linex([(vars.x[o][d][o][j+n_demands], 1)]), 'E', 0, 0))

						idx += 1

				for i in range(n_candidate_stops):
					if costs[d][i+n_demands] > 5:
						cns.append('A8(%d)' % idx)
						cs.append((linex([(vars.x[o][d][i+n_demands][d], 1)]), 'E', 0, 0))

						idx += 1

				for i in range(n_demands + n_candidate_stops):
					for j in range(n_demands):
						if j != d:
							cns.append('A9(%d)' % idx)
							cs.append((linex([(vars.x[o][d][i][j], 1)]), 'E', 0, 0))

							idx += 1

				for i in range(n_demands):
					for j in range(n_demands + n_candidate_stops):
						if i != o:
							cns.append('A10(%d)' % idx)
							cs.append((linex([(vars.x[o][d][i][j], 1)]), 'E', 0, 0))

						idx += 1

		idx = 0
		for r in range(r_max):
			# for i in range(n_candidate_stops):
			# 	for j in range(n_candidate_stops):
			# 		cns.append('B0(%d)' % idx)
			# 		cs.append((
			# 			linex([(vars.rx[r][i][j], 1)] + 
			# 				  [(vars.x[o][d][i+n_demands][j+n_demands], -1)
			# 				   for o in range(len(demands))
			# 				   for d in range(len(demands))]),
			# 			'L', 0, 0))

			# 		idx += 1

			# idx = 0
			# for i in range(n_candidate_stops):
			# 	for j in range(n_candidate_stops):
			# 		cns.append('B0-1(%d)' % idx)
			# 		cs.append((
			# 			linex([(vars.rx0[r][i][j], 1)] + 
			# 				  [(vars.x[o][d][i+n_demands][j+n_demands], -1)
			# 				   for o in range(len(demands))
			# 				   for d in range(len(demands))]),
			# 			'L', 0, 0))

			# 		idx += 1

			idx = 0
			for r in range(r_max):
				for i in range(n_candidate_stops):
					for j in range(n_candidate_stops):
						cns.append('B0-2(%d)' % idx)
						cs.append((
							linex([(vars.rx0[r][i][j], 1),
								   (vars.c[r], 1)]),
							'L', 1, 0))

						idx += 1

		idx = 0
		for i in range(n_candidate_stops):
			for j in range(n_candidate_stops):
				cns.append('B1(%d)' % idx)
				cs.append((
					linex([(vars.rx[r][i][j], 1)
						   for r in range(r_max)] + 
						  [(vars.rx0[r][i][j], 1)
						   for r in range(r_max)] +
						  [(vars.x[o][d][i+n_demands][j+n_demands], -1.0/n_demands/n_demands)
						   for o in range(n_demands)
						   for d in range(n_demands)]),
					'G', 0, 0))
				idx += 1

		idx = 0
		for r in range(r_max):
			cns.append('B2(%d)' % idx)
			cs.append((
				linex([(vars.rx[r][n_candidate_stops][j], 1)
					   for j in range(n_candidate_stops+1)]),
				'E', 1, 0))

			cns.append('B3(%d)' % idx)
			cs.append((
				linex([(vars.rx[r][i][n_candidate_stops], 1)
					   for i in range(n_candidate_stops+1)] +
					  [(vars.rx[r][i][n_candidate_stops+1], 1)
					   for i in range(n_candidate_stops)]),
				'E', 1, 0))

			idx += 1

		idx = 0
		for r in range(r_max):
			for i in range(n_candidate_stops):
				cns.append('B4(%d)' % idx)
				cs.append((
					linex([(vars.rx[r][i][j],  1)
						   for j in range(n_candidate_stops+2)
						   if i != j] +
						  [(vars.rx[r][j][i], -1)
						   for j in range(n_candidate_stops+2)
						   if i != j]),
					'E', 0, 0))

				idx += 1

		idx = 0
		for r in range(r_max):
			for i in range(n_candidate_stops):
				cns.append('B5(%d)' % idx)
				cs.append((
					linex([(vars.rx[r][j][i], 1)
						   for j in range(n_candidate_stops+2)]),
					'L', 1, 0))

				cns.append('B6(%d)' % idx)
				cs.append((
					linex([(vars.rx[r][i][j], 1)
						   for j in range(n_candidate_stops+2)]),
					'L', 1, 0))

				idx += 1

		idx = 0
		for r in range(r_max):
			for i in range(n_candidate_stops):
				cns.append('B7(%d)' % idx)
				cs.append((linex([(vars.rx[r][i][i], 1)]), 'E', 0, 0))

				idx += 1

		for r in range(r_max):
			cns.append('R9(%d)' % r)
			cs.append((linex([(vars.rx[r][n_candidate_stops][n_candidate_stops+1], 1)]), 'E', 0, 0))

		idx = 0
		for r in range(r_max):
			for i in range(1,n_candidate_stops):
				cns.append('B8-1(%d)' % idx)
				cs.append((
					linex([(vars.rx[r][i][n_candidate_stops], 1)] +
						  [(vars.rx[r][k][n_candidate_stops], 1)
						    for k in range(n_candidate_stops+1)
						    if k < i]),
					'L', 1, 0))

				cns.append('B8-2(%d)' % idx)
				cs.append((
					linex([(vars.rx[r][i][n_candidate_stops],  1)] +
						  [(vars.rx[r][j][i],                 -1)
						   for j in range(n_candidate_stops+1)]),
					'L', 0, 0))

				cns.append('B8-3(%d)' % idx)
				cs.append((
					linex([(vars.rx[r][i][n_candidate_stops], 1),
						   (vars.c[r],                        1)]),
					'L', 1, 0))

				cns.append('B8-4(%d)' % idx)
				cs.append((
					linex([(vars.rx[r][i][n_candidate_stops],  1),
						   (vars.c[r],                         1)] +
						  [(vars.rx[r][k][n_candidate_stops],  1)
						    for k in range(n_candidate_stops+1)
						    if k < i] +
						  [(vars.rx[r][j][i],                 -1)
						   for j in range(n_candidate_stops+1)]),
					'G', 0, 0))

				idx += 1

		idx = 0
		for r in range(r_max):
			for i in range(n_candidate_stops):
				for j in range(n_candidate_stops):
					if i != j:
						cns.append('B9(%d)' % idx)
						cs.append((
							linex([(vars.rq[r][i],       1),
								   (vars.rq[r][j],      -1),
								   (vars.rx[r][i][j], 1000)]),
							'L', 999, 0))

						idx += 1

		idx = 0
		for r in range(r_max):
			for i in range(n_candidate_stops):
				for j in range(n_candidate_stops):
					cns.append('B10-1(%d)' % idx)
					cs.append((
						linex([(vars.rx0[r][i][j],                 1),
							   (vars.rx[r][i][n_candidate_stops], -1),
							   (vars.rx[r][n_candidate_stops][j], -1)]),
						'G', -1, 0))

					cns.append('B10-2(%d)' % idx)
					cs.append((
						linex([(vars.rx0[r][i][j],                 1),
							   (vars.rx[r][i][n_candidate_stops], -1)]),
						'L', 0, 0))

					cns.append('B10-3(%d)' % idx)
					cs.append((
						linex([(vars.rx0[r][i][j],                 1),
							   (vars.rx[r][n_candidate_stops][j], -1)]),
						'L', 0, 0))

					idx += 1

		for r in range(r_max):
			cns.append('C1(%d)' % r)
			cs.append((
				linex([(vars.c[r], 1)] +
					  [(vars.rx[r][i][n_candidate_stops+1], -1)
					   for i in range(n_candidate_stops)]),
				'E', 0, 0))



		idx = 0
		for i in range(n_candidate_stops):
			for j in range(n_candidate_stops):
				if i != j:
					cns.append('C3(%d)' % idx)
					cs.append((
						linex([(vars.x[o][d][i+n_demands][j+n_demands], demands[o][d])
							   for o in range(n_demands)
							   for d in range(n_demands)] + 
							  [(vars.z1[r][i][j], -max_cap)
							   for r in range(r_max)]),
						'L', 0, 0))

					idx += 1

		idx = 0
		for r in range(r_max):
			for i in range(n_candidate_stops):
				for j in range(n_candidate_stops):
					if i != j:
						cns.append('C3-2(%d)' % idx)
						cs.append((
							linex([(vars.z1[r][i][j],   1),
								   (vars.rx[r][i][j], -60)]),
							'L', 0, 0))

						cns.append('C3-3(%d)' % idx)
						cs.append((
							linex([(vars.z1[r][i][j],  1),
								   (vars.f[r],        -1)]),
							'L', 0, 0))

						cns.append('C3-3(%d)' % idx)
						cs.append((
							linex([(vars.z1[r][i][j],   1),
								   (vars.f[r],         -1),
								   (vars.rx[r][i][j], -60)]),
							'G', -60, 0))

						idx += 1

		idx = 0
		for r in range(r_max):
			for i in range(n_candidate_stops):
				for j in range(n_candidate_stops):
					if i != j:
						cns.append('C5-2(%d)' % idx)
						cs.append((
							linex([(vars.z2[r][i][j],   1),
								   (vars.rx[r][i][j], -60)]),
							'L', 0, 0))

						cns.append('C5-3(%d)' % idx)
						cs.append((
							linex([(vars.z2[r][i][j],   1),
								   (vars.c[r],        -60)]),
							'L', 0, 0))

						cns.append('C5-4(%d)' % idx)
						cs.append((
							linex([(vars.z2[r][i][j],  1),
								   (vars.f[r],        -1)]),
							'L', 0, 0))

						cns.append('C5-5(%d)' % idx)
						cs.append((
							linex([(vars.z2[r][i][j],   1),
								   (vars.f[r],         -1),
								   (vars.rx[r][i][j], -60),
								   (vars.c[r],        -60)]),
							'G', -120, 0))

						idx += 1

		cns.append('C5')
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

		# idx = 0
		# for o in range(n_demands):
		# 	for d in range(n_demands):
		# 		if o != d:
		# 			for i in range(n_demands + n_candidate_stops):
		# 				for j in range(n_demands + n_candidate_stops):
		# 					if i != j:
		# 						cns.append('SUB(%d)' % idx)
		# 						cs.append((
		# 							linex([(vars.q[o][d][i],       1),
		# 								   (vars.q[o][d][j],      -1),
		# 								   (vars.x[o][d][i][j], 1000)]),
		# 							'L', 999, 0))

		# 						idx += 1

		# idx = 0
		# for o in range(n_demands):
		# 	for d in range(n_demands):
		# 		if o != d:
		# 			cns.append('C0(%d)' % idx)
		# 			cs.append((
		# 				linex([(vars.x[o][d][i][j], 1)
		# 					   for j in range(n_demands)
		# 					   for i in range(n_candidate_stops+n_demands)]),
		# 				'E', 1, 0))

		# 			idx += 1

		# idx = 0
		# for o in range(n_demands):
		# 	for d in range(n_demands):
		# 		if o != d:
		# 			cns.append('C4(%d)' % idx)
		# 			cs.append((
		# 				linex([(vars.x[o][d][i][j], 1)
		# 					   for i in range(n_demands)
		# 					   for j in range(n_demands)]),
		# 				'E', 0, 0))

					# idx += 1

		# idx = 0
		# for o in range(n_demands):
		# 	for d in range(n_demands):
		# 		if o != d:
		# 			cns.append('C5(%d)' % idx)
		# 			cs.append((
		# 				linex([(vars.t[o][d], 1)] + 
		# 					  [(vars.x[o][d][i][j], -costs[i][j])
		# 					   for i in range(n_demands + n_candidate_stops)
		# 					   for j in range(n_demands + n_candidate_stops)]),
		# 				'E', 0, 0))

		# 			idx += 1

		# idx = 0
		# for i in range(n_candidate_stops):
		# 	for j in range(n_candidate_stops):
		# 		if i != j:
		# 			cns.append('C3(%d)' % idx)
		# 			cs.append((
		# 				linex([(vars.x[o][d][n_demands + i][n_demands + j], -demands[o][d])
		# 					   for o in range(n_demands)
		# 					   for d in range(n_demands)] + 
		# 					  [(vars.D[i][j], 1)]),
		# 				'E', 0, 0))

		# idx = 0
		# for i in range(n_candidate_stops):
		# 	for j in range(n_candidate_stops):
		# 		if i != j:
		# 			cns.append('C2(%d)' % idx)
		# 			cs.append((
		# 				linex([(vars.D[i][j], 1)] + 
		# 					  [(vars.f[r], -max_cap)]),
		# 				'L', 0, 0))
		# 			idx += 1

		# idx = 0
		# for r in range(r_max):
		# 	cns.append('C4(%d)' % idx)
		# 	cs.append((
		# 		linex([(vars.T[r], 1)] + 
		# 			  [(vars.rx[r][i][j], -ridetime(i, j))
		# 			   for i in range(n_candidate_stops)
		# 			   for j in range(n_candidate_stops)
		# 			   if i != j]),
		# 		'E', 0, 0))

		# 	idx += 1

		# idx = 0
		# for r in range(r_max):
		# 	for i in range(n_candidate_stops-1):
		# 		cns.append('B8(%d)' % i)
		# 		cs.append((
		# 			linex([(vars.rx[r][i][n_candidate_stops],    1),
		# 				   (vars.rx[r][i+1][n_candidate_stops], -1)]),
		# 			'L', 0, 0))

		# 		idx += 1

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