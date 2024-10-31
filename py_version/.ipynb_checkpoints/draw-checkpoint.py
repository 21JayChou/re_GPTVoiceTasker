import numpy as np
from bqplot import Graph, LinearScale, ColorScale, Figure, Tooltip
from ipywidgets import Layout, VBox

fig_layout = Layout(width='600px', height='600px')
node_data = [
    dict(label='A', shape='rect'),
    dict(label='B', shape='ellipse'),
    dict(label='C', shape='ellipse'),
    dict(label='D', shape='rect'),
    dict(label='E', shape='ellipse'),
    dict(label='F', shape='circle'),
    dict(label='G', shape='ellipse'),
]
link_data = [{'source': s, 'target': t} for s, t in np.random.randint(0, 7, (10, 2)) if s != t]
graph = Graph(node_data=node_data, link_data=link_data, charge=-600, colors=['lightblue'] * 7)
graph.link_type = 'arc' # arc, line, slant_line
fig = Figure(marks=[graph], layout=fig_layout)
VBox([fig])