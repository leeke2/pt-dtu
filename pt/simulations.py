import numpy as np
from copy import deepcopy
import pandas as pd


# TODO: Fix schedule and ridetime for circular routes

def generate_schedule(adm, frequencies, costs):
    routes = []
    headways = [round(headway, 2) for headway in (1/np.array(frequencies)).tolist()]
    schedules = []

    def route_nodes(adm):
        n_candidate_stops = len(adm) - 2
        links = np.argwhere(np.round(adm)).tolist()
        nodes = []

        first_link = filter(lambda link: link[0] == n_candidate_stops, links)[0]
        links.remove(first_link)

        nodes += first_link

        while len(links) > 0:
            link = filter(lambda link: link[0] == nodes[-1], links)[0]
            links.remove(link)

            nodes.append(link[1])

        return nodes

    def schedule_times(offsets, headway, latest_departure=60):
        depot_departures = []

        t = 0
        while(t < latest_departure):
            depot_departures.append(t)
            t += headway

        schedule = np.vstack([depot_departures] * len(offset))
        schedule += np.array(offsets).reshape(-1, 1)

        return np.round(schedule, 2).tolist()

    for idx, r in enumerate(adm):
        route = route_nodes(r)

        rt = [round(costs[i][j], 2)
              for i,j in zip(route[1:-2], route[2:-1])]
        offset = np.cumsum([0] + rt).tolist()

        schedules.append(schedule_times(offset, headways[idx]))

    return schedules

def generate_arrivals(demands, latest_arrival=20, seed=0):
    arrivals = []
    np.random.seed(seed)

    for i in range(len(demands)):
        arrivals.append([])

        for j in range(len(demands[i])):
            rand = np.random.uniform(1, 0, int(demands[i][j] * 2 * latest_arrival))

            od_arrivals = np.round(-np.log(rand) / demands[i][j], 2)
            od_arrivals = np.cumsum(od_arrivals)

            arrivals[i].append(np.around(od_arrivals[od_arrivals < latest_arrival], 2).tolist())

    return arrivals

def generate_trips(arrivals, costs, rx, x):
    n_demands = len(x)
    passenger_trips = []
    routes = []
    idx = 0
    trip_idx = 1

    def route_nodes(adm):
        n_candidate_stops = len(adm) - 2
        links = np.argwhere(np.round(adm)).tolist()
        nodes = []

        first_link = filter(lambda link: link[0] == n_candidate_stops, links)[0]
        links.remove(first_link)

        nodes += first_link

        while len(links) > 0:
            link = filter(lambda link: link[0] == nodes[-1], links)[0]
            links.remove(link)

            nodes.append(link[1])

        return nodes

    def trip_path(x):
        links = np.argwhere(np.round(x)).tolist()
        nodes = []

        if len(links) > 0:
            sets = map(set, zip(*links))
            first_node = list(sets[0] - sets[1])[0]

            first_link = filter(lambda link: link[0] == first_node, links)[0]
            links.remove(first_link)

            nodes += first_link

            while len(links) > 0:
                link = filter(lambda link: link[0] == nodes[-1], links)[0]
                links.remove(link)

                nodes.append(link[1])

            return nodes
    
    def path_transfers(nodes, routes, costs):
        n_candidates = None
        is_circular = []
        
        # Look for circular routes
        for route in routes:
            if route[0] == route[-1]:
                n_candidates = route[0]
                is_circular.append(True)
            else:
                is_circular.append(False)
                
        # Guess n_candidates if no circular route found
        if n_candidates is None:
            n_candidates = max(reduce(lambda x,y: x+y, routes)) - 1
        
        routes = deepcopy(routes)
        for i, _ in enumerate(routes):
            if is_circular[i]:
                routes[i] = routes[i][:-1] + routes[i][1:]
                
        def nodes_in_route(nodes, route):
            if nodes[0] not in route:
                return False
            
            idx = route.index(nodes[0])
            if route[idx:idx+len(nodes)] != nodes:
                return False
            
            return True
        
        def merge(a, b, forbid=None):
            res = []

            for y in b:
                if forbid is None or (forbid is not None and y[0][0] != forbid):
                    res.append((a[0]+y[0], a[1]+y[1]))

            return res if res != [] else None
        
        def cost(org, des, path, routes):
            cost = 0.0

            for i, r in enumerate(path[0]):
                end_stop = path[1][i] if i != len(path[0])-1 else des

                if i == 0:
                    idx = routes[r].index(org)
                else:
                    idx = routes[r].index(path[1][i-1])
                
                while routes[r][idx] != end_stop:
                    cost += costs[routes[r][idx]+n_demands][routes[r][idx+1]+n_demands]
                    idx += 1

            return cost
        
        def rfind(nodes, routes):
            paths = []
            
            if len(nodes) == 2:
                return [([r], []) for r, route in enumerate(routes) 
                        if nodes_in_route(nodes, route)]
            else:
                for offset in range(len(nodes) -1):
                    if offset == 0:
                        possible_routes = [nodes_in_route(nodes, route) for route in routes]
                    else:
                        possible_routes = [nodes_in_route(nodes[:-offset], route) for route in routes]
                        
                    if sum(possible_routes) == 0:
                        paths.append(None)
                    elif offset == 0:
                        paths += [([i], []) for i, r in enumerate(possible_routes) if r]
                    else:
                        res = rfind(nodes[-offset-1:], routes)

                        if res is not None:
                            paths += [merge(([i], [nodes[len(nodes)-1-offset]]), res, forbid=i)
                                      for i, p in enumerate(possible_routes)
                                      if p]

                        
            paths_tmp = []
            for p in paths:
                if p is not None:
                    paths_tmp.append(p)
            
            return paths_tmp
        
        paths = rfind(nodes, routes)

        path_costs = [cost(nodes[0], nodes[-1], path, routes) for path in paths]
        return paths[np.argmin(path_costs)]

    ########################################################

    for route in rx:
        routes.append(route_nodes(route))

    for o in range(len(arrivals)):
        for d in range(len(arrivals[o])):
            if o != d:
                route_od = []
                path = trip_path(x[o][d])

                if len(path) > 2:
                    path[1:-1] = map(lambda node: node - n_demands, path[1:-1])
                    transfers = path_transfers(path[1:-1], routes, costs)
                    transfers = zip(transfers[0], transfers[1] + [-1])

                    if len(transfers) == 1:
                        route_od.append((transfers[0][0], path[1], path[-2]))
                    else:
                        for i, (r,s) in enumerate(transfers):
                            if i == 0:
                                route_od.append((r, path[1], s))
                            elif s == -1:
                                route_od.append((r, route_od[-1][2], path[-2]))
                            else:
                                route_id.append((r, route_od[-1][2], s))

                    for arrival in arrivals[o][d]:
                        for i, (r,a,b) in enumerate(route_od[::-1]):
                            if i == len(route_od) - 1: # First
                                alpha = arrival
                            else:
                                alpha = -1

                            if i == 0: # Last
                                update = -1
                            else:
                                update = idx - 1

                            passenger_trips.append(pd.Series({'trip': trip_idx,
                                                              'idx': idx,
                                                              'origin': o,
                                                              'destination': d,
                                                              'alpha': alpha,
                                                              'route': r,
                                                              'start': a,
                                                              'end': b,
                                                              'update': update,
                                                              'type': 'ride',
                                                              'walktime': costs[o][d]}))
                            idx += 1
                        trip_idx += 1
                else:
                    for arrival in arrivals[o][d]:
                        passenger_trips.append(pd.Series({'trip': trip_idx,
                                                          'idx': idx,
                                                          'origin': path[0],
                                                          'destination': path[1],
                                                          'alpha': arrival,
                                                          'route': -1,
                                                          'start': -1,
                                                          'end': -1,
                                                          'update': -1,
                                                          'type': 'walk',
                                                          'walktime': costs[path[0]][path[1]]}))
                        idx += 1
                        trip_idx += 1

    return  pd.DataFrame(passenger_trips)
    
def calculate_waiting_times(trips, rx, schedule, max_capacity):
    routes = []
    events = []

    def route_nodes(adm):
        n_candidate_stops = len(adm) - 2
        links = np.argwhere(np.round(adm)).tolist()
        nodes = []

        first_link = filter(lambda link: link[0] == n_candidate_stops, links)[0]
        links.remove(first_link)

        nodes += first_link

        while len(links) > 0:
            link = filter(lambda link: link[0] == nodes[-1], links)[0]
            links.remove(link)

            nodes.append(link[1])

        return nodes

    for route in rx:
        routes.append(route_nodes(route))

    for r, sr in enumerate(schedule):
        for s, srs in enumerate(sr):
            for k, srsk in enumerate(srs):
                events.append((srsk,r,routes[r][s+1],k))
                
    events = sorted(events)

    trips = trips.copy()
    trips.sort_values(by='alpha')
    trips['served'] = 0

    capacity = [[0 for _ in route_schedule[0]] for route_schedule in schedule]
    occupants = [[[] for _ in route_schedule[0]] for route_schedule in schedule]
    
    for event in events:
        t, r, s, k = event

        if s == routes[r][1]:
            capacity[r][k] = 30

        occ = trips.loc[occupants[r][k], :]
        if len(occ > 0):
            alight = occ[occ.end == s].idx.values.tolist()

            if len(alight) > 0:
                capacity[r][k] += len(alight)
                occupants[r][k] = [x for x in occupants[r][k] if x not in alight]
                
                for idx in alight:
                    if trips.loc[idx, 'update'] != -1:
                        trips.loc[ps.loc[idx, 'update'], 'alpha'] = t

                trips.loc[alight, 'alight'] = t

        board = trips[(trips.type == 'ride') & (trips.start == s) & (trips.alpha < t) & (trips.alpha > 0) & (trips.served == 0) & (trips.route == r)]
        if len(board) > 0:
            board = board[:capacity[r][k]].idx.values.tolist()
            
            trips.loc[board, 'served'] = 1
            occupants[r][k] += board

            capacity[r][k] -= len(board)

            trips.loc[board, 'board'] = t
            
        if s == routes[r][-2]:
            capacity[r][k] = 0

    trips['ridetime'] = trips.alight - trips.board
    trips['waittime'] = trips.board - trips.alpha

    return trips

def calculate_walktrips_percentage(trips):
    print trips.groupby('trip').first().reset_index().groupby('type').trip.count()

def calculate_statistics(trips):
    return trips.waittime.describe().reset_index().rename(columns={'index': 'statistic', 'waittime': 'value'})

def simulate(return_trips=False, **kwargs):
    rx = kwargs['rx']
    x = kwargs['x']
    max_capacity = kwargs['max_capacity']
    demands = kwargs['demands']
    costs = kwargs['costs']
    frequencies = kwargs['frequencies']
    n_demands = len(x)

    if 'latest_arrival' in kwargs:
        latest_departure = kwargs['latest_departure']
    else:
        latest_departure = 60

    if 'latest_arrival' in kwargs:
        latest_arrival = kwargs['latest_arrival']
    else:
        latest_arrival = 20

    if 'seeds' in kwargs:
        seeds = kwargs['seeds']
    else:
        seeds = [0]

    trips_arr = []
    stats = []
    schedule = generate_schedule(rx, frequencies, np.array(costs)[n_demands:, n_demands:],)

    for seed in seeds:
        arrivals = generate_arrivals(demands, latest_arrival=latest_arrival, seed=seed)
        trips = generate_trips(arrivals, costs, rx, x)
        trips = calculate_waiting_times(trips, rx, schedule, max_capacity)

        trips_arr.append(trips)

        stat = calculate_statistics(trips)
        stat['seed'] = seed
        stat = stat[['seed', 'statistic', 'value']]

        stats.append(stat)

    if return_trips:
        return trips_arr
    else:
        return pd.concat(stats)


