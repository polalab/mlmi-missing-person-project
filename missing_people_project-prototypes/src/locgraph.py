import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dash import html, dcc
import networkx as nx
import numpy as np

def layout_disjoint_components(G, connected_components):
    """
    Layout disjoint components separately to avoid visual confusion.
    """
    pos = {}
    
    # Sort components by size (largest first)
    components = sorted(connected_components, key=len, reverse=True)
    
    # Calculate grid layout for components
    num_components = len(components)
    grid_cols = int(np.ceil(np.sqrt(num_components)))
    grid_rows = int(np.ceil(num_components / grid_cols))
    
    # Space between component centers
    component_spacing = 6
    
    for idx, component in enumerate(components):
        # Calculate grid position for this component
        row = idx // grid_cols
        col = idx % grid_cols
        
        # Calculate center position for this component
        center_x = col * component_spacing
        center_y = row * component_spacing
        
        # Create subgraph for this component
        subgraph = G.subgraph(component)
        
        # Layout this component separately
        try:
            if nx.is_directed_acyclic_graph(subgraph):
                component_pos = nx.nx_agraph.graphviz_layout(subgraph, prog='dot')
            else:
                component_pos = nx.spring_layout(subgraph, 
                                               k=3, 
                                               iterations=100, 
                                               weight='weight',
                                               scale=1.5,
                                               seed=42)
        except:
            component_pos = nx.spring_layout(subgraph, 
                                           k=3, 
                                           iterations=100, 
                                           weight='weight',
                                           scale=1.5,
                                           seed=42)
        
        # Adjust positions to reduce overlaps within component
        component_pos = adjust_positions_to_reduce_overlaps(subgraph, component_pos, min_distance=0.4)
        
        # Translate component to its grid position
        for node in component:
            x, y = component_pos[node]
            pos[node] = (x + center_x, y + center_y)
    
    return pos

def adjust_positions_to_reduce_overlaps(G, pos, min_distance=0.3):
    """
    Adjust node positions to reduce overlaps using a simple force-based approach.
    """
    import copy
    pos_adjusted = copy.deepcopy(pos)
    nodes = list(G.nodes())
    
    # Apply repulsive forces to separate overlapping nodes
    for iteration in range(50):  # Multiple iterations for better separation
        forces = {node: np.array([0.0, 0.0]) for node in nodes}
        
        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes):
                if i >= j:
                    continue
                
                # Calculate distance between nodes
                pos1 = np.array(pos_adjusted[node1])
                pos2 = np.array(pos_adjusted[node2])
                diff = pos1 - pos2
                distance = np.linalg.norm(diff)
                
                # If nodes are too close, apply repulsive force
                if distance < min_distance and distance > 0:
                    # Normalize direction vector
                    direction = diff / distance
                    # Apply force proportional to overlap
                    force_magnitude = (min_distance - distance) * 0.1
                    force = direction * force_magnitude
                    
                    forces[node1] += force
                    forces[node2] -= force
        
        # Apply forces to positions
        for node in nodes:
            pos_adjusted[node] = (
                pos_adjusted[node][0] + forces[node][0],
                pos_adjusted[node][1] + forces[node][1]
            )
    
    return pos_adjusted

def create_network_graph_from_csv(csv_file_path, graph_title="Network Graph"):
    """
    Takes a CSV file with network data and returns a Dash HTML div containing a directed network graph.
    
    Parameters:
    csv_file_path (str): Path to the CSV file
    graph_title (str): Title for the graph
    
    Returns:
    dash.html.Div: HTML div containing the network graph
    
    Expected CSV columns:
    - source: Source node
    - target: Target node  
    - weight: Edge weight (optional)
    - description: Edge description (optional)
    - reports: Report ID (optional)
    - relationship: Relationship type (optional)
    """
    
    # Read CSV file
    try:
        df = pd.read_csv(csv_file_path)
    except FileNotFoundError:
        return html.Div([
            html.H3("Error: CSV file not found"),
            html.P(f"Could not locate file: {csv_file_path}")
        ])
    
    # Validate required columns
    required_columns = ['source', 'target']
    if not all(col in df.columns for col in required_columns):
        return html.Div([
            html.H3("Error: Missing required columns"),
            html.P(f"CSV must contain columns: {required_columns}")
        ])
    
    # Create NetworkX directed graph
    G = nx.DiGraph()
    
    # Add edges with attributes
    for _, row in df.iterrows():
        edge_attrs = {}
        if 'weight' in df.columns:
            edge_attrs['weight'] = row.get('weight', 1)
        if 'description' in df.columns:
            edge_attrs['description'] = row.get('description', '')
        if 'reports' in df.columns:
            edge_attrs['reports'] = row.get('reports', '')
        if 'relationship' in df.columns:
            edge_attrs['relationship'] = row.get('relationship', '')
            
        G.add_edge(row['source'], row['target'], **edge_attrs)
    
    # Find connected components (disjoint subgraphs)
    connected_components = list(nx.connected_components(G.to_undirected()))
    
    # If there's only one component, use the original layout
    if len(connected_components) == 1:
        # Get node positions using improved layout algorithm
        # Try multiple layout algorithms and choose the best one
        try:
            # First try hierarchical layout if the graph has clear hierarchy
            if nx.is_directed_acyclic_graph(G):
                pos = nx.nx_agraph.graphviz_layout(G, prog='dot')
            else:
                # Use spring layout with optimized parameters for minimal overlap
                pos = nx.spring_layout(G, 
                                     k=5,  # Increased from 3 - more space between nodes
                                     iterations=100,  # Increased from 50 - better convergence
                                     weight='weight',  # Use edge weights if available
                                     scale=2,  # Larger scale for more spread
                                     center=(0, 0),
                                     dim=2,
                                     seed=42)  # Fixed seed for reproducible layouts
        except:
            # Fallback to basic spring layout if graphviz is not available
            pos = nx.spring_layout(G, 
                                 k=5, 
                                 iterations=100, 
                                 weight='weight', 
                                 scale=2,
                                 seed=42)
        
        # Post-process positions to reduce overlaps further
        pos = adjust_positions_to_reduce_overlaps(G, pos)
        
    else:
        # Layout disjoint components separately
        pos = layout_disjoint_components(G, connected_components)
    
    # Extract node coordinates
    node_x = [pos[node][0] for node in G.nodes()]
    node_y = [pos[node][1] for node in G.nodes()]
    node_text = list(G.nodes())
    
    # Process node text to make it multiline
    def format_node_text(text):
        """Convert underscores to spaces and split long text into multiple lines"""
        # Replace underscores with spaces
        formatted = text.replace('_', ' ')
        
        # Split long text into multiple lines (wrap at ~12 characters)
        words = formatted.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 <= 12:  # +1 for space
                current_line.append(word)
                current_length += len(word) + 1
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return '<br>'.join(lines)
    
    # Format node text for multiline display
    formatted_node_text = [format_node_text(node) for node in G.nodes()]
    
    # Create node trace
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=formatted_node_text,
        textposition="middle center",
        hoverinfo='text',
        hovertext=[f"Node: {node}<br>Connections: {G.degree(node)}" for node in G.nodes()],
        marker=dict(
            size=50,  # Increased from 20 to 50
            color='lightblue',
            line=dict(width=2, color='darkblue')
        ),
        textfont=dict(size=8, color='black'),  # Slightly smaller text to fit better
        name="Nodes"
    )
    
    # Create curved arrows to reduce visual overlap
    arrow_traces = []
    
    # Group edges by direction to create curved paths for bidirectional connections
    edge_groups = {}
    for edge in G.edges():
        key = tuple(sorted([edge[0], edge[1]]))
        if key not in edge_groups:
            edge_groups[key] = []
        edge_groups[key].append(edge)
    
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        
        # Calculate if this edge needs curvature (bidirectional or multiple edges)
        edge_key = tuple(sorted([edge[0], edge[1]]))
        edges_in_group = edge_groups[edge_key]
        
        # Calculate arrow direction
        dx = x1 - x0
        dy = y1 - y0
        length = np.sqrt(dx**2 + dy**2)
        
        if length > 0:
            # Normalize direction
            dx /= length
            dy /= length
            
            # Add curvature if there are multiple edges between same nodes
            if len(edges_in_group) > 1:
                # Create curved path
                curve_offset = 0.2 if edge == edges_in_group[0] else -0.2
                # Perpendicular vector for curvature
                perp_dx = -dy
                perp_dy = dx
                
                # Calculate midpoint with offset
                mid_x = (x0 + x1) / 2 + curve_offset * perp_dx
                mid_y = (y0 + y1) / 2 + curve_offset * perp_dy
                
                # Adjust start and end points to avoid overlap with larger nodes
                node_radius = 0.08
                start_x = x0 + node_radius * dx
                start_y = y0 + node_radius * dy
                end_x = x1 - node_radius * dx
                end_y = y1 - node_radius * dy
                
                # Create curved arrow using multiple points
                curve_points = 20
                curve_x = []
                curve_y = []
                
                for i in range(curve_points + 1):
                    t = i / curve_points
                    # Quadratic Bezier curve
                    curve_pt_x = (1-t)**2 * start_x + 2*(1-t)*t * mid_x + t**2 * end_x
                    curve_pt_y = (1-t)**2 * start_y + 2*(1-t)*t * mid_y + t**2 * end_y
                    curve_x.append(curve_pt_x)
                    curve_y.append(curve_pt_y)
                
                # Calculate final arrow direction
                final_dx = curve_x[-1] - curve_x[-2]
                final_dy = curve_y[-1] - curve_y[-2]
                final_length = np.sqrt(final_dx**2 + final_dy**2)
                if final_length > 0:
                    final_dx /= final_length
                    final_dy /= final_length
                
                # Create hover text for edge
                edge_data = G[edge[0]][edge[1]]
                hover_text = f"From: {edge[0]}<br>To: {edge[1]}"
                if 'weight' in edge_data:
                    hover_text += f"<br>Weight: {edge_data['weight']}"
                if 'description' in edge_data:
                    hover_text += f"<br>Description: {edge_data['description']}"
                if 'relationship' in edge_data:
                    hover_text += f"<br>Relationship: {edge_data['relationship']}"
                if 'reports' in edge_data:
                    hover_text += f"<br>Report: {edge_data['reports']}"
                
                # Create curved line trace with hover
                curved_line = go.Scatter(
                    x=curve_x,
                    y=curve_y,
                    mode='lines',
                    line=dict(width=2, color='gray'),
                    hoverinfo='text',
                    hovertext=hover_text,
                    hoverlabel=dict(bgcolor="white", bordercolor="black"),
                    showlegend=False
                )
                arrow_traces.append(curved_line)
                
                # Add relationship text along the curved path (at midpoint)
                relationship_text = edge_data.get('relationship', '')
                if relationship_text:
                    # Find midpoint of curve for text placement
                    mid_idx = len(curve_x) // 2
                    text_annotation = dict(
                        x=curve_x[mid_idx],
                        y=curve_y[mid_idx],
                        text=relationship_text.replace('_', ' '),
                        showarrow=False,
                        font=dict(size=8, color='darkred'),
                        bgcolor='rgba(255,255,255,0.8)',
                        bordercolor='darkred',
                        borderwidth=1,
                        xref='x',
                        yref='y'
                    )
                    if 'text_annotations' not in locals():
                        text_annotations = []
                    text_annotations.append(text_annotation)
                
                # Add arrowhead at the end
                arrow_annotation = dict(
                    x=curve_x[-1],
                    y=curve_y[-1],
                    ax=curve_x[-1] - 0.05 * final_dx,
                    ay=curve_y[-1] - 0.05 * final_dy,
                    xref='x',
                    yref='y',
                    axref='x',
                    ayref='y',
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=2,
                    arrowcolor='gray'
                )
                
            else:
                # Straight arrow for single connections
                # Adjust start and end points to avoid overlap with larger nodes
                node_radius = 0.08
                start_x = x0 + node_radius * dx
                start_y = y0 + node_radius * dy
                end_x = x1 - node_radius * dx
                end_y = y1 - node_radius * dy
                
                # Create hover text for edge
                edge_data = G[edge[0]][edge[1]]
                hover_text = f"From: {edge[0]}<br>To: {edge[1]}"
                if 'weight' in edge_data:
                    hover_text += f"<br>Weight: {edge_data['weight']}"
                if 'description' in edge_data:
                    hover_text += f"<br>Description: {edge_data['description']}"
                if 'relationship' in edge_data:
                    hover_text += f"<br>Relationship: {edge_data['relationship']}"
                if 'reports' in edge_data:
                    hover_text += f"<br>Report: {edge_data['reports']}"
                
                # Create straight line trace with hover
                straight_line = go.Scatter(
                    x=[start_x, end_x],
                    y=[start_y, end_y],
                    mode='lines',
                    line=dict(width=2, color='gray'),
                    hoverinfo='text',
                    hovertext=hover_text,
                    hoverlabel=dict(bgcolor="white", bordercolor="black"),
                    showlegend=False
                )
                arrow_traces.append(straight_line)
                
                # Add relationship text along the straight line (at midpoint)
                relationship_text = edge_data.get('relationship', '')
                if relationship_text:
                    # Calculate midpoint for text placement
                    mid_x = (start_x + end_x) / 2
                    mid_y = (start_y + end_y) / 2
                    
                    # Calculate angle for text rotation
                    angle = np.degrees(np.arctan2(dy, dx))
                    # Keep text readable (don't flip upside down)
                    if angle > 90 or angle < -90:
                        angle += 180
                    
                    text_annotation = dict(
                        x=mid_x,
                        y=mid_y,
                        text=relationship_text.replace('_', ' '),
                        showarrow=False,
                        font=dict(size=8, color='darkred'),
                        bgcolor='rgba(255,255,255,0.8)',
                        bordercolor='darkred',
                        borderwidth=1,
                        textangle=angle,
                        xref='x',
                        yref='y'
                    )
                    if 'text_annotations' not in locals():
                        text_annotations = []
                    text_annotations.append(text_annotation)
                
                # Create straight arrow annotation
                arrow_annotation = dict(
                    x=end_x,
                    y=end_y,
                    ax=start_x,
                    ay=start_y,
                    xref='x',
                    yref='y',
                    axref='x',
                    ayref='y',
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=2,
                    arrowcolor='gray'
                )
            
            # Create hover text for edge
            edge_data = G[edge[0]][edge[1]]
            hover_text = f"From: {edge[0]}<br>To: {edge[1]}"
            if 'weight' in edge_data:
                hover_text += f"<br>Weight: {edge_data['weight']}"
            if 'description' in edge_data:
                hover_text += f"<br>Description: {edge_data['description']}"
            if 'relationship' in edge_data:
                hover_text += f"<br>Relationship: {edge_data['relationship']}"
            if 'reports' in edge_data:
                hover_text += f"<br>Report: {edge_data['reports']}"
            
            # Add hover text to annotation - this is no longer needed since we have line traces
            # arrow_annotation['text'] = ''
            # arrow_annotation['hovertext'] = hover_text
            # arrow_annotation['hoverlabel'] = dict(bgcolor="white", bordercolor="black")
            
            # Add to traces
            if 'curved_line' not in locals() or len(edges_in_group) == 1:
                # This is a straight arrow, add it to annotations
                if 'arrow_annotations' not in locals():
                    arrow_annotations = []
                arrow_annotations.append(arrow_annotation)
            else:
                # This was a curved arrow, annotation was already handled above
                if 'arrow_annotations' not in locals():
                    arrow_annotations = []
                arrow_annotations.append(arrow_annotation)
    
    # Ensure arrow_annotations and text_annotations exist
    if 'arrow_annotations' not in locals():
        arrow_annotations = []
    if 'text_annotations' not in locals():
        text_annotations = []
    
    # Create the figure
    fig = go.Figure(data=[node_trace] + arrow_traces,
                   layout=go.Layout(
                       title=graph_title,
                       ##titlefont_size=16,
                       showlegend=True,
                       hovermode='closest',
                       margin=dict(b=20,l=5,r=5,t=40),
                       annotations=arrow_annotations + text_annotations + [dict(
                        #    text=f"Directed Network Graph - {num_components} component{'s' if num_components != 1 else ''} positioned separately",
                           showarrow=False,
                           xref="paper", yref="paper",
                           x=0.005, y=-0.002,
                           xanchor="left", yanchor="bottom",
                           font=dict(color="gray", size=10)
                       )],
                       xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                       yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                       plot_bgcolor='white'
                   ))
    
    # Create summary statistics
    num_nodes = len(G.nodes())
    num_edges = len(G.edges())
    density = nx.density(G)
    num_components = len(connected_components)
    
    # Create component size information
    component_sizes = [len(comp) for comp in connected_components]
    component_info = f"Components: {num_components} | Sizes: {sorted(component_sizes, reverse=True)}"
    
    # Create the HTML div
    network_div = html.Div([
        html.H2(graph_title, style={'textAlign': 'center', 'marginBottom': '20px'}),
        
        # Graph statistics
        html.Div([
            html.H4("Graph Statistics:", style={'marginBottom': '10px'}),
            html.P(f"Nodes: {num_nodes} | Edges: {num_edges} | Density: {density:.3f}"),
            html.P(f"{component_info}"),
            html.P("Each disconnected component is positioned separately for clarity" if num_components > 1 else "All nodes are connected in a single component")
        ], style={'backgroundColor': '#f0f0f0', 'padding': '10px', 'marginBottom': '20px', 'borderRadius': '5px'}),
        
        # The network graph
        dcc.Graph(
            id='network-graph',
            figure=fig,
            style={'height': '600px'}
        ),
        
        # Legend
        html.Div([
            html.H4("Legend:", style={'marginBottom': '10px'}),
            html.P("• Blue circles: Nodes with multiline text (hover for connection count)"),
            html.P("• Gray arrows: Directed relationships (hover for details)"),
            html.P("• Red text: Relationship types displayed on connections"),
            html.P("• Curved arrows used for bidirectional connections"),
            html.P("• Disconnected components are positioned separately in a grid layout")
        ], style={'backgroundColor': '#f9f9f9', 'padding': '10px', 'marginTop': '20px', 'borderRadius': '5px'})
    ])
    
    return network_div

# Example usage:
# if __name__ == "__main__":
#     # This would typically be used in a Dash app
#     network_graph_div = csv_to_network_graph('your_network_data.csv', 'Location Network Graph')
#     
#     # In a Dash app, you would include this div in your layout:
#     # app.layout = html.Div([network_graph_div])