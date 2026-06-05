# Working with technology tree
import math

# graph structures
import networkx as nx

def make_graph( product_table, node_table, link_table ):
    G = nx.DiGraph()

    for p in product_table:
        G.add_node( "p" + str(p.id), label = p.full_name, pk = p.id, type = 'product' )

    for n in node_table:
        G.add_node( "n" + str(n.id ), label = n.full_name, pk = p.id, type = 'node' )

    for l in link_table:
        p_id = "p" + str(l.product_id )
        n_id = "n" + str(l.node_type_id )
        if l.out_flag:
            G.add_edge( n_id , p_id )
        else:
            G.add_edge( p_id , n_id )

    return G

# node positions on canvas
def circular_pos(G, radius=1.0):
    nodes = list(G.nodes())
    n = len(nodes)
    if n == 0:
        return {}
    pos = {}
    for i, node in enumerate(nodes):
        angle = 2 * math.pi * i / n
        pos[node] = (radius * math.cos(angle), radius * math.sin(angle))
    return pos

# Plotly layout
def graph_to_plotly_data(G):
    pos = circular_pos(G, radius=1.0)

    edge_x = []
    edge_y = []
    annotations = []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        # main line (without arrowhead)
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        # add arrow annotation pointing from u to v
        annotations.append({
            "x": x1, "y": y1,
            "ax": x0, "ay": y0,
            "xref": "x", "yref": "y",
            "axref": "x", "ayref": "y",
            "showarrow": True,
            "arrowhead": 3,
            "arrowsize": 2,
            "arrowwidth": 1,
            "arrowcolor": "#888",
            "opacity": 0.9
        })

    edge_trace = {
        "x": edge_x, "y": edge_y,
        "mode": "lines",
        "line": {"width": 1, "color": "#888"},
        "hoverinfo": "none",
        "type": "scatter"
    }

    node_x = []
    node_y = []
    labels = []
    for n in G.nodes():
        x, y = pos[n]
        node_x.append(x); node_y.append(y)
        labels.append(str(G.nodes[n].get("label", n)))

    node_trace = {
        "x": node_x, "y": node_y,
        "mode": "markers+text",
        "marker": {"size": 20, "color": "#ff7f0e"},
        "text": labels,
        "textposition": "top center",
        "hoverinfo": "text",
        "type": "scatter"
    }

    layout = {
        "showlegend": False,
        "xaxis": {"visible": False},
        "yaxis": {"visible": False},
        "margin": {"l":0,"r":0,"t":0,"b":0},
        "annotations": annotations
    }

    return {"data": [edge_trace, node_trace], "layout": layout}