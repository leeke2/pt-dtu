# TODO: check vars.c

import os

from pt import viz
from pt.models import BaseModel
from pt.models import Helper, linex
from plotly.offline import iplot, plot
import time
from itertools import combinations, product
import numpy as np

class Model_P4_1(BaseModel):

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
		candidate_routes = kwargs['candidate_routes']
		is_circular = kwargs['is_circular']
		n_buses = kwargs['n_buses']
		costs = kwargs['costs']

		n_candidate_stops = len(candidate_stops)
		n_demands = len(demands)
		n_candidate_routes = len(candidate_routes)

		costs_w = np.array(costs)[:n_demands,:n_demands]

		self.vars.register('x', Helper.g('x_{},{},{},{}', 'B', 0, n_demands, n_demands, n_candidate_stops+n_demands, n_candidate_stops+n_demands))
		self.vars.register('w', Helper.g('w_{},{}', 'C', 0, n_demands, n_demands))
		self.vars.register('r', Helper.g('r_{},{}', 'C', 0, n_demands, n_demands))

		self.vars.register('w', Helper.g('w_{},{}', 'C', 0, n_demands, n_demands))
		self.vars.register('r', Helper.g('r_{},{}', 'C', 0, n_demands, n_demands))
		self.vars.register('hod', Helper.g('hod_{},{}', 'C', 0, n_demands, n_demands))
		
		self.vars.register('t', Helper.g('t_{}', 'C', 0, r_max))
		self.vars.register('h', Helper.g('h_{}', 'C', 0, r_max))

		# Route
		self.vars.register('rx', Helper.g('rx_{},{},{}', 'B', 0, r_max, n_candidate_stops+2, n_candidate_stops+2))
		self.vars.register('rx0', Helper.g('rx0_{},{},{}', 'B', 0, r_max, n_candidate_stops, n_candidate_stops))
		# self.vars.register('rq', Helper.g('q_{},{}', 'C', 0, r_max, n_candidate_stops))

		self.vars.register('f', Helper.g('f_{}', 'C', 0, r_max))

		#self.vars.register('c', Helper.g('c_{}', 'B', 0, r_max))
		self.vars.register('z1', Helper.g('z1_{},{},{}', 'C', 0, r_max, n_buses+1, n_candidate_routes))
		self.vars.register('z2', Helper.g('z2_{},{},{},{},{}', 'C', 0, n_demands, n_demands, r_max, n_candidate_stops, n_candidate_stops))
		self.vars.register('z3', Helper.g('z3_{},{},{}', 'C', 0, r_max, n_candidate_stops, n_candidate_stops))
		self.vars.register('z4', Helper.g('z4_{},{},{}', 'C', 0, r_max, n_candidate_stops, n_candidate_stops))
		self.vars.register('z5', Helper.g('z5_{},{},{}', 'C', 0, r_max, n_candidate_stops, n_candidate_stops))

		self.vars.register('s', Helper.g('s_{},{}', 'C', np.multiply(np.array(demands).flatten(), np.exp(costs_w/np.max(costs_w)).flatten()).tolist(), n_demands, n_demands))
		# self.vars.register('s', Helper.g('s_{},{}', 'C', np.array(demands).flatten().tolist(), n_demands, n_demands))

		self.vars.register('xc', Helper.g('xc_{},{}', 'B', 0, r_max, n_candidate_routes))
		self.vars.register('zc', Helper.g('zc_{},{}', 'C', 0, r_max, n_candidate_routes))
		self.vars.register('xn', Helper.g('xn_{},{}', 'B', 0, r_max, n_buses+1))

	def generate_constraints(self, **kwargs):
		r_max = kwargs['r_max']
		max_cap = kwargs['max_cap']
		candidate_stops = kwargs['candidate_stops']
		demand_centroids = kwargs['demand_centroids']
		demands = kwargs['demands']
		n_buses = kwargs['n_buses']
		candidate_routes = kwargs['candidate_routes']
		is_circular = kwargs['is_circular']
		t = kwargs['route_time']
		costs = kwargs['costs']

		n_candidate_stops = len(candidate_stops)
		n_demands = len(demands)
		n_candidate_routes = len(candidate_routes)

		def it(spec):
			lengths = {'d': n_demands, 's': n_candidate_stops, 'n': n_demands+n_candidate_stops, 'r': r_max, 'c': n_candidate_routes, 'b': n_buses+1}

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
				# if costs[o][d] == 0:
				# 	f = 1
				# else:
				# 	f = 1.0/float(costs[o][d])/float(costs[o][d])
				f = 0

				cns.append(('A11-1(%d)' % idx))
				cs.append((
					linex([(vars.s[o][d], 1),
						(vars.r[o][d], 1),
						(vars.w[o][d], 1-f),
						(vars.hod[o][d], 0.5)]),
					'E', costs[o][d]*(1-f), 0))

				cns.append(('A12(%d)' % idx))
				cs.append((
					linex([(vars.r[o][d], 1),
						(vars.w[o][d], 1),
						(vars.hod[o][d],0.5)]),
					'L', costs[o][d], 0))
			else:
				cns.append(('A11-2(%d)' % idx))
				cs.append((linex([(vars.s[o][d], 1)]),'E', 0, 0))



		#///////////////////////////////////////////////////////////////////////
		#            Transit route network design problem (TRNDP)
		#///////////////////////////////////////////////////////////////////////

		# for idx, (r,i,j) in it('rss'):
		# 	cns.append('B1(%d)' % idx)
		# 	cs.append((
		# 		linex([(vars.rx0[r][i][j], 1),
		# 			   (vars.c[r], 1)]),
		# 		'L', 1, 0))

		# for idx, (r,i,j) in it('rss'):
		# 	cns.append('B1(%d)' % idx)
		# 	cs.append((
		# 		linex([(vars.rx0[r][i][j], 1)] + 
		# 		      [(vars.xc[r][c],    -(candidate_routes[c][i][n_candidate_stops] + candidate_routes[c][n_candidate_stops][j] - 1))
		# 		       for c in range(n_candidate_routes)]),
		# 		'L', 0, 0))

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

		for idx, (r,i,j) in it('rss'):
			cns.append('B3(%d)' % idx)
			cs.append((
				linex([(vars.rx[r][i][j],                         1)] +
				      [(vars.xc[r][c],    -candidate_routes[c][i][j])
				       for c in range(n_candidate_routes)]),
				'E', 0, 0))

		for idx, (r,i) in it('rs'):
			cns.append('B4(%d)' % idx)
			cs.append((
				linex([(vars.rx[r][i][n_candidate_stops],                                          1)] +
				      [(vars.xc[r][c],                    -candidate_routes[c][i][n_candidate_stops])
					   for c in range(n_candidate_routes)]),
				'E', 0, 0))

		for idx, (r,i) in it('rs'):
			cns.append('B5(%d)' % idx)
			cs.append((
				linex([(vars.rx[r][i][n_candidate_stops+1],                                       1)] +
					  [(vars.xc[r][c],                 -candidate_routes[c][i][n_candidate_stops+1])
					   for c in range(n_candidate_routes)]),
				'E', 0, 0))

		for idx, (r,j) in it('rs'):
			cns.append('B8(%d)' % idx)
			cs.append((
				linex([(vars.rx[r][n_candidate_stops][j],                                       1)] +
					  [(vars.xc[r][c],                 -candidate_routes[c][n_candidate_stops][j])
					   for c in range(n_candidate_routes)]),
				'E', 0, 0))

		for idx, (r) in it('r'):
			cns.append('B6(%d)' % idx)
			cs.append((
				linex([(vars.xc[r][c], 1)
					for c in range(n_candidate_routes)]),
				'E', 1, 0))

		for idx, (r) in it('r'):
			cns.append('B7(%d)' % idx)
			cs.append((
				linex([(vars.xn[r][n], 1)
					for n in range(n_buses+1)]),
				'E', 1, 0))

		# for idx, (r) in it('r'):
		# 	cns.append('B3(%d)' % idx)
		# 	cs.append((
		# 		linex([(vars.rx[r][n_candidate_stops][j], 1)
		# 			   for j in range(n_candidate_stops+1)]),
		# 		'E', 1, 0))

		# for idx, (r) in it('r'):
		# 	cns.append('B4(%d)' % idx)
		# 	cs.append((
		# 		linex([(vars.rx[r][i][n_candidate_stops], 1)
		# 			   for i in range(n_candidate_stops+1)] +
		# 			  [(vars.rx[r][i][n_candidate_stops+1], 1)
		# 			   for i in range(n_candidate_stops)]),
		# 		'E', 1, 0))

		# for idx, (r,i) in it('rs'):
		# 	cns.append('B5(%d)' % idx)
		# 	cs.append((
		# 		linex([(vars.rx[r][i][j],  1)
		# 			   for j in range(n_candidate_stops+2)
		# 			   if i != j] +
		# 			  [(vars.rx[r][j][i], -1)
		# 			   for j in range(n_candidate_stops+2)
		# 			   if i != j]),
		# 		'E', 0, 0))

		# for idx, (r,i) in it('rs'):
		# 	cns.append('B6(%d)' % idx)
		# 	cs.append((
		# 		linex([(vars.rx[r][j][i], 1)
		# 			   for j in range(n_candidate_stops+2)]),
		# 		'L', 1, 0))

		# for idx, (r,i) in it('rs'):
		# 	cns.append('B7(%d)' % idx)
		# 	cs.append((
		# 		linex([(vars.rx[r][i][j], 1)
		# 			   for j in range(n_candidate_stops+2)]),
		# 		'L', 1, 0))

		# for idx, (r,i) in it('rs'):
		# 	cns.append('B8(%d)' % idx)
		# 	cs.append((linex([(vars.rx[r][i][i], 1)]), 'E', 0, 0))

		# for idx, (r) in it('r'):
		# 	cns.append('B9(%d)' % r)
		# 	cs.append((linex([(vars.rx[r][n_candidate_stops][n_candidate_stops+1], 1)]), 'E', 0, 0))

		# for idx, (r,i,j) in it('rss'):
		# 	if i != j:
		# 		cns.append('B10(%d)' % idx)
		# 		cs.append((
		# 			linex([(vars.rq[r][i],       1),
		# 				   (vars.rq[r][j],      -1),
		# 				   (vars.rx[r][i][j], 1000)]),
		# 			'L', 999, 0))


		# for idx, (r,i) in it('rs'):
		# 	if i != 0:
		# 		cns.append('B11-1(%d)' % idx)
		# 		cs.append((
		# 			linex([(vars.rx[r][i][n_candidate_stops], 1)] +
		# 				  [(vars.rx[r][k][n_candidate_stops], 1)
		# 				    for k in range(n_candidate_stops+1)
		# 				    if k < i]),
		# 			'L', 1, 0))

		# for idx, (r,i) in it('rs'):
		# 	if i != 0:
		# 		cns.append('B11-2(%d)' % idx)
		# 		cs.append((
		# 			linex([(vars.rx[r][i][n_candidate_stops],  1)] +
		# 				  [(vars.rx[r][j][i],                 -1)
		# 				   for j in range(n_candidate_stops+1)]),
		# 			'L', 0, 0))

		# for idx, (r,i) in it('rs'):
		# 	if i != 0:
		# 		cns.append('B11-3(%d)' % idx)
		# 		cs.append((
		# 			linex([(vars.rx[r][i][n_candidate_stops], 1),
		# 				   (vars.c[r],                        1)]),
		# 			'L', 1, 0))

		# for idx, (r,i) in it('rs'):
		# 	if i != 0:
		# 		cns.append('B11-4(%d)' % idx)
		# 		cs.append((
		# 			linex([(vars.rx[r][i][n_candidate_stops],  1),
		# 				   (vars.c[r],                         1)] +
		# 				  [(vars.rx[r][k][n_candidate_stops],  1)
		# 				    for k in range(n_candidate_stops+1)
		# 				    if k < i] +
		# 				  [(vars.rx[r][j][i],                 -1)
		# 				   for j in range(n_candidate_stops+1)]),
		# 			'G', 0, 0))

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

# 		for idx, (r) in it('r'):
# 			cns.append('C1(%d)' % r)
# 			cs.append((
# 				linex([(vars.c[r], 1)] +
# 					  [(vars.rx[r][i][n_candidate_stops+1], -1)
# 					   for i in range(n_candidate_stops)]),
# 				'E', 0, 0))

		# for idx, (i,j) in it('ss'):
		# 	if i != j:
		# 		cns.append('C3-1(%d)' % idx)
		# 		cs.append((
		# 			linex([(vars.x[o][d][i+n_demands][j+n_demands], demands[o][d])
		# 				for o in range(n_demands)
		# 				for d in range(n_demands)] + 
		# 				[(vars.zc[r][c], -max_cap*candidate_routes[c][i][j])
		# 				for c in range(n_candidate_routes)
		# 				for r in range(r_max)] + 
		# 				[(vars.z3[r][i][j], -max_cap*candidate_routes[c][i][j])
		# 				for r in range(r_max)]),
		# 			'L', 0, 0))
		for idx, (i,j) in it('ss'):
			if i != j:
				cns.append('C3-1(%d)' % idx)
				cs.append((
					linex([(vars.x[o][d][i+n_demands][j+n_demands], demands[o][d])
						for o in range(n_demands)
						for d in range(n_demands)] + 
						[(vars.z4[r][i][j], -max_cap)
						for r in range(r_max)] + 
						[(vars.z5[r][i][j], -max_cap)
						for r in range(r_max)]),
					'L', 0, 0))

		for idx, (r,c) in it('rc'):
			cns.append('C3-2(%d)' % idx)
			cs.append((
				linex([(vars.zc[r][c],  1),
					   (vars.f[r],     -1)]),
				'L', 0, 0))

			cns.append('C3-3(%d)' % idx)
			cs.append((
				linex([(vars.zc[r][c],   1),
					   (vars.xc[r][c], -60)]),
				'L', 0, 0))

			cns.append('C3-4(%d)' % idx)
			cs.append((
				linex([(vars.zc[r][c],  1),
					   (vars.f[r],     -1),
					   (vars.xc[r][c], -60)]),
				'G', -60, 0))

		for idx, (r,i,j) in it('rss'):
			if i != j:
				cns.append('C3-2(%d)' % idx)
				cs.append((
					linex([(vars.z4[r][i][j],   1),
						   (vars.rx[r][i][j], -60)]),
					'L', 0, 0))

		for idx, (r,i,j) in it('rss'):
			if i != j:
				cns.append('C3-3(%d)' % idx)
				cs.append((
					linex([(vars.z4[r][i][j],  1),
						   (vars.f[r],        -1)]),
					'L', 0, 0))

		for idx, (r,i,j) in it('rss'):
			if i != j:
				cns.append('C3-4(%d)' % idx)
				cs.append((
					linex([(vars.z4[r][i][j],   1),
						   (vars.f[r],         -1),
						   (vars.rx[r][i][j], -60)]),
					'G', -60, 0))

		for idx, (r,i,j) in it('rss'):
			if i != j:
				cns.append('C3-5(%d)' % idx)
				cs.append((
					linex([(vars.z5[r][i][j],   1),
						   (vars.rx0[r][i][j], -60)]),
					'L', 0, 0))

		for idx, (r,i,j) in it('rss'):
			if i != j:
				cns.append('C3-6(%d)' % idx)
				cs.append((
					linex([(vars.z5[r][i][j],  1),
						   (vars.f[r],        -1)]),
					'L', 0, 0))

		for idx, (r,i,j) in it('rss'):
			if i != j:
				cns.append('C3-7(%d)' % idx)
				cs.append((
					linex([(vars.z5[r][i][j],   1),
						   (vars.f[r],         -1),
						   (vars.rx0[r][i][j], -60)]),
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
					linex([(vars.z3[r][i][j],   1)] +
						[(vars.xc[r][c],    -60)
						for c in range(n_candidate_routes)]),
					'L', 0, 0))

		for idx, (r) in it('r'):
			cns.append('C4(%d)' % idx)
			cs.append((
				linex([(vars.xn[r][n],     n)
					   for n in range(n_buses+1)] +
					  [(vars.zc[r][c], -t[c])
					   for c in range(n_candidate_routes)]),
				'E', 0, 0))

		cns.append('C5')
		cs.append((
			linex([(vars.xn[r][n], n)
				   for n in range(n_buses+1)]),
			'L', n_buses, 0))

		for idx, (r) in it('r'):
			cns.append('C5(%d)'  % idx)
			cs.append((linex([(vars.f[r], 1)]), 'G', 0.2, 0))

		for idx, (r) in it('r'):
			cns.append('C6(%d)' % idx)
			cs.append((
				linex([(vars.h[r], 1)] + 
					  [(vars.z1[r][n][c], -t[c]/float(n) if n != 0 else 0)
					   for n in range(n_buses+1)
					   for c in range(n_candidate_routes)]),
				'E', 0, 0))

		for idx, (r,n,c) in it('rbc'):
			cns.append('C7-1(%d)' % idx)
			cs.append((
				linex([(vars.z1[r][n][c],  1),
					   (vars.xn[r][n],    -1)]),
				'L', 0, 0))

			cns.append('C7-2(%d)' % idx)
			cs.append((
				linex([(vars.z1[r][n][c],  1),
					   (vars.xc[r][c],    -1)]),
				'L', 0, 0))

			cns.append('C7-3(%d)' % idx)
			cs.append((
				linex([(vars.z1[r][n][c],  1),
					   (vars.xc[r][c],    -1),
					   (vars.xn[r][n],    -1)]),
				'G', -1, 0))



		for idx, (o,d,r,j,k) in it('ddrss'):
			cns.append('C8-1(%d)' % idx)
			cs.append((
				linex([(vars.z2[o][d][r][j][k],  1),
					   (vars.x[o][d][o][j+n_demands],     -60)]),
				'L', 0, 0))

			cns.append('C8-2(%d)' % idx)
			cs.append((
				linex([(vars.z2[o][d][r][j][k],  1),
					   (vars.x[o][d][j+n_demands][k+n_demands],     -60)]),
				'L', 0, 0))

			cns.append('C8-3(%d)' % idx)
			cs.append((
				linex([(vars.z2[o][d][r][j][k],  1),
					   (vars.rx[r][j][k],       -60),
					   (vars.rx0[r][j][k],      -60)]),
				'L', 0, 0))

			# cns.append('C8-4(%d)' % idx)
			# cs.append((
			# 	linex([(vars.z2[o][d][r][j][k],  1),
			# 		   (vars.h[r],              -1)]),
			# 	'L', 0, 0))

			cns.append('C8-6(%d)' % idx)
			cs.append((
				linex([(vars.z2[o][d][r][j][k],         1),
					   (vars.h[r],                     -1),
					   (vars.rx[r][j][k],             -60),
					   (vars.rx0[r][j][k],            -60),
					   (vars.x[o][d][o][j+n_demands], -60),
					   (vars.x[o][d][j+n_demands][k+n_demands], -60)]),
				'G', -180, 0))

		for idx, (o,d) in it('dd'):
			cns.append('C9(%d)' % idx)
			cs.append((
				linex([(vars.hod[o][d], 1)] +
					  [(vars.z2[o][d][r][j][k], -1)
					   for r in range(r_max)
					   for j in range(n_candidate_stops)
					   for k in range(n_candidate_stops)
					   if j != k]),
				'E', 0, 0))

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
	dists = [[0, 348, 361, 212, 1167, 511, 208],
			 [348, 0, 709, 560, 1515, 859, 392],
			 [361, 709, 0, 149, 806, 654, 245],
			 [212, 560, 149, 0, 955, 505, 96],
			 [1151, 1499, 790, 939, 0, 481, 1035],
			 [511, 859, 654, 505, 481, 0, 501],
			 [208, 556, 245, 96, 1051, 501, 0]]

	return float(dists[x][y]) / speed / 1000.0 * 60.0

# return 275 * (abs(x[0] - y[0]) + abs(x[1] - y[1]))

def ridecost(x, y, n_candidate_stops=11):
	if x == 0 or y == 0 or x == n_candidate_stops+1 or y == n_candidate_stops+1:
		return 0

	return ridetime(x-1,y-1)
