from IPython.display import clear_output
import ipywidgets as widgets
import polyline
import gmaps
gmaps.configure(api_key="AIzaSyCZf5uJaTDC_VwqYplD7ZrZGRfL2aQuk2U")

candidate_stops = [[55.786607, 12.522433], [55.789593, 12.524096], [55.786347, 12.518064], [55.785952, 12.520341], [55.783093, 12.515329], [55.782207, 12.520024], [55.786214, 12.521319]]
n_candidate_stops = len(candidate_stops)

polylines_string = [[[],
  'iynsIgxlkAuKkF}D}A',
  'iynsIgxlkAfD~ARH]`DuAfNStB',
  'iynsIgxlkAfD~ARH]`DYvC',
  'iynsIgxlkAfD~ARH]`DuAfNe@|EMtBIrA@~@J|AHxDA~AhANl@Th@ZVVTJp@v@rArAxDrEXZPmBv@aIj@wF',
  'iynsIgxlkAfD~AnGnCrIzDbBv@',
  'iynsIgxlkAfD~ARH]`DoAi@'],
 ['}kosIqbmkAbE`BnKfF',
  [],
  '}kosIqbmkAbE`BvFpC~FnC~@d@RH]`DuAfNStB',
  '}kosIqbmkAbE`BvFpC~FnC~@d@RH]`DYvC',
  '}kosIqbmkAbE`BvFpC~FnC~@d@RH]`DuAfNe@|EMtBIrA@~@J|AHxDA~AhANl@Th@ZVVTJp@v@rArArCdDd@l@XZPmBv@aI^qDJeA',
  '}kosIqbmkAbE`BvFpC~FnC~@d@nGnCvLrF',
  '}kosIqbmkAqAe@uDeB_@dD|HlDnAl@|ExB|IzD'],
 ['uwnsI}|kkAfC_W[MuBcAi@W',
  'uwnsI}|kkAfC_W[MuBcA_McG}D}A',
  [],
  'uwnsI}|kkAnAeM',
  'uwnsI}|kkA_@|EIrA@~@J|AHxDA~AhANl@Th@ZVVTJp@v@rArAxDrEXZPmBv@aIj@wF',
  'uwnsI}|kkAfC_WtKzEvFfCd@T',
  'uwnsI}|kkAd@{EbAaKoAi@'],
 ['eunsIcklkAv@yH[M_D{A',
  'eunsIcklkAv@yH[MmN}GwDaBmAe@',
  'eunsIcklkAoAdM',
  [],
  'eunsIcklkA{@nIe@|EMtBIrA@~@J|AHxDA~AhANl@Th@ZVVTJp@v@rArArCdDd@l@XZPmBv@aI^qDJeA',
  'eunsIcklkAv@yHtKzE|G|C',
  'eunsIcklkAXwCoAi@'],
 ['icnsIykkkAqArMc@rEw@_A[_@eEuEm@q@QSKWcA}@s@Wm@KIE?_C?YWkFGkBLuBv@cI`BcP[M_D{A',
  'icnsIykkkAqArMc@rEw@_A[_@eEuEm@q@QSKWcA}@s@Wm@KIE?_C?YWkFGkBLuBv@cI`BcP[MmN}GwDaBmAe@',
  'icnsIykkkAqArMc@rEw@_A[_@eEuEm@q@QSKWcA}@s@Wm@KIE?_C?YWkFGkBLuBPgB',
  'icnsIykkkAqArMc@rEw@_A[_@eEuEm@q@QSKWcA}@s@Wm@KIE?_C?YWkFGkBLuBv@cIh@iF',
  [],
  'icnsIykkkAj@cFAsAy@a@cAa@EI?c@TkBx@cIz@^PiBF}@|@`@d@T',
  'icnsIykkkAqArMc@rEw@_A[_@eEuEm@q@QSKWcA}@s@Wm@KIE?_C?YWkFGkBLuBv@cIbAaKoAi@'],
 ['y}msIcilkAwLsFoGoC_Ae@gBy@',
  'y}msIcilkAwLsFoGoC_Ae@_GoCwFqCcEaB',
  'y}msIcilkAwLsF{FeC]`DuAfNStB',
  'y}msIcilkAwLsF{FeC]`DYvC',
  'y}msIcilkAcBw@QrBGr@{@_@{@pIUpB?JDJp@Vp@ZZP@rAk@bF',
  [],
  'y}msIcilkAwLsF{FeC]`DoAi@'],
 ['{vnsIeqlkAnAh@\\aD[M_D{A',
  '{vnsIeqlkAnAh@\\aD[MmN}GwDaBmAe@',
  '{vnsIeqlkAnAh@cA`Ke@zE',
  '{vnsIeqlkAnAh@YvC',
  '{vnsIeqlkAnAh@cA`Kw@bIWhE@~@Fr@JxC?lC?ZP@v@Ll@Th@ZVVTJPRl@p@dEtErA~ApA_Nb@gE',
  '{vnsIeqlkAnAh@\\aDtKzE|G|C',
  []]]

polylines = []
for i in range(len(polylines_string)):
    polylines.append([])
    
    for j in range(len(polylines_string)):
        if polylines_string[i][j] != '':
            polylines[i].append(polyline.decode(polylines_string[i][j]))

def map_plot(idx, d):
    line_coords = list(map(lambda i : polylines[i[0]][i[1]], list(zip(idx[:-1], idx[1:]))))

    # Features to draw on the map
    lines = []
    markers = []

    for points in line_coords:
        for p1, p2 in zip(points[:-1], points[1:]):
            lines.append(gmaps.Line(start=p1, end = p2, stroke_weight=3.0))

    for i, p in enumerate(map(lambda x: candidate_stops[x], idx)):
        markers.append(gmaps.Marker(p))
        
    d.features = lines + markers

def route_explorer():
    global re_circular
    global re_stops
    global re_fig
    global re_drawing
    global re_button_stops
    global re_button_circular
    global re_box
    global re_label
    
    def reset():
        global re_label
        global re_drawing

        re_label.value = ', '.join(map(str, re_stops))

        if len(re_stops) >= 2:
            map_plot(re_stops, re_drawing)
        else:
            re_drawing.features = []
        
    def stop_toggled(b):
        global re_stops

        if b['new']:
            if re_circular:
                re_stops.insert(len(re_stops)-1, int(b['owner'].description))
            else:
                re_stops.append(int(b['owner'].description))
        else:
            stop = int(b['owner'].description)

            if re_circular and stop == re_stops[0]:
                re_stops.remove(stop)
                re_stops.remove(stop)

                if len(re_stops) == 0:
                    global re_button_circular
                    re_button_circular.value = False
                else:
                    re_stops.append(stops[0])
            else:
                re_stops.remove(stop)

        reset()

    def circular_toggled(b):
        global re_circular
        global re_stops

        re_circular = b['new']

        if re_circular:
            b['owner'].button_style = 'success'
            if len(re_stops) > 0:
                re_stops.append(stops[0])
        else:
            b['owner'].button_style = ''
            if len(re_stops) > 1:
                re_stops.pop(-1)

        reset()
    
    re_circular = False
    re_stops = []
    re_fig = gmaps.figure(center=(55.785822, 12.521520), zoom_level=16, layout={'height':'800px', 'width':'800px'})
    re_drawing = gmaps.drawing_layer(show_controls=False)
    re_fig.add_layer(re_drawing)
    
    re_buttons_stops = [widgets.ToggleButton(
        description=str(i),
        disabled=False,
        button_style='', # 'success', 'info', 'warning', 'danger' or '',
        layout={'width': '30px', 'height': '30px'}
    ) for i in range(n_candidate_stops)]

    re_button_circular = widgets.ToggleButton(
        description='C',
        disabled=False,
        layout={'width': '30px', 'height': '30px'}
    )
    
    re_box = widgets.Box([widgets.Label('Stops')] + re_buttons_stops + [re_button_circular])
    re_label = widgets.Label('')
    
    for button in re_buttons_stops:
        button.observe(stop_toggled, 'value')
    re_button_circular.observe(circular_toggled, 'value')

    display(re_box)
    display(re_label)
    display(re_fig)

def route_explorer_from_file():
    global reff_fig
    global reff_drawing
    global reff_dropdown
    global reff_routes
    
    reff_routes = open('routes.ipts').read().splitlines()

    reff_dropdown = widgets.Dropdown(
        options=[''] + reff_routes,
        description='Route',
        disabled=False,
    )

    def route_changed(r):
        global reff_drawing
        if r.new != '':        
            map_plot(list(map(int, r.new.split(','))), reff_drawing)
        else:
            reff_drawing.features = []

    reff_dropdown.observe(route_changed, 'value')

    reff_fig = gmaps.figure(center=(55.785822, 12.521520), zoom_level=16, layout={'height':'800px', 'width':'800px'})
    reff_drawing = gmaps.drawing_layer(show_controls=False)
    reff_fig.add_layer(reff_drawing)
    
    display(reff_dropdown)
    display(reff_fig)