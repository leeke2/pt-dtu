"""Summary
"""
__all__ = ['BaseModel', 'Routes', 'Route', 'Transfer', 'Groups', 'Group']

import os
import time
from datetime import datetime
from psutil import virtual_memory
# from cpuinfo import get_cpu_info

import cplex

from pt.models import Helper

class BaseModel:

    """A base class of all Cplex models.

    Attributes:
        _cp (Cplex): A Cplex problem.
        output (bool): Model produces output when solved if True.
        sc (Scenario): The test case to be used to solve the problem.
        vars (dict): The decision variables.
        timestamp (str): The time the model was initialized.
        base_directory (str): The default directory for output files.
    """

    def __init__(self, *args, **kwargs):
        """Creates a model with the base functionalities.

        Args:
            sc (Scenario): The test case to be used to solve the problem.
        """
        self._cp = cplex.Cplex()
        self._cp.parameters.conflict.display = 2
        # self._cp.parameters.mip.strategy.heuristicfreq = 100
        self._cp.objective.set_sense(self._cp.objective.sense.maximize)
        self._cp.set_problem_type(self._cp.problem_type.LP)

        if 'verbose' in kwargs and not kwargs['verbose']:
            self._cp.set_log_stream(None)
            self._cp.set_error_stream(None)
            self._cp.set_warning_stream(None)
            self._cp.set_results_stream(None)

        if 'output' in kwargs:
            self.output = kwargs['output']
        else:
            self.output = False

        if 'scautosave' in kwargs:
            self.sc_autosave = kwargs['scautosave']
        else:
            if 'sc' in kwargs:
                self.sc_autosave = True
            else:
                self.sc_autosave = False

        if 'sc' in kwargs:
            self.sc = kwargs['sc']
        else:
            self.sc = None

        self.vars = Variables(self)

        Helper.cp = self._cp

        self.timestamp = str(datetime.now().strftime("%y%m%d%H%M"))

        if self.sc is not None:
            self.base_directory = os.path.join('tests', '%s_%s_%s' % (
                self.timestamp, self.__class__.__name__, self.sc.name))
        else:
            self.base_directory = os.path.join('tests', '%s_%s' % (
                self.timestamp, self.__class__.__name__))

        if self.output and not os.path.exists(self.base_directory):
            os.makedirs(self.base_directory)

    def solve(self, name=False):
        """Solves the problem and assigns solution values to the variables.
        """

        if self.sc_autosave:
            self.sc.save()
            self.base_directory = os.path.join('tests', '%s_%s_%s' % (
                self.timestamp, self.__class__.__name__, self.sc.name))

            if self.output and not os.path.exists(self.base_directory):
                os.makedirs(self.base_directory)

        if self.output:
            if not name:
                self._cp.write(os.path.join(
                    self.base_directory,
                    ('%s_%s_%s_model.lp' % (
                        self.timestamp, self.__class__.__name__, self.sc.name))))
            else:
                self._cp.write('%s_model.lp' % name)

        
        start = time.time()
        self._cp.solve()
        self.computation_time = time.time() - start

        self.vars.setvalues(self._cp.solution.get_values())

        if self.output:
            if not name:
                if self.output == "all" or self.output == "solution":
                    self._exportSolution()

                if self.output == "all" or self.output == "report":
                    self._exportReport()
            else:
                if self.output == "all" or self.output == "solution":
                    self._exportSolution(name)

                if self.output == "all" or self.output == "report":
                    self._exportReport(name)

    def _exportReport(self, name=False):
        if not name:
            f = open(os.path.join(self.base_directory,
                                  ('%s_%s_%s_report.md' %
                                   (self.timestamp,
                                    self.__class__.__name__,
                                    self.sc.name))), 'wb')
        else:
            f = open('%s_report.md' % name, 'wb')

        f.write('# Optimisation report\n')
        f.write("**Model**: %s  \n" % (self.__class__.__name__, ))
        f.write("**Scenario**: %s  \n" % (self.sc.name, ))
        f.write("**Timestamp**: %s  \n\n" % (self.timestamp, ))

        f.write("**Objective value**: %d  \n" % (self._cp.solution.get_objective_value(), ))
        # f.write("**Computation time**: %.2fs (%s, %dG)  \n" % (self.computation_time, get_cpu_info()['brand'], int(virtual_memory().total/(1024.**3))))
        f.write("**# of variables**: %d  \n" % (self._cp.variables.get_num(), ))
        f.write("**# of constraints**: %d  \n\n" % (self._cp.linear_constraints.get_num(), ))

        f.write("## Settings\n")
        f.write("```python\n{\n")
        settings = ""
        for k, v in self.options.iteritems():
            settings += "    '%s': %s,\n" % (k, ("'%s'" % v if isinstance(v, str) else v))

        f.write(settings[:-2] + "\n")
        f.write("}\n```\n\n")

        # f.write('\n')

        # f.write('ROUTES\n')
        # f.write('\t'.join([r.name for r in self.sc.routes]) + '\n')

        # f.write('\n')

        # f.write('VEHICLES\n')
        # f.write('\t'.join(map(str, [r.n_buses for r in self.sc.routes])))

        # f.write('\n')

        # f.write('STOPS\n')
        # for r in range(len(self.sc.routes)):
        #     f.write('\t'.join(self.sc.routes[r].stops) + '\n')

        # f.write('\n')

        # f.write('WALKING TIME\n')
        # for r, val in self.sc.omega.iteritems():
        #     for s, val2 in val.iteritems():
        #         for rp, val3 in val2.iteritems():
        #             f.write('\t'.join(map(str, [r, rp, s, val3])) + '\n')

        # f.write('\n')
        f.write("## Arrival / Departure schedule\n")

        f.write("![Schedule](schedule.png)\n\n")

        for route in self.sc.routes:
            f.write("**Route %s**\n\n" % (route.name, ))
            f.write("| | " + " | ".join(["%s-%d" % (route.name, k+1) for k in range(route.n_buses)]) + " |\n")
            f.write("| --- |" + " | ".join([":---:" for _ in range(route.n_buses)]) + " |\n")
            for s in range(route.n_stops):
                f.write('| **%s** | ' % (route.stops[s], ) + ' | '.join(
                    map(lambda elem: ("%d / %d" % (elem[0], elem[1])) if elem[0] != elem[1] else str(elem[0]),
                        [(int(self.vars.a[route.id][s][k] + .5),
                          int(self.vars.d[route.id][s][k] + .5))
                         for k in range(route.n_buses)])) + ' |\n')

            f.write("\n")

        # for r in self.sc.routes:
        #     for rp, ss in r.transfers:
        #         for s in ss:
        #             f.write('CONNECTIVITY\n')
        #             f.write('\t'.join(map(str, [r.id, rp.id, s])))

        #             for k in range(r.n_buses):
        #                 f.write('\t'.join(
        #                     [str(int(round(
        #                         self.vars.c[r.id][rp.id][s][k][kp])))
        #                      for kp in range(rp.n_buses)]) + '\n')

        #             f.write('\n')

        f.write("## Group itineraries\n")

        f.write("![Schedule](trip.png)\n\n")

        f.write("| Group | Size | t_o | t_g | Itinerary |\n")
        f.write("| :-- | :-: | :-: | :-: | :-- |\n")

        for group in self.sc.groups:
            vehicle_taken = []

            for r, rp, s in zip(group.routes[:-1],
                                group.routes[1:],
                                group.stops):
                if len(vehicle_taken) == 0:
                    for k, kp in [(k, kp)
                                  for k in range(r.n_buses)
                                  for kp in range(rp.n_buses)]:
                        if self.vars.p[r.id][rp.id][
                                s][k][kp][group.id] == 1:
                            vehicle_taken.append(k)
                            break

                for kp in range(rp.n_buses):
                    if self.vars.p[r.id][rp.id][
                            s][vehicle_taken[-1]][kp][group.id] == 1:
                        vehicle_taken.append(kp)
                        break

            itinerary = ""

            itinerary += "%d Arrives at **%s** (%s)<br>" % (group.alpha, group.origin, group.routes[0])

            for i, r in enumerate(group.routes):
                if i == 0:
                    itinerary += "%d Boards %s-%d<br>" % (self.vars.d[r.id][r.stops.index(group.origin)][vehicle_taken[i]], r, vehicle_taken[i] + 1)
                else:
                    itinerary += "%d Boards %s-%d<br>" % (self.vars.d[r.id][r.stops.index(group.stops[i-1])][vehicle_taken[i]], r, vehicle_taken[i] + 1)
                
                if i != len(group.routes) - 1:
                    itinerary += "%d Arrives at **%s** (%s), transfers to %s<br>" % (self.vars.a[r.id][r.stops.index(group.stops[i])][vehicle_taken[i]], group.stops[i], r, group.routes[i+1])
                    itinerary += "%d Arrives at **%s** (%s)<br>" % (self.vars.a[r.id][r.stops.index(group.stops[i])][vehicle_taken[i]] + self.sc.omega[r.id][group.stops[i]][group.routes[i+1].id], group.stops[i], group.routes[i+1])

            f.write("| **G%d** | %d | %d | %d | %s |\n" % (group.id, group.size, sum(self.vars.to[group.id]), self.vars.tg[group.id], itinerary))
        f.close()

    def _exportSolution(self, name=False):
        if not name:
            f = open(os.path.join(self.base_directory,
                                  ('%s_%s_%s_solution.soln' %
                                   (self.timestamp,
                                    self.__class__.__name__,
                                    self.sc.name))), 'wb')
        else:
            f = open('%s_solution.soln' % name, 'wb')

        f.write('SOLUTION FOR MODEL %s' % (self.__class__.__name__, ) + '\n')
        f.write('SCENARIO: %s\n' % self.sc.name)
        f.write('TIMESTAMP: %s\n\n' % (self.timestamp, ))

        for k, v in self.options.iteritems():
            f.write('%s: %s\n' % (k, v))

        f.write('\n')

        f.write('ROUTES\n')
        f.write('\t'.join([r.name for r in self.sc.routes]) + '\n')

        f.write('\n')

        f.write('VEHICLES\n')
        f.write('\t'.join(map(str, [r.n_buses for r in self.sc.routes])))

        f.write('\n')

        f.write('STOPS\n')
        for r in range(len(self.sc.routes)):
            f.write('\t'.join(self.sc.routes[r].stops) + '\n')

        f.write('\n')

        f.write('WALKING TIME\n')
        for r, val in self.sc.omega.iteritems():
            for s, val2 in val.iteritems():
                for rp, val3 in val2.iteritems():
                    f.write('\t'.join(map(str, [r, rp, s, val3])) + '\n')

        f.write('\n')

        f.write('DEPARTURE\n')
        for route in self.sc.routes:
            for k in range(route.n_buses):
                f.write('\t'.join(
                    map(lambda elem: str(int(elem + .5)),
                        [self.vars.d[route.id][s][k]
                         for s in range(route.n_stops)])) + '\n')
        f.write('\n')

        f.write('ARRIVAL\n')
        for route in self.sc.routes:
            for k in range(route.n_buses):
                f.write('\t'.join(
                    map(lambda elem: str(int(elem + .5)),
                        [self.vars.a[route.id][s][k]
                         for s in range(route.n_stops)])) + '\n')

        f.write('\n')

        for r in self.sc.routes:
            for rp, ss in r.transfers:
                for s in ss:
                    f.write('CONNECTIVITY\n')
                    f.write('\t'.join(map(str, [r.id, rp.id, s])))

                    for k in range(r.n_buses):
                        f.write('\t'.join(
                            [str(int(round(
                                self.vars.c[r.id][rp.id][s][k][kp])))
                             for kp in range(rp.n_buses)]) + '\n')

                    f.write('\n')

        f.write('GROUPS\n')
        for group in self.sc.groups:
            vehicle_taken = []

            for r, rp, s in zip(group.routes[:-1],
                                group.routes[1:],
                                group.stops):
                if len(vehicle_taken) == 0:
                    for k, kp in [(k, kp)
                                  for k in range(r.n_buses)
                                  for kp in range(rp.n_buses)]:
                        if self.vars.p[r.id][rp.id][
                                s][k][kp][group.id] == 1:
                            vehicle_taken.append(k)
                            break

                for kp in range(rp.n_buses):
                    if self.vars.p[r.id][rp.id][
                            s][vehicle_taken[-1]][kp][group.id] == 1:
                        vehicle_taken.append(kp)
                        break

            f.write('\t'.join([str(group.alpha),
                               str(group.size),
                               ' '.join(map(str, group.routes)),
                               ' '.join(group.stops),
                               group.origin,
                               str(self.vars.tg[group.id]),
                               ' '.join(map(str, vehicle_taken))]) + '\n')

        f.close()

    def generate_variables(self):
        raise NotImplementedError(
            ('Decision variables not initialized. Please implement '
             'generate_variables(self) in class %s' %
             self.__class__.__name__))

    def generate_constraints(self):
        raise NotImplementedError(
            ('Constraints not initialized. Please implement '
             'generate_constraints(self) in class %s' %
             self.__class__.__name__))

    def clear_constraints(self):
        self._cp.linear_constraints.delete()

class Variables:

    """A class for storing the decision variables and their values.


    When a solution has been found and populated to the Variables object,
    reference to the decision variables will return its solution value,
    instead of its index in the list of Cplex variables.

    Attributes:
        s (dict): The solution to the problem.
        v (dict): The indices to the decision variables for use in the models.
        solutionFound (bool): Indicates if the solution has been populated.
    """

    def __init__(self, model):
        self.solutionFound = False
        self.model = model

        self.variables = dict()
        self.solutions = dict()

    def register(self, variable, index):
        self.variables[variable] = index

    def setvalues(self, values):
        self.solutions = self._digset(self.variables, values)
        self.solutionFound = True

    def _digset(self, items, values):
        """Recursively assigns solution value to the corresponding variables.

        Values are automatically rounded and cast as integers.
        """
        vartype = isinstance(items, list)*1 + isinstance(items, dict)*2

        if vartype == 0:
            return values[items]
            # return int(round(values[items]))
        else:
            if vartype == 1:
                return [self._digset(item, values) for item in items]
            elif vartype == 2:
                return {key: self._digset(item, values)
                        for key, item in items.iteritems()}

    def resetSolution(self):
        self.solutionFound = False

    def __getattr__(self, attr):
        if attr not in dir(Variables):
            if attr in self.variables:
                if self.solutionFound:
                    return self.solutions[attr]
                else:
                    return self.variables[attr]
        else:
            return eval("self.%s" % (attr,))


class Routes:
    """A collection of route objects."""

    def __init__(self, routes):
        self.routes = routes

    def __getitem__(self, index):
        return self.routes[index]

    def __len__(self):
        return len(self.routes)

    def __iter__(self):
        return iter(self.routes)

    def rsk(self, k_offset=0, s_offset=0):
        """Returns all combinations of routes-stops-buses.

        Used as a short-hand for nested for-loops when generating constraints.

        Use the ``k_offset`` and ``s_offset`` parameters to include/exclude
        the last vehicles/stops from the iteration. Useful for constraints
        involving reference to previous vehicles/stops.

        Args:
            k_offset (int, optional): Number of last buses to exclude.
            s_offset (int, optional): Number of last stops to exclude.
        """
        return [(r, s, k)
                for r in self.routes
                for s in range(r.n_stops - s_offset)
                for k in range(r.n_buses - k_offset)]

    def tf(self):
        """Returns all transfer with the combination of buses for each route.

        Used as a short-hand for nested for-loops when generating constraints.
        """
        return [(r, rp, s, k, kp)
                for r in self.routes
                for rp, ss in r.transfers
                for s in ss
                for k in range(r.n_buses)
                for kp in range(rp.n_buses)]


class Route:

    attributes = ['id', 'name', 'stops', 'n_buses', 'first_bus',
                  'last_bus', 'hw_min', 'hw_max', 'dw_min', 'dw_max']

    def __init__(self, args):
        for attr in Route.attributes:
            setattr(self, attr, args[attr])

        self.n_stops = len(self.stops)
        self.transfers = []

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class Transfer:

    attributes = ['route_to', 'route_from', 'at']

    def __init__(self, args):
        for attr in Transfer.attributes:
            setattr(self, attr, args[attr])


class Groups:

    """A collection of group objects."""

    def __init__(self, groups):
        self.groups = groups

    def __getitem__(self, index):
        return self.groups[index]

    def __len__(self):
        return len(self.groups)

    def __iter__(self):
        return iter(self.groups)

    def gp(self, n=False, k=False, kp=False):
        """Returns different combinations of group-transfers.

        Used as a short-hand for nested for-loops when generating constraints.

        Different combinations can be obtained by changing the parameters
        ``trasfers``, ``k`` and ``kp``

        transfers, k, kp =
        (1, True, True)         : (g, r1, r2, s1, k1, k2)
        (1, True, False)        : (g, r1, r2, o, k)
        (1, False)              : (g, r1, r2, s1)
        (2)                     : (g, r1, rp1, s1, r2, rp2, s2)
        (-1)                    : (g, [(r, rp, s)])
        (False, False, False)   : (g, r, rp, s)
        (False, True, True)     : (g, r, rp, s, k, kp)
        (0, True, True)         : (g, r, k)
        (0, True, False)        : (g, r, o, d, k)
        (0, False)              : (g, r)

        Args:
            n (bool/int, optional): Number of transfers.
                Returns only the first ``n`` transfers if integer is specified.
        """
        if n == 1:
            if k:
                if kp:
                    return [(g, g.routes[0], g.routes[1], g.stops[0], k, kp)
                            for g in self.groups
                            for k in range(g.routes[0].n_buses)
                            for kp in range(g.routes[1].n_buses)]
                else:
                    return [((g, g.routes[0], g.routes[1], g.origin, k)
                             if len(g.routes) > 1
                             else (g, g.routes[0], None, g.origin, k))
                            for g in self.groups
                            for k in range(g.routes[0].n_buses)]

            return [(g, g.routes[0], g.routes[1], g.stops[0]) for g in groups]
        elif n == 2:
            result = []

            for g in self.groups:
                trs = zip(g.routes[:-1], g.routes[1:], g.stops)

                if len(trs) > 1:
                    result += [(g, r1, rp1, s1, r2, rp2, s2)
                               for (r1, rp1, s1), (r2, rp2, s2) in
                               zip(trs[:-1], trs[1:])]

            return result
        elif n == -1:
            return [(g, zip(g.routes[:-1], g.routes[1:], g.stops))
                    for g in self.groups]
        elif n == 0:
            if k:
                if kp:
                    return [(g, g.routes[0], k)
                            for g in self.groups
                            for k in range(g.routes[0].n_buses)]
                else:
                    return [(g, g.routes[0], g.origin, g.destination, k)
                            for g in self.groups
                            for k in range(g.routes[0].n_buses)]
            else:
                return [(g, g.routes[0])
                        for g in self.groups]
        else:
            if not k and not kp:
                return [(g, r, rp, s)
                        for g in self.groups
                        for r, rp, s in
                        zip(g.routes[:-1], g.routes[1:], g.stops)]
            else:
                return [(g, r, rp, s, k, kp)
                        for g in self.groups
                        for r, rp, s in
                        zip(g.routes[:-1], g.routes[1:], g.stops)
                        for k in range(r.n_buses)
                        for kp in range(rp.n_buses)]


class Group:

    attributes = ['id', 'routes', 'stops', 'origin', 'size', 'alpha', 'destination']

    def __init__(self, args):
        for attr in Group.attributes:
            if attr in args:
                setattr(self, attr, args[attr])

    def __repr__(self):
        return 'G%d' % self.id

    def __str__(self):
        return 'G%d' % self.id