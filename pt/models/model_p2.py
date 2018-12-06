import os

from pt import viz
from pt.models import BaseModel
from pt.models import Helper, linex
from plotly.offline import iplot, plot
import time
from itertools import combinations

class Model_P2(BaseModel):

	def __init__(self, *args, **kwargs):
		BaseModel.__init__(self, *args, **kwargs)

		self.options = dict(
			max_transfer_waiting_time_constraint=False,
			waiting_time_objective_coefficient='demand'
		)

		self.customOptions = False

	def generate_variables(self):
		routes = [1,2,3]
		n_buses = 50
		# demand = [[[9,9]], [[10,10]], [[24,25]]]
		demand = [[[591,662,708,542,823,871,836,681]], [[666,687,682,376,202,172,161,131]], [[1583,1741,1864,1577,1983,1866,1609,1422], [22,16,13,18,19,34,59,50]]]
		# demand = [[[138,141,155,157,146,162,180,174,165,182,194,167,100,116,144,182,202,207,205,209,221,218,211,221,224,208,203,201,181,174,170,156]], [[152,158,164,192,185,179,156,167,166,177,160,179,90,99,91,96,59,51,45,47,46,48,35,43,39,45,42,35,42,28,30,31]], [[366,386,395,436,443,432,436,430,426,442,480,516,366,323,392,496,516,485,491,491,499,464,479,424,418,417,388,386,360,357,350,355], [2,8,10,2,2,5,6,3,3,2,6,2,2,5,7,4,7,2,4,6,8,7,8,11,15,15,16,13,12,11,14,13]]]

		self.vars.register('sw', Helper.g('w_r', 'C', 1, 1))
		self.vars.register('w', Helper.g('w_r{}_i{}', 'C', 0, len(routes), len(demand[0][0])))
		# self.vars.register('w', Helper.g('w_r{}_i{}', 'C', [sum(demand[r]) for r in range(len(routes))], len(routes), len(demand[0][0])))
		self.vars.register('delta', Helper.g('delta_r{},i{}', 'C', 0, len(routes), len(demand[0][0])))
		self.vars.register('n', Helper.g('n_i{},r{},n{}', 'B', 0, len(demand[0][0]), len(routes), n_buses))
		self.vars.register('ndelta', Helper.g('ndelta_i{},r{},n{}', 'C', 0, len(demand[0][0]), len(routes), n_buses))

	def generate_constraints(self, c=30, n=20):
		routes = [1,2,3]
		M = 60
		route_length = [2,3,4]
		max_capacity = c
		n_buses = n
		# demand = [[[9,9]], [[10,10]], [[24,25]]]
		# demand = [[[138,141,155,157,146,162,180,174,165,182,194,167,100,116,144,182,202,207,205,209,221,218,211,221,224,208,203,201,181,174,170,156]], [[152,158,164,192,185,179,156,167,166,177,160,179,90,99,91,96,59,51,45,47,46,48,35,43,39,45,42,35,42,28,30,31]], [[366,386,395,436,443,432,436,430,426,442,480,516,366,323,392,496,516,485,491,491,499,464,479,424,418,417,388,386,360,357,350,355], [2,8,10,2,2,5,6,3,3,2,6,2,2,5,7,4,7,2,4,6,8,7,8,11,15,15,16,13,12,11,14,13]]]
		demand = [[[591,662,708,542,823,871,836,681]], [[666,687,682,376,202,172,161,131]], [[1583,1741,1864,1577,1983,1866,1609,1422], [22,16,13,18,19,34,59,50]]]
		vars = self.vars

		cs = []
		cns = []

		cns.append('last')
		cs.append((
			linex([(vars.sw[0], 								   -1)] + 
			      [(vars.w[r][i], sum(map(lambda x: x[i], demand[r])))
			       for r in range(len(routes))
			       for i in range(len(demand[0][0]))]),
			'E', 0, 0))

		for r in range(len(routes)):
			for i in range(len(demand[0][0])):
				cns.append('C0(%d)' % (r*len(demand[0][0]) + i,))
				cs.append((
					linex([(vars.w[r][i],        1),
						   (vars.delta[r][i], -0.5)]),
					'E', 0, 0))

		for r in range(len(routes)):
			for i in range(len(demand[0][0])):
				cns.append('C1(%d)' % (r*len(demand[0][0]) + i,))
				cs.append((linex([(vars.delta[r][i], 1)]), 'L', max_capacity / sum(map(lambda x: x[i]/60.0, demand[r])), 0))

		for r in range(len(routes)):
			for i in range(len(demand[0][0])):
				cns.append('C22(%d)' % (r*len(demand[0][0]) + i,))
				cs.append((
					linex([(vars.ndelta[i][r][k], k+1)
						   for k in range(n_buses)]), 
					'G', route_length[r]*2, 0))

		for r in range(len(routes)):
			for i in range(len(demand[0][0])):
				cns.append('C2(%d)' % (r*len(demand[0][0]) + i,))
				cs.append((
					linex([(vars.n[i][r][k], 1)
						   for k in range(n_buses)]), 
					'E', 1, 0))

		if n_buses < len(vars.n[i][r]):
			for r in range(len(routes)):
				for i in range(len(demand[0][0])):
					for k in range(len(vars.n[i][r]) - n_buses):
						cns.append('C?(%d)' % k)
						cs.append((linex([(vars.n[i][r][k+n_buses], 1)]), 'E', 0, 0))

		for r in range(len(routes)):
			for i in range(len(demand[0][0])):
				for k in range(len(vars.n[i][r])):
				# for k in range(n_buses):
					cns.append('C3(%d)' % (r*len(demand[0][0]) + i,))
					cs.append((
						linex([(vars.ndelta[i][r][k],  1),
							   (vars.n[i][r][k],      -M)]), 
						'L', 0, 0))

					cns.append('C4(%d)' % (r*len(demand[0][0]) + i,))
					cs.append((
						linex([(vars.ndelta[i][r][k],  1),
							   (vars.delta[r][i],     -1)]),
						'L', 0, 0)) 

					cns.append('C5(%d)' % (r*len(demand[0][0]) + i,))
					cs.append((
						linex([(vars.ndelta[i][r][k],  1),
							   (vars.n[i][r][k],      -M),
							   (vars.delta[r][i],     -1)]), 
						'G', -M, 0))

		for i in range(len(demand[0][0])):
			cns.append('C6(%d)' % i)
			cs.append((
				linex([(vars.n[i][r][k], k+1)
					   for k in range(n_buses)
					   for r in range(len(routes))]), 
				'L', n_buses, 0))

		cs = zip(*cs)

		self._cp.linear_constraints.add(
            lin_expr=cs[0],
            senses=cs[1],
            rhs=cs[2],
            range_values=cs[3])

		self._cp.linear_constraints.set_names(enumerate(cns))



