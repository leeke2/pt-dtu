import os

from pt import viz
from pt.models import BaseModel
from pt.models import Helper, linex
from plotly.offline import iplot, plot
import time
from itertools import combinations

class Model_P1(BaseModel):

	def __init__(self, *args, **kwargs):
		BaseModel.__init__(self, *args, **kwargs)

		self.options = dict(
			max_transfer_waiting_time_constraint=False,
			waiting_time_objective_coefficient='demand'
		)

		self.customOptions = False

	def generate_variables(self):
		groups = self.sc.groups
		plan_horizon = self.sc.plan_horizon

		r = self.sc.routes[0]

		# d: Departure time
		self.vars.register('d', Helper.g('d_s{},k{}',
										  'I', 0, r.n_stops, r.n_buses))
		# a: Arrival time
		self.vars.register('a', Helper.g('a_s{},k{}',
										  'I', 0, r.n_stops, r.n_buses))
		
		# h: Dwell time
		self.vars.register('h', Helper.g('h_s{},k{}',
										  'I', 0, r.n_stops, r.n_buses))

		# c: Capacity
		self.vars.register('c', Helper.g('c_s{},k{}',
										  'I', 0, r.n_stops, r.n_buses))

		p = []
		pt = []
		pta = []
		# ptd = []

		for g in groups:
			p.append(Helper.g(
				'p_g%d,k{}' % g.id, 'B', 0, g.routes[0].n_buses))
			pt.append(Helper.g(
				'pt_g%d,k{}' % g.id, 'B', 0, g.routes[0].n_buses))
			pta.append(Helper.g(
				'pta_g%d,k{}' % g.id, 'I', 0, g.routes[0].n_buses))
			# ptd.append(Helper.g(
			# 	'ptd_g%d,k{}' % g.id, 'I', 0, g.routes[0].n_buses))

		self.vars.register('p', p)
		self.vars.register('pt', pt)
		self.vars.register('pta', pta)
		# self.vars.register('ptd', ptd)

		# self.vars.register('w', Helper.g(
		# 	'w_g{}', 'I', [0 for g in groups], len(groups)))
		self.vars.register('t', Helper.g(
			't_g{}', 'I', [g.size for g in groups], len(groups)))

	def generate_constraints(self):
		routes, groups = (self.sc.routes, self.sc.groups)
		omega, theta = (self.sc.omega, self.sc.theta)
		plan_horizon, M = (self.sc.plan_horizon, self.sc.M)

		vars = self.vars

		r = routes[0]

		cs = []
		cns = []

		# C1: First bus
		if r.first_bus is not None:
			cns.append('C1')
			cs.append((
				linex([(vars.d[0][0], 1)]),
				'E', r.first_bus, 0))

		# C2: Last bus
		if r.last_bus is not None:
			cns.append('C2')
			cs.append((
				linex([(vars.d[0][r.n_buses-1], 1)]),
				'E', r.last_bus, 0))

		# C3: Headway range
		for x, (r,s,k) in enumerate(routes.rsk(1)):
			if r.hw_max != r.hw_min or (r.hw_max == r.hw_min and s == 0):
				cns.append('C3(%d)' % x)
				cs.append((
					linex([(vars.d[s][k+1],  1),
						   (vars.d[s][k],   -1)]),
					'R', r.hw_max, r.hw_min-r.hw_max))

		# C?: Bus order
		for x, (r, s, k) in enumerate(routes.rsk(1)):
			cns.append('C?(%d)' % x)
			cs.append((
                linex([(vars.a[s][k],    1),
                       (vars.a[s][k+1], -1)]),
                'L', 0, 0))

		for x, (r, s, k) in enumerate(routes.rsk(1)):
			cns.append('C??(%d)' % x)
			cs.append((
                linex([(vars.d[s][k],    1),
                       (vars.d[s][k+1], -1)]),
                'L', 0, 0))

		# C4: Departure-arrival relationship
		for x, (r, s, k) in enumerate(routes.rsk()):
			cns.append('C4(%d)' % x)
			cs.append((
				linex([(vars.d[s][k],  1),
					   (vars.a[s][k], -1),
					   (vars.h[s][k], -1)]),
				'E', 0, 0))

		for x, (r, s, k) in enumerate(routes.rsk()):
			cns.append('Dwell(%d)' % x)
			cs.append((
				# linex([(vars.h[s][k], 1)]), 'R', r.dw_max, r.dw_min-r.dw_max))
				linex([(vars.h[s][k], 1)]), 'E', 1, 0))

		# C5:
		for x, (r, s, k) in enumerate(routes.rsk(0,1)):
			cns.append('C5(%d)' % x)
			cs.append((
				linex([(vars.a[s+1][k],  1),
					   (vars.d[s][k],   -1)]),
				'E', theta[s], 0))

		# C6:
		for x, (g, r, _, o, k) in enumerate(groups.gp(1, True, False)):
			cns.append('C6(%d)' % x)
			cs.append((
				linex([(vars.d[r.stops.index(o)][k],  1),
					   (vars.p[g.id][k]            , -M)]),
				'R', g.alpha, -M))

		# C72:
		for x, (g, r, k) in enumerate(groups.gp(0, True, True)):
			cns.append('C72(%d' % x)
			cs.append((
				linex([(vars.pt[g.id][k],  1),
					   (vars.p[g.id][k],  -1)]),
				'L', 0, 0))

		# At least one pt = 1
		for x, (g, r) in enumerate(groups.gp(0, False)):
			cns.append('CTest(%d' % x)
			cs.append((
				linex([(pt, 1) for pt in vars.pt[g.id]]),
				'E', 1, 0))

		# # C7: 
		# for x, (g, r, k) in enumerate(groups.gp(0, True)):
		# 	cns.append('C7(%d)' % x)
		# 	cs.append((
		# 		linex([(vars.p[g.id][k],     1),
		# 			   (vars.pt[g.id][k],   -M)] + 
		# 			  ([(vars.p[g.id][k-1], -1)]
		# 			   if k != 0 else [])),
		# 		'R', 0, M))

		# C8:
		for x, (r, s, k) in enumerate(routes.rsk()):
			cns.append('C8(%d)' % x)
			cs.append((
				linex([(vars.c[s][k],           1)] +
					  ([(vars.c[s-1][k],        -1)]
					   if s != 0 else []) +
					  ([(vars.pt[g.id][k], -g.size)
					  	for g in groups
					  	if g.origin == r.stops[s]]) +
					  ([(vars.pt[g.id][k],  g.size)
					  	for g in groups
					  	if g.destination == r.stops[s]])),
				'E', 0, 0))

		# C9:
		for x, (r, s, k) in enumerate(routes.rsk(0)):
			cns.append('C9(%d)' % x)
			cs.append((linex([(vars.c[s][k], 1)]), 'L', 50, 0))

		for x, (g, r, k) in enumerate(groups.gp(0, True, True)):
			cns.append('C10_2(%d' % x)
			cs.append((
				linex([(vars.pta[g.id][k],  1),
					   (vars.pt[g.id][k],  -M)]),
				'L', 0, 0))

		for x, (g, r, _, d, k) in enumerate(groups.gp(0, True, False)):
			cns.append('C10_3(%d' % x)
			cs.append((
				linex([(vars.pta[g.id][k],  		  1),
					   (vars.a[r.stops.index(d)][k], -1)]),
				'L', 0, 0))

		for x, (g, r, _, d, k) in enumerate(groups.gp(0, True, False)):
			cns.append('C10_4(%d' % x)
			cs.append((
				linex([(vars.pta[g.id][k],  		  1),
					   (vars.a[r.stops.index(d)][k], -1),
					   (vars.pt[g.id][k],            -M)]),
				'G', -M, 0))

		# for x, (g, r, o, _, k) in enumerate(groups.gp(0, True, False)):
		# 	cns.append('C12_1(%d)' % x)
		# 	cs.append((
		# 		linex([(vars.ptd[g.id][k],  		      1),
		# 			   (vars.pt[g.id][k],            -M)]),
		# 		'L', 0, 0))

		# for x, (g, r, o, _, k) in enumerate(groups.gp(0, True, False)):
		# 	cns.append('C12_2(%d)' % x)
		# 	cs.append((
		# 		linex([(vars.ptd[g.id][k],  		      1),
		# 			   (vars.d[r.stops.index(o)][k], -1)]),
		# 		'L', 0, 0))

		# for x, (g, r, o, _, k) in enumerate(groups.gp(0, True, False)):
		# 	cns.append('C12_3(%d)' % x)
		# 	cs.append((
		# 		linex([(vars.ptd[g.id][k],  		      1),
		# 			   (vars.d[r.stops.index(o)][k], -1),
		# 			   (vars.pt[g.id][k],            -M)]),
		# 		'G', -M, 0))

		# for x, (g, r) in enumerate(groups.gp(0, False)):
		# 	cns.append('C12_4(%d' % x)
		# 	cs.append((
		# 		linex([(ptd, 1) for ptd in vars.ptd[g.id]] + 
		# 			  [(vars.w[g.id], -1)]),
		# 		'E', g.alpha, 0))

		for x, (g, r) in enumerate(groups.gp(0, False)):
			cns.append('CLast(%d' % x)
			cs.append((
				linex([(pta, 1) for pta in vars.pta[g.id]] + 
					  [(vars.t[g.id], -1)]),
				'E', g.alpha, 0))

		for x, (g1, g2) in enumerate(combinations(groups, 2)):
			cns.append('CComb(%d)' % x)
			cs.append((
				linex([(vars.pt[g1.id][k], k)
					   for k in range(g1.routes[0].n_buses)] + 
					  [(vars.pt[g2.id][k], -k)
					   for k in range(g2.routes[0].n_buses)]),
				('L' if g1.alpha < g2.alpha else 'G'), 0, 0))

		cs = zip(*cs)

		self._cp.linear_constraints.add(
            lin_expr=cs[0],
            senses=cs[1],
            rhs=cs[2],
            range_values=cs[3])

		self._cp.linear_constraints.set_names(enumerate(cns))



