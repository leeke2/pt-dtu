"""Summary
"""
import os
import pickle
from datetime import datetime
from random import randint

from pt.models import Routes, Route, Transfer, Groups, Group
from pt import viz
from plotly.offline import iplot, plot
import time
import os

class Scenario:

    """Represents a test case."""

    _ROUTE_ATTRS = ['routes', 'stops', 'buses', 'sigma_f', 'sigma_l',
                    'delta_min', 'delta_max', 'dwell_min', 'dwell_max']
    _TRANSFER_ATTRS = ['transfers']
    _GROUP_ATTRS = ['groups', 'alpha', 'demands']
    _PARAM_ATTRS = ['M', 'plan_horizon', 'theta', 'omega']

    def __init__(self, name, data=False, transfer=True):
        """Constructs a new Scenario object

        Args:
            name (str): The name of the test case.
                The name specified should not include whitespaces/ This name
                is to be used as the filename of the saved file.

        """
        self._valid = False
        self.name = name
        self.system_generated_name = False

        if data:
            sc._generateRoutes(
                *(data[attr] for attr in Scenario._ROUTE_ATTRS))

            if transfer:
                sc._generateTransfers(data['transfers'])

            sc._generateGroups(
                *(data[attr] for attr in Scenario._GROUP_ATTRS))

            sc.plan_horizon = data['plan_horizon']
            sc.M = data['M']
            sc.theta = data['theta']
            sc.omega = data['omega']

            for attr in Scenario._ROUTE_ATTRS:
                del data[attr]

            for attr in Scenario._GROUP_ATTRS:
                del data[attr]

            del data['transfers']
            del data['plan_horizon']
            del data['M']
            del data['theta']
            del data['omega']

            for key in data:
                sc[key] = data[key]

            sc._name_tmp = None

            return sc

    def _generateRoutes(self, names=None, stops=None, buses=None,
                        first_bus=None, last_bus=None, hw_min=None,
                        hw_max=None, dw_min=None, dw_max=None):
        routes = []

        for r in range(len(names)):
            routes.append(Route({
                'id': r,
                'name': names[r],
                'stops': stops[r],
                'n_buses': buses[r],
                'first_bus': first_bus[r],
                'last_bus': last_bus[r],
                'hw_min': hw_min[r],
                'hw_max': hw_max[r],
                'dw_min': dw_min[r],
                'dw_max': dw_max[r], }))

        self.routes = Routes(routes)

    def _generateTransfers(self, transfers):
        if 'transfers' not in self.__dict__:
            self.transfers = []

        for route1, v in transfers.iteritems():
            for route2, stops in v.iteritems():
                self.routes[route1].transfers.append(
                    (self.routes[route2], stops))

                for stop in stops:
                    self.transfers.append(Transfer({
                        'route_from': self.routes[route1],
                        'route_to': self.routes[route2],
                        'at': stop}))

    def _generateGroups(self, trips=None, alpha=None, demands=None):
        groups = []

        if len(trips[0]) == 3:
            for g, (rs, ss, o) in enumerate(trips):
                groups.append(Group({
                    'id': g,
                    'routes': [self.routes[r] for r in rs],
                    'stops': ss,
                    'origin': o,
                    'size': demands[g],
                    'alpha': alpha[g], }))
        elif len(trips[0]) == 4:
            for g, (rs, ss, o, d) in enumerate(trips):
                groups.append(Group({
                    'id': g,
                    'routes': [self.routes[r] for r in rs],
                    'stops': ss,
                    'origin': o,
                    'destination': d,
                    'size': demands[g],
                    'alpha': alpha[g], }))

        self.groups = Groups(groups)

    def _generateRandomGroups(self, n_groups, max_transfers=2):
        groups = []

        routes = [route.name for route in self.routes]
        stops = [route.stops for route in self.routes]
        transfers = {}

        for transfer in self.transfers:
            if transfer.route_from.id not in transfers:
                transfers[transfer.route_from.id] = {}

            if transfer.route_to.id not in transfers[transfer.route_from.id]:
                transfers[transfer.route_from.id][transfer.route_to.id] = []

            transfers[transfer.route_from.id][transfer.route_to.id].append(transfer.at)

        data = {
            "routes": routes,
            "stops": stops,
            "transfers": transfers
        }

        stops_all = list(set(reduce(lambda x, y: x+y, data['stops'])))

        while len(groups) < n_groups:
            group = False

            while not group:
                origin = stops_all[randint(0, len(stops_all) - 1)]
                destination = stops_all[randint(0, len(stops_all) - 1)]

                while origin == destination:
                    origin = stops_all[randint(0, len(stops_all) - 1)]
                    destination = stops_all[randint(0, len(stops_all) - 1)]

                origin_route_ids = [i for i, _ in enumerate(data['stops']) if origin in data['stops'][i]]

                route_id = origin_route_ids[randint(0, len(origin_route_ids)-1)]
                connections = self._connections(origin, destination, route_id, data)
                if connections:
                    group = connections[randint(0,len(connections)-1)] + (origin,destination)

            groups.append(Group({
                'id': len(groups),
                'routes': [self.routes[r] for r in group[0]],
                'stops': group[1],
                'origin': group[2],
                'size': randint(1, 10),
                'alpha': randint(1, self.plan_horizon/4), }))

        self.groups = Groups(groups)

    def _connections(self, origin, destination, current_route_id, data, current_transfers=0, current_trajectory=[], current_tranfer_stations = [], max_transfers=2):
        if current_trajectory == []:
            current_trajectory = [current_route_id]

        trajectories = []
        
        if destination in data['stops'][current_route_id] and data['stops'][current_route_id].index(origin) < data['stops'][current_route_id].index(destination):
            if current_transfers == 0:
                return False
            else:
                return [(current_trajectory, current_tranfer_stations)]
        else:
            if current_transfers < 2:
                if current_route_id in data['transfers']:
                    for route_id, stations in data['transfers'][current_route_id].iteritems():
                        for station in stations:
                            if station != origin and data['stops'][current_route_id].index(station) > data['stops'][current_route_id].index(origin):
                                ts = self._connections(station, destination, route_id, data, current_transfers+1, current_trajectory + [route_id], current_tranfer_stations + [station])

                                if ts:
                                    for t in ts:
                                        if not t==False and not t[1]==[]:
                                            trajectories.append(t)

                    return trajectories
                else:
                    return False
            else:
                return False

    def __setattr__(self, name, value):
        if ('_name_tmp' in self.__dict__ and
                self._name_tmp is None and
                name != 'name'):

            if not self.system_generated_name:
                self.__dict__['_name_tmp'] = (
                    '%s-%s' % (self.name,
                               str(datetime.now().strftime("%y%m%d%H%M%S%f"))))
            else:
                self.__dict__['_name_tmp'] = (
                    '%s-%s' % (self.name[:-19],
                               str(datetime.now().strftime("%y%m%d%H%M%S%f"))))
            self.system_generated_name = True

        self.__dict__[name] = value

    def set(self, data):
        if all([attr in data for attr in Scenario._ROUTE_ATTRS]):
            self._generateRoutes(
                *(data[attr] for attr in Scenario._ROUTE_ATTRS))

        if 'transfers' in data:
            self._generateTransfers(data['transfers'])

        if 'groups' in data:
            self._generateGroups(
                *(data[attr] for attr in Scenario._GROUP_ATTRS))

    def rename(self, name):
        self._name_tmp = name
        self.system_generated_name = False
        return self

    def save(self):
        if '_name_tmp' not in self.__dict__:
            self._name_tmp = None

        if self._name_tmp is None:
            filename = os.path.join('scenarios', '%s.tc' % self.name)
        else:
            filename = os.path.join('scenarios', '%s.tc' % self._name_tmp)

            ## WARN

        transfers = dict()

        for route1 in self.routes:
            if route1.id not in transfers:
                transfers[route1.id] = {}

            for route2, stops in route1.transfers:
                if route2.id not in transfers[route1.id]:
                    transfers[route1.id][route2.id] = []

                transfers[route1.id][route2.id] = stops

        with open(filename, 'w+') as f:
            attributes = ['routes', 'stops', 'buses', 'dwell_min',
                          'dwell_max', 'sigma_f', 'sigma_l', 'delta_min',
                          'delta_max', 'groups', 'alpha', 'demands']

            data = {attribute: [] for attribute in attributes}

            for route in self.routes:
                data['routes'].append(route.name)
                data['stops'].append(route.stops)
                data['buses'].append(route.n_buses)
                data['dwell_min'].append(route.dw_min)
                data['dwell_max'].append(route.dw_max)
                data['sigma_f'].append(route.first_bus)
                data['sigma_l'].append(route.last_bus)
                data['delta_min'].append(route.hw_min)
                data['delta_max'].append(route.hw_max)

            for group in self.groups:
                if "destination" in dir(group):
                    data['groups'].append(([route.id for route in group.routes],
                                            group.stops, group.origin, group.destination))
                else :
                    data['groups'].append(([route.id for route in group.routes],
                                            group.stops, group.origin))
                data['alpha'].append(group.alpha)
                data['demands'].append(group.size)

            data['plan_horizon'] = self.plan_horizon
            data['M'] = self.M
            data['theta'] = self.theta
            data['omega'] = self.omega

            data['transfers'] = transfers

            pickle.dump(data, f)

        if self._name_tmp is not None:
            self.name = self._name_tmp
            self._name_tmp = None

        return self

    def _exportReport(self, name=False, max_time=False):
        if '_name_tmp' not in self.__dict__:
            self._name_tmp = None

        if self._name_tmp is None:
            report_time = datetime.now()
            # timestamp = str(report_time.strftime("%y%m%d%H%M"))

            if not name:
                f = open(os.path.join("scenarios",
                                      ('report_%s.md' %
                                       (self.name,))), 'wb')
            else:
                f = open('%s_report.md' % name, 'wb')

            viz.init(username='kelvinlee18', api_key='VEAEhweIN3AloAbkxPD4')

            md = "# Scenario specification\n**Scenario:** %s  \n**Report generated:** %s  \n\n## Parameters\n**M:** %d  \n**Planning horizon:** %d\n\n## Routes\n| Route | #   | First | Last | Headway | Dwell | Stops    |\n| :---- | :-: | :---: | :--: | :-----: | :---: | :------- |\n%s\n\n## Travel time\n%s \n## Transfers\n<table><thead><tr><th align=\"left\">From</th><th align=\"left\">At</th><th align=\"left\">To</th><th align=\"center\">Transfer time</th></tr></thead><tbody>%s</tbody></table>\n\n## Groups\n\n| Group | Size | Origin | Arrival | Itinerary |\n| ----- | :--: | :----: | :-----: | :-------- |\n%s"

            routes = ""
            travel_times = ""
            for r in self.routes:
                routes += "| " + " | ".join([r.name, str(r.n_buses), str(r.first_bus if r.first_bus is not None else "-"), str(r.last_bus if r.last_bus is not None else "-"), "[%d, %d]" % (r.hw_min, r.hw_max), "[%d, %d]" % (r.dw_min, r.dw_max), " ".join(r.stops)]) + " |\n"
                
                image_filename = "%s_%s" % (self.name, r.name)
                travel_times += "![TT-%s](img/%s.png)\n" % (r.name, image_filename)

                if max_time:
                    fig = viz.travelTime(self, route=r.id, max_time=max_time)
                else:
                    fig = viz.travelTime(self, route=r.id)
                plot(fig, image_filename=image_filename, image="png", output_type="file", image_width=888)#, image_height=fig_schedule.layout.height)
                time.sleep(2)
                os.rename("/Users/kelvinlee/Downloads/%s.png" % (image_filename, ), os.path.join("scenarios", "img", "%s.png" %(image_filename, )))

            groups = ""
            for g in self.groups:
                stops = g.stops + [""]
                groups += "| " + " | ".join(["G%d" % (g.id, ), str(g.size), g.origin, str(g.alpha), " ".join([":oncoming_bus: **%s** %s" % (r.name, ("(%s)" % (s,) if s != "" else "")) for r, s in zip(g.routes, stops)])]) + " |\n"

            # print md % (self.name, 0, self.M, self.plan_horizon, routes, groups)

            transfers = ""
            rows_from = []
            a = {0: {"S2": {1: 3, 2: 5}, "S3": {1: 2}}, 1: {"S2": {0: 2}, "S3": {0: 1}}}
            # for f, ad in self.omega.iteritems():
            for fr, ad in a.iteritems():
                nrows_at = 0
                rows_at = []

                for at, td in ad.iteritems():
                    rows_to = []

                    for to, tt in td.iteritems():
                        rows_to.append("<td align=\"left\">%s</td><td align=\"center\">%d</td>" % (self.routes[to].name, tt))

                    if len(rows_to) > 1:
                        rows_at.append("<td rowspan=\"%d\" align=\"left\">%s</td>%s" % (len(rows_to), at, rows_to.pop(0)))
                    else:
                        rows_at.append("<td align=\"left\">%s</td>%s" % (at, rows_to.pop(0)))

                    rows_at += ["%s" % (r,) for r in rows_to]
                    nrows_at += len(rows_to) + 1

                if len(rows_at) > 1:
                    rows_from.append("<tr><td rowspan=\"%d\" align=\"left\">%s</td>%s</tr>" % (nrows_at, self.routes[fr].name, rows_at.pop(0)))
                else:
                    rows_from.append("<tr><td align=\"left\">%s</td>%s</tr>" % (self.routes[fr].name, rows_at.pop(0)))

                rows_from += ["<tr>%s</tr>" % (r, ) for r in rows_at]

            transfers = "".join(rows_from)

            f.write(md % (self.name, report_time.strftime("%c"), self.M, self.plan_horizon, routes, travel_times, transfers, groups))

        else:
            # error
            pass

    @classmethod
    def load(cls, name):
        """Returns a new Scenario object from saved test case.

        If the specified file does not exist, or when the required inputs are
        not given in the test case, an exception is raised

        Args:
            fn (str): The name of the test case.
                Do not include the file extension .tc. Test cases by default,
                should be stored in scenarios folder under the base directory.
        """
        if os.path.isfile(os.path.join('scenarios', '%s.tc' % (name, ))):
            with open(os.path.join('scenarios', '%s.tc' % (name, ))) as f:
                sc = cls(name)

                data = pickle.load(f)

                sc._generateRoutes(
                    *(data[attr] for attr in Scenario._ROUTE_ATTRS))

                sc._generateTransfers(data['transfers'])

                sc._generateGroups(
                    *(data[attr] for attr in Scenario._GROUP_ATTRS))

                sc.plan_horizon = data['plan_horizon']
                sc.M = data['M']
                sc.theta = data['theta']
                sc.omega = data['omega']

            sc._name_tmp = None

            return sc
        else:
            raise IOError('Test case %s does not exist.' %
                          os.path.join('scenarios', '%s.tc' % name))