import requests
import time

def __walktime(a, b):
	return 1100 * (abs(a[0] - b[0]) + abs(a[1] - b[1]))

def __ridetime(a, b, waypoint=None, speed=15.0):
	# dists = [[0, 348, 650, 361, 212, 1032, 1167, 1130, 511, 784],
	#          [348, 0, 998, 709, 560, 1380, 1515, 1478, 859, 1132],
	#          [659, 1007, 0, 298, 447, 664, 799, 986, 952, 1225],
	#          [361, 709, 289, 0, 149, 671, 806, 993, 654, 927],
	#          [212, 560, 438, 149, 0, 820, 955, 1124, 505, 778],
	#          [1016, 1364, 660, 655, 804, 0, 309, 323, 1309, 885],
	#          [1151, 1499, 795, 790, 939, 309, 0, 632, 481, 576],
	#          [1130, 1478, 983, 978, 1127, 323, 632, 0, 618, 893],
	#          [511, 859, 943, 654, 505, 941, 481, 618, 0, 389],
	#          [784, 1132, 1216, 927, 778, 1216, 576, 893, 389, 0]]
	
	
	if a != b:
		x1, y1 = a
		x2, y2 = b
		
		url = 'https://maps.googleapis.com/maps/api/directions/json'	
		params = dict(
			origin='%f,%f' % (x1, y1),
			destination='%f,%f' % (x2, y2),
			key='AIzaSyCZf5uJaTDC_VwqYplD7ZrZGRfL2aQuk2U'
		)
			
		if waypoint is not None:
			params['waypoints'] = waypoint#'55.789483, 12.523095'

		resp = requests.get(url=url, params=params)
		data = resp.json()
		
		time.sleep(.1)
		return data['routes'][0]['legs'][0]['distance']['value'] / speed / 1000.0 * 60.0
	else:
		return 0
	# polylines[i1][i2] = polyline.decode(data['routes'][0]['overview_polyline']['points'])
	# polylines_string[i1][i2] = data['routes'][0]['overview_polyline']['points']
	# return float(dists[x][y]) / speed / 1000.0 * 60.0

def calculate_costs(demand_nodes, candidate_nodes):
	costs = []

	n_demands = len(demand_nodes)
	n_candidate_stops = len(candidate_nodes)

	for i in range(n_demands + n_candidate_stops):
		costs.append([])

		for j in range(n_demands + n_candidate_stops):
			org = demand_nodes[i] if i < n_demands else candidate_nodes[i-n_demands]
			des = demand_nodes[j] if j < n_demands else candidate_nodes[j-n_demands]

			if i < n_demands or j < n_demands:
				costs[i].append(__walktime(org, des))
			else:
				costs[i].append(__ridetime(org, des))

	return costs