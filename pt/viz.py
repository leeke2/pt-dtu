"""Summary

Attributes:
    colors (TYPE): Description
    layout_def (TYPE): Description
"""
import os

from plotly.tools import set_credentials_file
from plotly.offline import init_notebook_mode
from plotly.graph_objs import Scatter, Figure, Layout, Annotations, Annotation

colors = [u'#008fd5', u'#fc4f30', u'#e5ae38',
          u'#6d904f', u'#8b8b8b', u'#810f7c']

layout_def = Layout(
    height=200,
    plot_bgcolor='#f7f7f7',
    paper_bgcolor='#f7f7f7',
    # plot_bgcolor='#f0f0f0',
    # paper_bgcolor='#f0f0f0',
    # showlegend=False,
    font=dict(
        family='Arial',
        size=12),
    xaxis=dict(
        autorange=True,
        showgrid=False,
        zeroline=False,
        showline=False,
        # autotick=True,
        ticks='',
        showticklabels=False,
        title='Time (minutes)'),
    yaxis=dict(
        autorange=True,
        showgrid=False,
        zeroline=True,
        zerolinewidth=1,
        zerolinecolor='rgb(.95,.95,.95)',
        showline=False,
        ticks='',
        showticklabels=False),
    margin=dict(
        l=100,
        r=50,
        b=90,
        t=30,
        pad=4))


def init(username=None, api_key=None, notebook_mode=False):
    """Establishes connection to plot.ly with the correct credentials.

    Args:
        username: Defaults to None
        api_key: Defaults to None
        notebook_mode (bool): Defaults to False

    Raises:
        RuntimeError: If no credential is provided, either as arguments
            or as a viz.conf config file in the working directory.
    """
    if username is None or api_key is None:
        if os.path.exists('vizz.conf'):
            print 'yay!'
        else:
            raise RuntimeError('')
    elif username is not None and api_key is not None:
        set_credentials_file(username=username, api_key=api_key)

    if notebook_mode:
        init_notebook_mode(connected=True)

    global layout
    layout = layout_def


def alter_layout(mods, g=False):
    """Make modifications to the default plot.ly layout.

    Args:
        mods (dict): Modifications to be made to the default layout
        g (bool): Defaults to False.
            If set to True, modifications are made globally.

    Returns:
        TYPE: Description
    """
    lo = layout_def

    for k, v in mods.iteritems():
        if isinstance(v, dict):
            for k2, v2 in v.iteritems():
                lo[k][k2] = v2
        else:
            lo[k] = v

    if g:
        global layout
        layout = lo
    else:
        return lo


def schedule(soln, sc, offset=False):
    """Summary

    Args:
        arr (TYPE): Description
        dep (TYPE): Description
        rs (TYPE): Description
        offset (int, optional): Description

    Returns:
        TYPE: Description
    """

    arr = [soln.a[0]]
    dep = [soln.d[0]]

    traces = []

    x_arr = []
    y_arr = []
    text_arr = []

    x_dep = []
    y_dep = []
    text_dep = []

    tooltip = '<b>Route</b>: {}<br><b>Bus</b>: {}<br>'\
        '<b>Arrival</b>: {}<br><b>Departure</b>: {}'

    for r, (arr_r, dep_r) in enumerate(zip(arr, dep)):
        x_arr += arr_r
        y_arr += [r] * len(arr_r)
        text_arr += [tooltip.format(sc.routes[r].name, k, arr, dep)
                     for k, (arr, dep) in enumerate(zip(arr_r, dep_r))]

        x_dep += dep_r
        y_dep += [r] * len(dep_r)
        text_dep += [tooltip.format(sc.routes[r].name, k, arr, dep)
                     for k, (arr, dep) in enumerate(zip(arr_r, dep_r))]

    traces.append(Scatter(
        x=x_arr,
        y=[-y-offset for y in y_arr],
        mode='markers',
        marker=dict(
            size=20,
            color=[0] * len(x_arr),
            colorscale='RdBu'),
        hoverinfo='text',
        text=text_arr,
        opacity=.3,
        showlegend=False))

    traces.append(Scatter(
        x=x_dep,
        y=[-y-offset for y in y_dep],
        mode='markers',
        marker=dict(
            symbol='triangle-right',
            size=10,
            color=[colors[r] for r in y_dep]),
        hoverinfo='text',
        text=text_dep,
        showlegend=False))

    if type(offset) is bool:
        for route in sc.routes:
            traces.append(Scatter(
                x=[sc.plan_horizon*2, sc.plan_horizon*2],
                y=[route.id, route.id],
                mode='lines+markers',
                marker=dict(
                    size=10,
                    color=[colors[route.id], colors[route.id]]
                ), line=dict(
                    width=5,
                    color=colors[route.id]
                ), showlegend=True,
                name='Route %s' % route.name))

        lo = alter_layout(dict(
            hovermode='closest',
            height=30*(len(sc.routes)+1)+30+90,
            yaxis=dict(
                zeroline=False,
                showgrid=False,
                tickvals=[-x for x in range(len(sc.routes))],
                ticktext=[r.name for r in sc.routes],
                showticklabels=True,
                autorange=False,
                range=[-len(sc.routes), 1]),
            xaxis=dict(showgrid=True,
                       # autotick=False,
                       dtick=10,
                       showticklabels=True,
                       range=[-1, sc.plan_horizon+1],
                       autorange=False),
            annotations=Annotations([
                Annotation(
                    x=0.5,
                    y=-85.0/30/(len(sc.routes)+1),
                    showarrow=False,
                    text='%s_%s_%s' % (soln.model.timestamp,
                                       soln.model.__class__.__name__,
                                       sc.name),
                    align='center',
                    xref='paper',
                    yref='paper',
                    font=dict(
                        family='SF Mono',
                        size=11,
                        color='rgba(0,0,0,.2)'))])))

        return Figure(data=traces, layout=lo)
    else:
        return (traces,
                zip([-y-offset for y in range(len(sc.routes))],
                    [r.name for r in sc.routes]))


def connectivity(soln, sc, offset=False):
    """Summary

    Args:
        c (TYPE): Description
        arr (TYPE): Description
        dep (TYPE): Description
        rs (TYPE): Description
        ss (TYPE): Description
        o (TYPE): Description
        offset (int, optional): Description

    Returns:
        TYPE: Description
    """
    traces = []
    t = 0
    ticktext = []

    x_arr = []
    y_arr = []
    r_arr = []
    text_arr = []

    x_dep = []
    y_dep = []
    r_dep = []
    text_dep = []

    for r, v1 in soln.c.iteritems():
        for rp, v2 in v1.iteritems():
            for s, cs in v2.iteritems():
                station_r = sc.routes[r].stops.index(s)
                station_rp = sc.routes[rp].stops.index(s)

                x_arr += [a for a in soln.a[r][station_r]]
                y_arr += [t] * len(soln.a[r][station_r])
                r_arr += [r] * len(soln.a[r][station_r])

                for k in range(sc.routes[r].n_buses):
                    kp = min([kp if cs[k][kp] == 1 else 999
                              for kp in range(sc.routes[rp].n_buses)])

                    if kp == 999:
                        text_arr.append('<b>Arrival</b>: %s<br>'
                                        '<b>Connects</b>: NC'
                                        % soln.a[r][station_r][k])
                    else:
                        text_arr.append('<b>Arrival</b>: %s<br>'
                                        '<b>Connects</b>: %s-%s'
                                        % (soln.a[r][station_r][k],
                                           sc.routes[rp].name,
                                           kp))

                x_dep += [d for d in soln.d[rp][station_rp]]
                y_dep += [t] * sc.routes[rp].n_buses
                r_dep += [rp] * sc.routes[rp].n_buses
                text_dep += ['{}-{}'.format(sc.routes[rp].name, kp)
                             for kp in range(sc.routes[rp].n_buses)]

                ticktext.append('%s-%s (%s)'
                                % (sc.routes[r].name, sc.routes[rp].name, s))
                t += 1

    traces.append(Scatter(
        x=x_arr,
        y=[-y-offset for y in y_arr],
        mode='markers',
        marker=dict(
            size=20,
            color=[colors[r] for r in r_arr]),
        hoverinfo='text',
        text=text_arr,
        showlegend=False))

    traces.append(Scatter(
        x=x_dep,
        y=[-y-offset for y in y_dep],
        mode='markers',
        marker=dict(
            symbol='triangle-right',
            size=10,
            color=[colors[r] for r in r_dep]),
        hoverinfo='text',
        text=text_dep,
        showlegend=False))

    if type(offset) is bool:
        for route in sc.routes:
            traces.append(Scatter(
                x=[sc.plan_horizon*2, sc.plan_horizon*2],
                y=[route.id, route.id],
                mode='lines+markers',
                marker=dict(
                    size=10,
                    color=[colors[route.id], colors[route.id]]
                ), line=dict(
                    width=5,
                    color=colors[route.id]
                ), showlegend=True,
                name='Route %s' % route.name))

        lo = alter_layout(dict(
            hovermode='closest',
            height=90 + 30 + 30*(t+1),
            yaxis=dict(
                zeroline=False,
                showgrid=False,
                tickvals=[-x for x in range(t)],
                ticktext=ticktext,
                showticklabels=True,
                autorange=False,
                range=[-t, 1]
                ),
            xaxis=dict(
                autorange=False,
                range=[-1, sc.plan_horizon+1],
                showgrid=True,
                # autotick=False,
                dtick=10,
                showticklabels=True),
            annotations=Annotations([
                Annotation(
                    x=0.5,
                    y=-85.0/30/(t+1),
                    showarrow=False,
                    text='%s_%s_%s' % (soln.model.timestamp,
                                       soln.model.__class__.__name__,
                                       sc.name),
                    align='center',
                    xref='paper',
                    yref='paper',
                    font=dict(
                        family='SF Mono',
                        size=11,
                        color='rgba(0,0,0,.2)'))])))

        return Figure(data=traces, layout=lo)
    else:
        return traces, zip([-y-offset for y in range(t)], ticktext)


def trip(soln, sc, offset=False):
    """Summary

    Args:
        gr (TYPE): Description
        p (TYPE): Description
        arr (TYPE): Description
        dep (TYPE): Description
        stations (TYPE): Description
        omega (TYPE): Description
        alpha (TYPE): Description
        offset (int, optional): Description

    Returns:
        TYPE: Description
    """
    traces = []

    for group in sc.groups:
        sp = group.origin

        for r, rp, s in zip(group.routes[:-1], group.routes[1:], group.stops):
            station_r = r.stops.index(s)
            station_rp = rp.stops.index(s)

            for k, kp in [(k, kp) for k in range(r.n_buses)
                          for kp in range(rp.n_buses)]:
                if soln.p[r.id][rp.id][s][k][kp][group.id] == 1:
                    traces.append(Scatter(
                        x=[soln.d[r.id][r.stops.index(sp)][k],
                           soln.a[r.id][station_r][k]],
                        y=[-offset-group.id, -offset-group.id],
                        mode='lines+markers',
                        marker=dict(
                            size=10,
                            color=[colors[r.id], colors[r.id]]),
                        line=dict(
                            width=5,
                            color=colors[r.id]),
                        hoverinfo='text',
                        text=['<b>Bus</b>: R%s-%s<br><b>Departs</b>: %s'
                              % (r.id,
                                 k,
                                 soln.d[r.id][r.stops.index(sp)][k]),
                              '<b>Bus</b>: R%s-%s<br><b>Arrives</b>: %s'
                              '<br><b>Transfer time</b>: %s'
                              % (r.id,
                                 k,
                                 soln.a[r.id][station_r][k],
                                 sc.omega[r.id][s][rp.id])],
                        showlegend=False))

                    break
            sp = s

        traces.append(Scatter(
            x=[soln.d[rp.id][rp.stops.index(sp)][kp], min(
                soln.d[rp.id][rp.stops.index(sp)][kp] + 5, sc.plan_horizon)],
            y=[-offset-group.id, -offset-group.id],
            mode='lines',
            line=dict(
                width=5,
                color=colors[rp.id],
                dash="dot"),
            hoverinfo='text',
            text=['<b>Bus</b>: R%s-%s<br><b>Departs</b>: %s'
                  % (rp.id, kp, soln.d[rp.id][rp.stops.index(sp)][kp]), ''],
            showlegend=False))

        traces.append(Scatter(
            x=[soln.d[rp.id][rp.stops.index(sp)][kp]],
            y=[-offset-group.id],
            mode='markers',
            marker=dict(
                size=10,
                color=[colors[rp.id], colors[rp.id]]),
            hoverinfo='text',
            text=['<b>Bus</b>: R%s-%s<br><b>Departs</b>: %s'
                  % (rp.id, kp, soln.d[rp.id][rp.stops.index(sp)][kp]), ''],
            showlegend=False))

        traces.append(Scatter(
            x=[g.alpha for g in sc.groups],
            y=[-y-offset for y in range(len(sc.groups))],
            mode='markers',
            marker=dict(
                size=10,
                color=[0] * len(sc.groups),
                colorscale='RdBu',
                cmin=-1,
                cmax=1),
            hoverinfo='text',
            showlegend=False))

    if type(offset) is bool:
        for route in sc.routes:
            traces.append(Scatter(
                x=[sc.plan_horizon*2, sc.plan_horizon*2],
                y=[route.id, route.id],
                mode='lines+markers',
                marker=dict(
                    size=10,
                    color=[colors[route.id], colors[route.id]]
                ), line=dict(
                    width=5,
                    color=colors[route.id]
                ), showlegend=True,
                name='Route %s' % route.name))

        lo = alter_layout(dict(
            hovermode='closest',
            height=90 + 30 + 30*(len(sc.groups)+1),
            yaxis=dict(
                zeroline=False,
                showgrid=False,
                tickvals=[-x for x in range(len(sc.groups))],
                # ticktext=[('G%d (' % (g.id, )) + '-'.join([g.origin] + g.stops) + '-)'
                #           for g in sc.groups],
                ticktext=['-'.join([g.origin] + g.stops) + '-S6'
                          for g in sc.groups],
                showticklabels=True,
                autorange=False,
                range=[-len(sc.groups), 1]),
            xaxis=dict(
                autorange=False,
                range=[-1, sc.plan_horizon + 1],
                showgrid=True,
                # autotick=False,
                dtick=10,
                showticklabels=True),
            annotations=Annotations([
                Annotation(
                    x=0.5,
                    y=-85.0/30/(len(sc.groups)+1),
                    showarrow=False,
                    text='%s_%s_%s' % (soln.model.timestamp,
                                       soln.model.__class__.__name__,
                                       sc.name),
                    align='center',
                    xref='paper',
                    yref='paper',
                    font=dict(
                        family='SF Mono',
                        size=11,
                        color='rgba(0,0,0,.2)'))])))

        return Figure(data=traces, layout=lo)
    else:
        return (traces,
                zip([-y-offset for y in range(len(sc.groups))],
                    [('G%d (' % (g.id, )) + '-'.join([g.origin] + g.stops) + '-)'
                        for g in sc.groups]))


def comprehensive(soln, sc):
    traces_all = []
    ticks_all = []
    n_routes = 0
    n_transfers = 0

    trs, tks = schedule(soln, sc, offset=0)
    traces_all += trs
    ticks_all += tks
    n_routes = len(tks)

    trs, tks = connectivity(soln, sc, offset=len(ticks_all)+1)
    traces_all += trs
    ticks_all += tks
    n_transfers = len(tks)

    trs, tks = trip(soln, sc, offset=len(ticks_all)+2)
    traces_all += trs
    ticks_all += tks

    traces_all.append(Scatter(
        x=[0, sc.plan_horizon, None,
           0, sc.plan_horizon],
        y=[-n_routes, -n_routes, None,
           -n_transfers-n_routes-1, -n_transfers-n_routes-1],
        mode='lines',
        line=dict(
            color='rgba(100,100,100,.3)',
            width=2,
            dash='dot'
        ), showlegend=False
    ))

    traces_all.append(Scatter(
        x=[sc.plan_horizon-14]*3,
        y=[0, -n_routes-1, -n_routes-n_transfers-2],
        mode='text',
        text=['<b>Schedule</b>', '<b>Transfers</b>', '<b>Trips</b>'],
        textposition='middlright',
        textfont={
            'size': 13,
            'color': '#333333'
        }, showlegend=False
    ))

    for route in sc.routes:
        traces_all.append(Scatter(
            x=[sc.plan_horizon*2, sc.plan_horizon*2],
            y=[route.id, route.id],
            mode='lines+markers',
            marker=dict(
                size=10,
                color=[colors[route.id], colors[route.id]]
            ), line=dict(
                width=5,
                color=colors[route.id]
            ), showlegend=True,
            name='Route %s' % route.name))

    lo = alter_layout(dict(
        hovermode='closest',
        height=90 + 30 + 30*(len(ticks_all)+3),
        yaxis=dict(
            zeroline=False,
            showgrid=False,
            tickvals=zip(*ticks_all)[0],
            ticktext=zip(*ticks_all)[1],
            showticklabels=True,
            autorange='False',
            range=[-len(ticks_all)-2, 1]),
        xaxis=dict(
            autorange=False,
            range=[-1, sc.plan_horizon+1],
            showgrid=True,
            # autotick=False,
            dtick=10,
            showticklabels=True),
        annotations=Annotations([
            Annotation(
                x=0.5,
                y=-85.0/30/(len(ticks_all)+3),
                showarrow=False,
                text='%s_%s_%s' % (soln.model.timestamp,
                                   soln.model.__class__.__name__,
                                   sc.name),
                align='center',
                xref='paper',
                yref='paper',
                font=dict(
                    family='SF Mono',
                    size=11,
                    color='rgba(0,0,0,.2)'))])))

    return Figure(data=traces_all, layout=lo)

def travelTime(sc, route=False, max_time=False, offset=False):
    traces = []

    tooltip = '<b>Route</b>: {}<br><b>Bus</b>: {}<br>'\
        '<b>Arrival</b>: {}<br><b>Departure</b>: {}'

    for r in range(len(sc.theta)):
        if r == route:
            for s in range(len(sc.theta[r])):
                traces.append(Scatter(
                    x=range(len(sc.theta[r][s])),
                    y=sc.theta[r][s],
                    name="%s (%s-%s)" % (sc.routes.routes[r], sc.routes.routes[r].stops[s], sc.routes.routes[r].stops[s+1]),
                    line=dict(shape='hv'),
                    showlegend=True))

    # if type(offset) is bool:
    #     for route in sc.routes:
    #         traces.append(Scatter(
    #             x=[sc.plan_horizon*2, sc.plan_horizon*2],
    #             y=[route.id, route.id],
    #             mode='lines+markers',
    #             marker=dict(
    #                 size=10,
    #                 color=[colors[route.id], colors[route.id]]
    #             ), line=dict(
    #                 width=5,
    #                 color=colors[route.id]
    #             ), showlegend=True,
    #             name='Route %s' % route.name))

    max_tt, min_tt = (max(max(max(sc.theta))), min(min(min(sc.theta))))
    lo = alter_layout(dict(
        height=(max_tt - min_tt)*70,
        yaxis=dict(
            zeroline=False,
            showgrid=False,
            tickvals=range(0, max_tt+1),
            ticktext=map(str, range(0, max_tt+1)),
            showticklabels=True,
            # autorange=False,
            range=[0, max_tt + 1],
            title="Travel time(minutes)"),
        xaxis=dict(showgrid=True,
                   # autotick=False,
                   dtick=10,
                   showticklabels=True,
                   range=[-1, (sc.plan_horizon+1) if not max_time else max_time],
                   autorange=False,
                   title='Time(minutes)'),
        annotations=Annotations([
            Annotation(
                x=0.5,
                y=0,
                showarrow=False,
                text=sc.name,
                align='center',
                xref='paper',
                yref='paper',
                font=dict(
                    family='SF Mono',
                    size=11,
                    color='rgba(0,0,0,.2)'))])))

    if len(traces) == 1:
        traces.append(Scatter(
            x=[-100],
            y=[0],
            line=dict(shape='hv'),
            showlegend=False))

    return Figure(data=traces, layout=alter_layout(dict()))
    # else:
    #     return (traces,
    #             zip([-y-offset for y in range(len(sc.routes))],
    #                 [r.name for r in sc.routes]))