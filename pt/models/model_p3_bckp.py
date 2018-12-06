import os

from pt import viz
from pt.models import BaseModel
from pt.models import Helper, linex
from plotly.offline import iplot, plot
import time
from itertools import combinations

class Model_P3(BaseModel):

	def __init__(self, *args, **kwargs):
		BaseModel.__init__(self, *args, **kwargs)

		self.options = dict(
			max_transfer_waiting_time_constraint=False,
			waiting_time_objective_coefficient='demand'
		)

		self.customOptions = False

	def generate_variables(self):
		r_max = 1
		candidate_stops = [[55.785470, 12.523041],[55.786239, 12.522234],[55.786541, 12.526961],[55.789277, 12.523946],[55.786431, 12.521428],[55.785898, 12.520618],[55.785138, 12.520728],[55.784637, 12.520459],[55.782099, 12.514132],[55.782460, 12.519244],[55.782226, 12.520035]]
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

		# self.vars.register('st', Helper.g('st_{}', 'B', 1, n_candidate_stops))

		self.vars.register('x', Helper.g('x_{},{},{}', 'B', 0, r_max, n_candidate_stops+1, n_candidate_stops+1))
		# self.vars.register('xf', Helper.g('xf_{},{},{}', 'C', 0, r_max, n_candidate_stops+1, n_candidate_stops+1))
		# self.vars.register('zxf', Helper.g('zxf_{},{},{}', 'C', 0, r_max, n_candidate_stops+1, n_candidate_stops+1))

		# self.vars.register('xD', Helper.g('xD_{},{},{},{}', 'C', 0, r_max, n_candidate_stops, n_candidate_stops, n_candidate_stops))
		# self.vars.register('sD', Helper.g('sD_{},{},{}', 'B', 0, r_max, n_candidate_stops, n_candidate_stops))
		# self.vars.register('D', Helper.g('D_{},{},{}', 'C', 0, r_max, n_candidate_stops, n_candidate_stops))
		self.vars.register('f', Helper.g('f_{}', 'C', 0, r_max))
		# self.vars.register('T', Helper.g('T_{}', 'C', 1000, r_max))

		# self.vars.register('ts', Helper.g('ts_{}', 'C', -1, 1))
		
		self.vars.register('w', Helper.g('w_{},{}', 'C', reduce(lambda a,b: a+b, demands), len(demands), len(demands)))

		self.vars.register('s', Helper.g('s_{},{},{},{}', 'B', 0, len(demands), len(demands), n_candidate_stops, n_candidate_stops))

		self.vars.register('adm', Helper.g('adm_{},{}', 'B', 0, n_candidate_stops+1, n_candidate_stops+1))
		self.vars.register('xadm', Helper.g('adm_{},{},{},{}', 'B', 0, r_max, n_candidate_stops+1, n_candidate_stops+1, n_candidate_stops+1))

		# self.vars.register('q', Helper.g('q_{},{}', 'C', 0, r_max, n_candidate_stops))

		self.vars.register('delta', Helper.g('delta_{},{}', 'B', 0, r_max, n_candidate_stops))
		self.vars.register('deltaf', Helper.g('deltaf_{},{}', 'C', 0, r_max, n_candidate_stops))


		########
		# self.vars.register('w', Helper.g('w_r{}_i{}', 'C', 0, len(routes), len(demand[0][0])))
		# self.vars.register('w', Helper.g('w_r{}_i{}', 'C', [sum(demand[r]) for r in range(len(routes))], len(routes), len(demand[0][0])))
		# self.vars.register('delta', Helper.g('delta_r{},i{}', 'C', 0, len(routes), len(demand[0][0])))
		# self.vars.register('n', Helper.g('n_i{},r{},n{}', 'B', 0, len(demand[0][0]), len(routes), n_buses))
		# self.vars.register('ndelta', Helper.g('ndelta_i{},r{},n{}', 'C', 0, len(demand[0][0]), len(routes), n_buses))

	def generate_constraints(self):
		r_max = 1

		candidate_stops = [[55.785470, 12.523041],[55.786239, 12.522234],[55.786541, 12.526961],[55.789277, 12.523946],[55.786431, 12.521428],[55.785898, 12.520618],[55.785138, 12.520728],[55.784637, 12.520459],[55.782099, 12.514132],[55.782460, 12.519244],[55.782226, 12.520035]]
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
		n_buses = 11

		costs = []

		for i1, (stop_x1, stop_y1) in enumerate([[0,0]] + candidate_stops):
			costs.append([])

			for i2, (stop_x2, stop_y2) in enumerate([[0,0]] + candidate_stops):
				costs[i1].append(275 * (abs(stop_x1 - stop_x2) + abs(stop_y1 - stop_y2)))

		vars = self.vars

		cs = []
		cns = []

		# idx = 0
		# for r in range(r_max):
		# 	for i in range(n_candidate_stops):
		# 		for j in range(n_candidate_stops):
		# 			cns.append('RTS(%d)' % idx)
		# 			cs.append((
		# 				linex([(vars.D[r][i][j], 1),
		# 					   (vars.x[r][i+1][j+1], -ridetime(candidate_stops[i], candidate_stops[j]))] + 
		# 					  [(vars.x[r][i+1][x+1], -ridetime(candidate_stops[i], candidate_stops[x]))
		# 					   for x in range(n_candidate_stops)
		# 					   if x != i and x != j] +
		# 					  [(vars.xD[r][i][x][j], -1)
		# 					   for x in range(n_candidate_stops)
		# 					   if x != i and x != j]),
		# 				'E', 0, 0))

		# 			idx += 1

		# idx = 0
		# for r in range(r_max):
		# 	for i in range(n_candidate_stops):
		# 		for x in range(n_candidate_stops):
		# 			for j in range(n_candidate_stops):
		# 				cns.append('XD1(%d)' % idx)
		# 				cs.append((
		# 					linex([(vars.xD[r][i][x][j],  1),
		# 						   (vars.D[r][x][j],     -1)]),
		# 					'L', 0, 0))

		# 				cns.append('XD2(%d)' % idx)
		# 				cs.append((
		# 					linex([(vars.xD[r][i][x][j],    1),
		# 						   (vars.x[r][i+1][x+1], -100)]),
		# 					'L', 0, 0))

		# 				cns.append('XD3(%d)' % idx)
		# 				cs.append((
		# 					linex([(vars.xD[r][i][x][j],    1),
		# 						   (vars.D[r][x][j],       -1),
		# 						   (vars.x[r][i+1][x+1], -100)]),
		# 					'G', -100, 0))

		# 				idx += 1

		# max_T = sum(list(map(lambda x: ridetime(x[0], x[1]), combinations(candidate_stops, 2))))

		# idx = 0
		# for r in range(r_max):
		# 	for i in range(n_candidate_stops):
		# 		for j in range(n_candidate_stops):
		# 			cns.append('SD1(%d)' % idx)
		# 			cs.append((
		# 				linex([(vars.sD[r][i][j],      1),
		# 					   (vars.D[r][i][j],  -max_T)]),
		# 				'L', 0, 0))

		# 			cns.append('SXD2(%d)' % idx)
		# 			cs.append((
		# 				linex([(vars.sD[r][i][j],        1),
		# 					   (vars.D[r][i][j],  -1/max_T)]),
		# 				'G', 0, 0))

		# 			idx += 1

		# cns.append('TS')
		# cs.append((
		# 	linex([(vars.D[r][i][j], -1)
		# 		   for r in range(r_max)
		# 		   for i in range(n_candidate_stops)
		# 		   for j in range(n_candidate_stops)] + 
		# 		  [(vars.sD[r][i][j], walktime(candidate_stops[i], candidate_stops[j]))
		# 		   for r in range(r_max)
		# 		   for i in range(n_candidate_stops)
		# 		   for j in range(n_candidate_stops)] + 
		# 		  [(vars.ts[0], -1)]),
		# 	'E', 0, 0))

		# for i in range(n_candidate_stops):
		# 	cns.append('STP(%d)' % i)
		# 	cs.append((
		# 		linex([(vars.st[i], 1)] + 
		# 			  [(vars.x[r][i+1][j], -1)
		# 			   for r in range(r_max)
		# 			   for j in range(n_candidate_stops+1)]),
		# 		'L', 0, 0))

		# idx = 0
		# for r in range(r_max):
		# 	cns.append('ITS(%d)' % idx)
		# 	cs.append((
		# 		linex([(vars.x[r][i+1][j+1], 1)
		# 			   for i in range(n_candidate_stops)
		# 			   for j in range(n_candidate_stops)
		# 			   if i != j]),
		# 		'L', 1, 0))
		# 	idx += 1

		# idx = 0
		# for r in range(r_max):
		# 	for i in range(n_candidate_stops + 1):
		# 		for j in range(n_candidate_stops + 1):
		# 			cns.append('XF1(%d)' % idx)
		# 			cs.append((
		# 				linex([(vars.xf[r][i][j],  1),
		# 					   (vars.f[r],        -1)]),
		# 				'L', 0, 0))

		# 			cns.append('XF2(%d)' % idx)
		# 			cs.append((
		# 				linex([(vars.xf[r][i][j],   1),
		# 					   (vars.x[r][i][j],  -60)]),
		# 				'L', 0, 0))

		# 			cns.append('XF3(%d)' % idx)
		# 			cs.append((
		# 				linex([(vars.xf[r][i][j],   1),
		# 					   (vars.f[r],         -1),
		# 					   (vars.x[r][i][j],  -60)]),
		# 				'G', -60, 0))

		# 			idx += 1



		for r in range(r_max):
			cns.append('C1(%d)' % r)
			cs.append((
				linex([(vars.x[r][0][j], 1)
					   for j in range(n_candidate_stops+1)]),
				'E', 1, 0))

		# for r in range(r_max):
		# 	cns.append('C2(%d)' % r)
		# 	cs.append((
		# 		linex([(vars.x[r][i][0], 1)
		# 			   for i in range(n_candidate_stops+1)]),
		# 		'E', 1, 0))

		idx = 0
		for r in range(r_max):
			for j in range(n_candidate_stops):
				cns.append('C3(%d)' % idx)
				cs.append((
					linex([(vars.x[r][i][j],  1)
						   for i in range(n_candidate_stops + 1)
						   if i != j] + 
						  [(vars.x[r][j][i], -1)
						   for i in range(n_candidate_stops + 1)
						   if i != j]),
					'E', 0, 0))

				idx += 1

		idx = 0
		for r in range(r_max):
			for j in range(n_candidate_stops):
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
			for i in range(n_candidate_stops):
				cns.append('C6(%d)' % idx)
				cs.append((linex([(vars.x[r][i+1][i+1], 1)]), 'E', 0, 0))

		# idx = 0
		# for r in range(r_max):
		# 	for i in range(n_candidate_stops + 1):
		# 		for j in range(n_candidate_stops + 1):
		# 			cns.append('C7-1(%d)' % idx)
		# 			cs.append((
		# 				linex([(vars.zxf[r][i][j],  1),
		# 					   (vars.xf[r][i][j],  -1)]),
		# 				'L', 0, 0))

		# 			cns.append('C7-2(%d)' % idx)
		# 			cs.append((
		# 				linex([(vars.zxf[r][i][j],  1),
		# 					   (vars.x[r][0][0],   60)]),
		# 				'L', 60, 0))

		# 			cns.append('C7-3(%d)' % idx)
		# 			cs.append((
		# 				linex([(vars.zxf[r][i][j],  1),
		# 					   (vars.xf[r][i][j],  -1),
		# 					   (vars.x[r][0][0],   60)]),
		# 				'G', 0, 0))

		# 			idx += 1

		# cns.append('C8')
		# cs.append((
		# 	linex([(vars.zxf[r][i+1][j+1], 2*costs[i+1][j+1])
		# 		   for r in range(r_max)
		# 		   for i in range(n_candidate_stops)
		# 		   for j in range(n_candidate_stops)]),
		# 	'L', n_buses, 0, 0))

		# for r in range(r_max):
		# 	cns.append('C9(%d)' % r)
		# 	cs.append((
		# 		linex([(vars.x[r][i+1][j+1], costs[i+1][j+1])
		# 			   for i in range(n_candidate_stops)
		# 			   for j in range(n_candidate_stops)
		# 			   if i != j] + 
		# 			  [(vars.T[r], -1)]),
		# 		'E', 0, 0))

		# Stops for demand origin/destination
		idx = 0
		for p in range(len(demands)):
			for q in range(len(demands)):
				for c1 in range(n_candidate_stops):
					for c2 in range(n_candidate_stops):
						cns.append('S1(%d)' % idx)		
						cs.append((
							linex([(vars.s[p][q][c1][c2],  1),
								   (vars.adm[c1+1][c2+1], -1)]),
							'L', 0, 0))

						idx += 1

		# Stop for demand origin
		idx = 0
		for p in range(len(demands)):
			for q in range(len(demands)):
				cns.append('S2(%d)' % idx)		
				cs.append((
					linex([(vars.s[p][q][c1][c2], 1)
						   for c1 in range(n_candidate_stops)
						   for c2 in range(n_candidate_stops)]),
					'E', 1, 0))

				idx += 1

		# # Sub tour elimination
		# idx = 0
		# for r in range(r_max):
		# 	for i in range(n_candidate_stops):
		# 		for j in range(n_candidate_stops):
		# 			if i != j:
		# 				cns.append('SUB(%d)' % idx)
		# 				cs.append((
		# 					linex([(vars.q[r][i],            1),
		# 						   (vars.q[r][j],           -1),
		# 						   (vars.x[r][i+1][j+1], 1000)]),
		# 					'L', 999, 0))

		# 				idx += 1

		# Admissibility
		idx = 0
		for i in range(n_candidate_stops+1):
			for j in range(n_candidate_stops+1):
				cns.append('ADM(%d)' % idx)
				cs.append((
					linex([(vars.adm[i][j], 1)] + 
						  [(vars.x[r][i][j], -1)
						   for r in range(r_max)] + 
						  [(vars.xadm[r][i][x][j], -1)
						   for r in range(r_max)
						   for x in range(n_candidate_stops + 1)]),
					'L', 0, 0))


		# XADM
		idx = 0
		for r in range(r_max):
			for i in range(n_candidate_stops+1):
				for j in range(n_candidate_stops+1):
					for x in range(n_candidate_stops+1):
						cns.append('XADM1(%d)' % idx)
						cs.append((
							linex([(vars.xadm[r][i][x][j],  1),
								   (vars.x[r][i][x],       -1)]),
							'L', 0, 0))

						cns.append('XADM2(%d)' % idx)
						cs.append((
							linex([(vars.xadm[r][i][x][j],  1),
								   (vars.adm[x][j],        -1)]),
							'L', 0, 0))

						cns.append('XADM3(%d)' % idx)
						cs.append((
							linex([(vars.xadm[r][i][x][j],  1),
								   (vars.adm[x][j],        -1),
								   (vars.x[r][i][x],       -1)]),
							'G', -1, 0))

						idx += 1

		idx = 0
		for p in range(len(demands)):
			for q in range(len(demands)):
				cns.append("WAL(%d)" % idx)
				cs.append((
					linex([(vars.w[p][q], 1)] +
  						  [(vars.s[p][q][c1][c2], -walktime(demand_centroids[p], candidate_stops[c1])-walktime(demand_centroids[p], candidate_stops[c2]))
						   for c1 in range(n_candidate_stops)
						   for c2 in range(n_candidate_stops)]),
					'E', 0, 0))

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

		# idx = 0
		# for r in range(r_max):
		# 	cns.append("FRQ(%d)" % idx)
		# 	cs.append((
		# 		linex([(vars.f[r],           1),
		# 			   (vars.x[r][0][0], 0.033)]),
		# 		'G', 0.033, 0))

		# 	idx += 1

		cs = zip(*cs)

		self._cp.linear_constraints.add(
            lin_expr=cs[0],
            senses=cs[1],
            rhs=cs[2],
            range_values=cs[3])

		self._cp.linear_constraints.set_names(enumerate(cns))


def walktime(x, y):
	return 1100 * (abs(x[0] - y[0]) + abs(x[1] - y[1]))

def ridetime(x, y):
	return 275 * (abs(x[0] - y[0]) + abs(x[1] - y[1]))
