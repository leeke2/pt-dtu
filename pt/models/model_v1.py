import os

from pt import viz
from pt.models import BaseModel
from pt.models import Helper, linex
from plotly.offline import iplot, plot
import time


class Model_V1(BaseModel):

    def __init__(self, *args, **kwargs):
        BaseModel.__init__(self, *args, **kwargs)

        self.options = dict(
            max_transfer_waiting_time_constraint=False,
            waiting_time_objective_coefficient='demand',
        )

        self.customOptions = False

    def configure(self, ss):
        for k, v in ss.iteritems():
            if k in self.options and self.options[k] != v:
                self.customOptions = True
                self.options[k] = v

    def generate_variables(self):
        routes, groups = (self.sc.routes, self.sc.groups)
        plan_horizon = self.sc.plan_horizon

        c = Helper.initialize_nested_dict(len(routes), len(routes))
        t = Helper.initialize_nested_dict(len(routes), len(routes))
        p = Helper.initialize_nested_dict(len(routes), len(routes))
        zt = Helper.initialize_nested_dict(len(routes), len(routes))

        for r in routes:
            for rp, ss in r.transfers:
                c[r.id][rp.id] = Helper.g(
                    'c_r%d,rp%d,s{},k{},kp{}' % (r.id, rp.id),
                    'B', 0, ss, r.n_buses, rp.n_buses)
                t[r.id][rp.id] = Helper.g(
                    't_r%d,rp%d,s{},k{},kp{}' % (r.id, rp.id),
                    'I', 0, ss, r.n_buses, rp.n_buses)
                p[r.id][rp.id] = Helper.g(
                    'p_r%d,rp%d,s{},k{},kp{},g{}' % (r.id, rp.id),
                    'B', 0, ss, r.n_buses, rp.n_buses, len(groups))
                zt[r.id][rp.id] = Helper.g(
                    'zt_r%d,rp%d,s{},k{},kp{},g{}' % (r.id, rp.id),
                    'I', 0, ss, r.n_buses, rp.n_buses, len(groups))

        co = []
        to = []
        z = []

        for g in groups:
            co.append(Helper.g(
                'co_g%d,k{}' % g.id, 'B', 0, g.routes[0].n_buses))

            if self.options['waiting_time_objective_coefficient'] == 'demand':
                to.append(Helper.g(
                    'to_g%d,k{}' % g.id, 'I', g.size, g.routes[0].n_buses))
            else:
                to.append(Helper.g(
                    'to_g%d,k{}' % g.id,
                    'I',
                    g.size*self.options['waiting_time_objective_coefficient'],
                    g.routes[0].n_buses))

            z.append(Helper.g(
                'z_g%d,k{},kp{}' % g.id, 'B', 0,
                g.routes[0].n_buses, g.routes[1].n_buses))

        self.vars.register('d', [Helper.g('d_r%d,s{},k{}' % r.id,
                                          'I', 0, r.n_stops, r.n_buses)
                                 for r in routes])
        self.vars.register('a', [Helper.g('a_r%d,s{},k{}' % r.id,
                                          'I', 0, r.n_stops, r.n_buses)
                                 for r in routes])
        self.vars.register('h', [Helper.g('h_r%d,s{},k{}' % r.id,
                                          'I', 0, r.n_stops, r.n_buses)
                                 for r in routes])
        self.vars.register('db', [Helper.g('db_r%d,s{},k{},n{}' % r.id,
                                           'B', 0, r.n_stops, r.n_buses,
                                           plan_horizon)
                                  for r in routes])

        self.vars.register('c', c)
        self.vars.register('t', t)
        self.vars.register('p', p)
        self.vars.register('zt', zt)

        self.vars.register('co', co)
        self.vars.register('to', to)
        self.vars.register('z', z)

        self.vars.register('tg', Helper.g(
            'tg_g{}', 'I', [g.size for g in groups], len(groups)))

    def generate_constraints(self):
        routes, groups = (self.sc.routes, self.sc.groups)
        omega, theta = (self.sc.omega, self.sc.theta)
        plan_horizon, M = (self.sc.plan_horizon, self.sc.M)

        vars = self.vars

        cs = []
        cns = []

        # C2: First bus
        for r in routes:
            if r.first_bus is not None:
                cns.append('C2(%d)' % r.id)
                cs.append((
                    linex([(vars.d[r.id][0][0], 1)]),
                    'E', r.first_bus, 0))

        # C3: Last bus
        for r in routes:
            if r.last_bus is not None:
                cns.append('C3(%d)' % r.id)
                cs.append((
                    linex([(vars.d[r.id][0][r.n_buses-1], 1)]),
                    'E', r.last_bus, 0))

        # C4: Headway range
        for x, (r, s, k) in enumerate(routes.rsk(1)):
            if r.hw_max != r.hw_min or (r.hw_max == r.hw_min and s == 0):
                cns.append('C4(%d)' % x)
                cs.append((
                    linex([(vars.d[r.id][s][k+1],  1),
                           (vars.d[r.id][s][k],   -1)]),
                    'R', r.hw_max, r.hw_min-r.hw_max))

        # C5: Bus order
        for x, (r, s, k) in enumerate(routes.rsk(1)):
            cns.append('C5(%d)' % x)
            cs.append((
                linex([(vars.d[r.id][s][k],    1),
                       (vars.d[r.id][s][k+1], -1)]),
                'L', 0, 0))

        # C6: Departure-arrival relationship
        for x, (r, s, k) in enumerate(routes.rsk()):
            cns.append('C6(%d)' % x)
            cs.append((
                linex([(vars.d[r.id][s][k],  1),
                       (vars.a[r.id][s][k], -1),
                       (vars.h[r.id][s][k], -1)]),
                'E', 0, 0))

        # C7: Dwell time range
        for x, (r, s, k) in enumerate(routes.rsk()):
            cns.append('C7(%d)' % x)
            cs.append((
                linex([(vars.h[r.id][s][k], 1)]),
                'R', r.dw_max, r.dw_min-r.dw_max))

        # C8/11
        for x, (r, s, k) in enumerate(routes.rsk(0, 1)):
            cns.append('C8(%d)' % x)
            cs.append((
                linex([(vars.a[r.id][s+1][k],                    1),
                       (vars.d[r.id][s][k],                     -1)] +
                      [(vars.db[r.id][s][k][n], -theta[r.id][s][n])
                       for n in range(plan_horizon)]),
                'E', 0, 0))

        # C9
        for x, (r, s, k) in enumerate(routes.rsk()):
            cns.append('C9(%d)' % x)
            cs.append((
                linex([(vars.d[r.id][s][k],      1)] +
                      [(vars.db[r.id][s][k][n], -n)
                       for n in range(plan_horizon)]),
                'E', 0, 0))

        # C10
        for x, (r, s, k) in enumerate(routes.rsk()):
            cns.append('C10(%d)' % x)
            cs.append((
                linex([(vars.db[r.id][s][k][n],  1)
                       for n in range(plan_horizon)]),
                'E', 1, 0))

        # C12
        for x, (r, rp, s, k, kp) in enumerate(routes.tf()):
            cns.append('C12(%d)' % x)
            cs.append((
                linex([(vars.d[rp.id][rp.stops.index(s)][kp],  1),
                       (vars.a[r.id][r.stops.index(s)][k],    -1),
                       (vars.c[r.id][rp.id][s][k][kp],        -M)]),
                'R', omega[r.id][s][rp.id], -M))

        # C13
        for x, (r, rp, s, k, kp) in enumerate(routes.tf()):
            cns.append('C13(%d)' % x)
            cs.append((
                linex([(vars.d[rp.id][rp.stops.index(s)][kp],  1),
                       (vars.a[r.id][r.stops.index(s)][k],    -1),
                       (vars.t[r.id][rp.id][s][k][kp],        -1)]),
                'L', omega[r.id][s][rp.id], 0))

        # C14
        for x, (g, r, _, o, k) in enumerate(groups.gp(1, True, False)):
            cns.append('C14(%d)' % x)
            cs.append((
                linex([(vars.d[r.id][r.stops.index(o)][k],  1),
                       (vars.co[g.id][k],                  -M)]),
                'R', g.alpha, -plan_horizon))

        # C14b
        for x, (g, r, _, o, k) in enumerate(groups.gp(1, True, False)):
            cns.append('C14b(%d)' % x)
            cs.append((
                linex([(vars.d[r.id][r.stops.index(o)][k],  1),
                       (vars.to[g.id][k],                  -1)] +
                      ([(vars.co[g.id][k-1],               -M)]
                       if k != 0 else [])),
                'L', g.alpha, 0))

        # C15a
        for x, (g, r, rp, s, k, kp) in enumerate(groups.gp(1, True, True)):
            cns.append('C15(%d)' % x)
            cs.append((
                linex([(vars.z[g.id][k][kp],               1),
                       (vars.c[r.id][rp.id][s][k][kp],    -1),
                       (vars.co[g.id][k],                 -1)] +
                      ([(vars.c[r.id][rp.id][s][k][kp-1],  1)]
                       if kp != 0 else []) +
                      ([(vars.co[g.id][k-1],               1)]
                       if k != 0 else [])),
                'G', -1, 0))

        # C15b
        for x, (g, r, rp, s, k, kp) in enumerate(groups.gp(1, True, True)):
            cns.append('C15b(%d)' % x)
            cs.append((
                linex([(vars.z[g.id][k][kp],               1),
                       (vars.c[r.id][rp.id][s][k][kp],    -1)] +
                      ([(vars.c[r.id][rp.id][s][k][kp-1],  1)]
                       if kp != 0 else [])),
                'L', 0, 0))

        # C15c
        for x, (g, _, _, _, k, kp) in enumerate(groups.gp(1, True, True)):
            cns.append('C15c(%d)' % x)
            cs.append((
                linex([(vars.z[g.id][k][kp], 1),
                       (vars.co[g.id][k],   -1)] +
                      ([(vars.co[g.id][k-1], 1)]
                       if k != 0 else [])),
                'L', 0, 0))

        # C15h
        for x, (g, r, rp, s, k, kp) in enumerate(groups.gp(1, True, True)):
            cns.append('C15h(%d)' % x)
            cs.append((
                linex([(vars.p[r.id][rp.id][s][k][kp][g.id],  1),
                       (vars.z[g.id][k][kp],                 -M)]),
                'L', 0, 0))

        # C15i
        for x, (g, r, rp, s, k, kp) in enumerate(groups.gp(1, True, True)):
            cns.append('C15i(%d)' % x)
            cs.append((
                linex([(vars.p[r.id][rp.id][s][k][kp][g.id],  1),
                       (vars.z[g.id][k][kp],                 -1)]),
                'G', 0, 0))

        # C3.5
        print(groups.gp())
        for x, (g, r, rp, s) in enumerate(groups.gp()):
            cns.append('C3.5(%d)' % x)
            cs.append((
                linex([(vars.p[r.id][rp.id][s][k][kp][g.id], 1)
                       for k in range(r.n_buses)
                       for kp in range(rp.n_buses)]),
                'E', 1, 0))

        # C3.6
        for x, (g, r1, rp1, s1, r2, rp2, s2) in enumerate(groups.gp(2)):
            cns.append('C3.6(%d)' % x)
            cs.append((
                linex([(vars.p[r1.id][rp1.id][s1][k1][kp1][g.id], kp1+1)
                       for k1 in range(r1.n_buses)
                       for kp1 in range(rp1.n_buses)] +
                      [(vars.p[r2.id][rp2.id][s2][k2][kp2][g.id], -k2-1)
                       for k2 in range(r2.n_buses)
                       for kp2 in range(rp2.n_buses)]),
                'E', 0, 0))

        # C3.8
        for x, (g, r, rp, s, k, kp) in enumerate(
                groups.gp(False, True, True)):
            cns.append('C3.8(%d)' % x)
            cs.append((
                linex([(vars.p[r.id][rp.id][s][k][kp][g.id],  1),
                       (vars.c[r.id][rp.id][s][k][kp],       -1)]),
                'L', 0, 0))

        # C3.7a
        for x, (g, r, rp, s, k, kp) in enumerate(
                groups.gp(False, True, True)):
            cns.append('C3.7a(%d)' % x)
            cs.append((
                linex([(vars.zt[r.id][rp.id][s][k][kp][g.id],            1),
                       (vars.p[r.id][rp.id][s][k][kp][g.id], -plan_horizon)]),
                'L', 0, 0))

        # C3.7c
        for x, (g, r, rp, s, k, kp) in enumerate(
                groups.gp(False, True, True)):
            cns.append('C3.7c(%d)' % x)
            cs.append((
                linex([(vars.zt[r.id][rp.id][s][k][kp][g.id],            1),
                       (vars.t[r.id][rp.id][s][k][kp],                  -1),
                       (vars.p[r.id][rp.id][s][k][kp][g.id], -plan_horizon)]),
                'G', -plan_horizon, 0))

        # C3.7d
        for x, (g, r, rp, s, k, kp) in enumerate(
                groups.gp(False, True, True)):
            cns.append('C3.7d(%d)' % x)
            cs.append((
                linex([(vars.zt[r.id][rp.id][s][k][kp][g.id],  1),
                       (vars.t[r.id][rp.id][s][k][kp],        -1)]),
                'L', 0, 0))

        # C3.7e
        for x, (g, trs) in enumerate(groups.gp(-1)):
            cns.append('C3.7e(%d)' % x)
            cs.append((
                linex([(vars.tg[g.id],                         1)] +
                      [(vars.zt[r.id][rp.id][s][k][kp][g.id], -1)
                       for r, rp, s in trs
                       for k in range(r.n_buses)
                       for kp in range(rp.n_buses)]),
                'G', 0, 0))

        cs = zip(*cs)

        self._cp.linear_constraints.add(
            lin_expr=cs[0],
            senses=cs[1],
            rhs=cs[2],
            range_values=cs[3])

        self._cp.linear_constraints.set_names(enumerate(cns))

    # TODO: clean
    def varyMaxTT(self, maxtt=False, step=5):
        self.vars.solutionFound = False

        vars = self.vars

        cs = []
        cns = []

        directory_maxtt = os.path.join(
                    self.base_directory,
                    "maxtt")
        if not os.path.exists(directory_maxtt):
            os.makedirs(directory_maxtt)

        nm = self._cp.variables.get_names()

        solution_exists = True

        if not maxtt:
            maxtt = self.sc.plan_horizon / 2

        results = []
        cons_idx_first = self._cp.linear_constraints.get_num()

        # C17
        vars.solutionFound = False
        for x, g in enumerate(self.sc.groups):
            cns.append('C17(%d)' % x)
            cs.append((
                linex([(vars.tg[g.id],   1)] +
                      ([(vars.to[g.id][k], 1)
                        for k in range(g.routes[0].n_buses)]
                       if self.options['max_transfer_waiting_time_constraint']
                       else [])),
                'L', maxtt))

        cs = zip(*cs)
        self._cp.linear_constraints.add(
            lin_expr=cs[0],
            senses=cs[1],
            rhs=cs[2])

        self._cp.linear_constraints.set_names(
            [(i+cons_idx_first, cn) for i, cn in enumerate(cns)])

        while solution_exists and maxtt > 0:
            try:
                directory = os.path.join(
                            self.base_directory,
                            "maxtt",
                            "%d" % (maxtt, ))
                if not os.path.exists(directory):
                    os.makedirs(directory)

                self.solve(name=os.path.join(
                    self.base_directory,
                    "maxtt",
                    "%d" % (maxtt, ),
                    ('%s_%s_%s_maxtt%d' % (
                        self.timestamp, self.__class__.__name__, self.sc.name, maxtt))))
                results += [(maxtt, g, self.sc.groups[g].size, tg, sum(to))
                            for g, (to, tg) in enumerate(
                                zip(self.vars.to, self.vars.tg))]

                fig_schedule = viz.schedule(self.vars, self.sc)
                plot(fig_schedule, image_filename="schedule", image="png", output_type="file", image_width=888, image_height=fig_schedule.layout.height)
                time.sleep(2)
                os.rename("/Users/kelvinlee/Downloads/schedule.png", os.path.join(self.base_directory, "maxtt", str(maxtt), "schedule.png"))

                fig_trip = viz.trip(self.vars, self.sc)
                plot(fig_trip, image_filename="trip", image="png", output_type="file", image_width=888, image_height=fig_trip.layout.height)
                time.sleep(2)
                os.rename("/Users/kelvinlee/Downloads/trip.png", os.path.join(self.base_directory, "maxtt", str(maxtt), "trip.png"))

                # fig = viz.comprehensive(self.vars, self.sc)
                # plot(fig,
                #      filename=os.path.join(
                #          self.base_directory,
                #          "maxtt",
                #          ('%s_%s_%s_maxtt%d_viz.html' % (
                #               self.timestamp, self.__class__.__name__, self.sc.name, maxtt))),
                #      auto_open=False)

                maxtt -= step
                self._cp.linear_constraints.set_rhs(
                    zip(cns, [maxtt] * len(cns)))
            except Exception as e:
                print e
                solution_exists = False

        f = open(os.path.join(
                         self.base_directory,
                         "maxtt","results.csv"), 'w+')
        f.write(('Max transfer time, Group, Demand, '
                 'Transfer time, Waiting time\n'))
        for row in results:
            f.write(','.join(map(str, list(row))) + '\n')
        f.close()