import plotly.graph_objects as go
import plotly.express as px
from dash import html, dcc, callback, Input, Output, State
import pandas as pd
import numpy as np
import networkx as nx
from collections import defaultdict, Counter
import json
import math
from utils.date_from_report_id import date_from_reportid


def create_association_network_graph(overview, df, config=None):
    """
    Creates an interactive network graph visualization from relationship data.
    
    Args:
        df: DataFrame with relationship data. Expected columns:
            - 'source' or 'from': Source node identifier
            - 'target' or 'to': Target node identifier
            - 'relationship' or 'edge_type': Type of relationship (optional)
            - 'weight' or 'strength': Relationship strength (optional, defaults to 1)
            - 'source_type': Type/category of source node (optional)
            - 'target_type': Type/category of target node (optional)
            - 'source_label': Display label for source (optional, uses source if not provided)
            - 'target_label': Display label for target (optional, uses target if not provided)
            - Additional columns will be included in hover information
        
        config: Dictionary with visualization options:
            - 'layout': 'spring', 'circular', 'kamada_kawai', 'random' (default: 'spring')
            - 'node_size_column': Column name to use for node sizing (optional)
            - 'color_by': 'type', 'degree', 'community' (default: 'type')
            - 'show_labels': Boolean, whether to show node labels (default: True)
            - 'edge_color_by': 'type', 'weight' (default: 'type')
            - 'filter_min_degree': Minimum node degree to include (default: 1)
    
    Returns:
        html.Details component containing the network graph and statistics
    
    File Format Examples:
    
    1. Basic CSV format:
       source,target,relationship
       person1,person2,knows
       person1,location1,visited
       person2,organization1,works_for
    
    2. Enhanced CSV format:
       source,target,relationship,weight,source_type,target_type,source_label,target_label
       P001,P002,family_member,5,person,person,John Doe,Jane Doe
       P001,L001,residence,3,person,location,John Doe,123 Main St
       P002,O001,employment,4,person,organization,Jane Doe,ABC Corp
    
    3. JSON format:
       [
         {"source": "P001", "target": "P002", "relationship": "family", "weight": 5},
         {"source": "P001", "target": "L001", "relationship": "residence", "weight": 3}
       ]
    """
    
    # Default configuration
    default_config = {
        'layout': 'spring',
        'node_size_column': None,
        'color_by': 'type',
        'show_labels': True,
        'edge_color_by': 'type',
        'filter_min_degree': 1,
        'node_size_range': [80, 140],  # Slightly smaller nodes to reduce overlap
        'edge_width_range': [2, 6]     # Thinner edges
    }
    
    if config:
        default_config.update(config)
    config = default_config
    
    # Standardize column names
    df = df.copy()
    
    # Map various possible column names to standard names
    column_mapping = {
        'from': 'source',
        'to': 'target',
        'edge_type': 'relationship',
        'strength': 'weight',
        'relation': 'relationship',
        'rel_type': 'relationship'
    }
    
    for old_name, new_name in column_mapping.items():
        if old_name in df.columns and new_name not in df.columns:
            df[new_name] = df[old_name]
    
    # Check required columns
    if 'source' not in df.columns or 'target' not in df.columns:
        return html.Details([
            html.Summary([
                html.Div([
                    html.H2("Network Graph", className="locations-main-title"),
                    html.Span("Invalid data format", className="item-count-prominent"),
                    html.Span("▼", className="dropdown-arrow")
                ], className="locations-section-header-prominent")
            ], className="locations-summary-prominent"),
            html.Div([
                html.P("Required columns 'source' and 'target' not found in the data.", 
                      style={'color': '#d63384', 'fontWeight': '600', 'textAlign': 'center', 'padding': '20px'})
            ], className="locations-dropdown-content")
        ], className="locations-section-prominent", open=True)
    
    # Fill missing optional columns
    if 'relationship' not in df.columns:
        df['relationship'] = 'connected'
    if 'weight' not in df.columns:
        df['weight'] = 1
    if 'source_type' not in df.columns:
        df['source_type'] = 'unknown'
    if 'target_type' not in df.columns:
        df['target_type'] = 'unknown'
    if 'source_label' not in df.columns:
        df['source_label'] = df['source']
    if 'target_label' not in df.columns:
        df['target_label'] = df['target']
    if 'reportid' not in df.columns:
        df['reportid'] = 'N/A'
    
    # Clean data
    df = df.dropna(subset=['source', 'target'])
    df = df[df['source'] != df['target']]  # Remove self-loops
    
    if len(df) == 0:
        return html.Details([
            html.Summary([
                html.Div([
                    html.H2("Network Graph", className="locations-main-title"),
                    html.Span("No valid relationships found", className="item-count-prominent"),
                    html.Span("▼", className="dropdown-arrow")
                ], className="locations-section-header-prominent")
            ], className="locations-summary-prominent"),
            html.Div([
                html.P("No valid relationship data found after cleaning.", 
                      style={'color': '#d63384', 'fontWeight': '600', 'textAlign': 'center', 'padding': '20px'})
            ], className="locations-dropdown-content")
        ], className="locations-section-prominent", open=True)
    
    # Create NetworkX graph
    G = nx.Graph()
    
    # Create a mapping for report IDs per edge
    edge_reportids = {}
    
    # Add edges with attributes
    for _, row in df.iterrows():
        edge_key = (row['source'], row['target'])
        G.add_edge(
            row['source'], 
            row['target'],
            relationship=row['relationship'],
            weight=row['weight'],
            source_label=row['source_label'],
            target_label=row['target_label'],
            reportid=row['reportid']
        )
        edge_reportids[edge_key] = row['reportid']
    
    # Add node attributes
    node_types = {}
    node_labels = {}
    node_reportids = {}
    
    for _, row in df.iterrows():
        if row['source'] not in node_types:
            node_types[row['source']] = row['source_type']
            node_labels[row['source']] = row['source_label']
            node_reportids[row['source']] = row['reportid']
        if row['target'] not in node_types:
            node_types[row['target']] = row['target_type']
            node_labels[row['target']] = row['target_label']
            node_reportids[row['target']] = row['reportid']
    
    nx.set_node_attributes(G, node_types, 'type')
    nx.set_node_attributes(G, node_labels, 'label')
    nx.set_node_attributes(G, node_reportids, 'reportid')
    
    # Filter nodes by minimum degree if specified
    if config['filter_min_degree'] > 1:
        nodes_to_remove = [node for node, degree in G.degree() if degree < config['filter_min_degree']]
        G.remove_nodes_from(nodes_to_remove)
    
    if len(G.nodes()) == 0:
        return html.Details([
            html.Summary([
                html.Div([
                    html.H2("Network Graph", className="locations-main-title"),
                    html.Span("No nodes after filtering", className="item-count-prominent"),
                    html.Span("▼", className="dropdown-arrow")
                ], className="locations-section-header-prominent")
            ], className="locations-summary-prominent"),
            html.Div([
                html.P("No nodes remain after applying minimum degree filter.", 
                      style={'color': '#d63384', 'fontWeight': '600', 'textAlign': 'center', 'padding': '20px'})
            ], className="locations-dropdown-content")
        ], className="locations-section-prominent", open=True)
    
    # Calculate layout positions with improved spacing parameters
    num_nodes = len(G.nodes())
    
    if config['layout'] == 'spring':
        # Improved spring layout with better spacing
        # k controls the optimal distance between nodes
        k = max(5, num_nodes * 0.5)  # Adaptive spacing based on number of nodes
        pos = nx.spring_layout(
            G, 
            k=k,                    # Optimal distance between nodes
            iterations=200,         # More iterations for better convergence
            seed=42,
            scale=3.0              # Larger scale for more spread
        )
    elif config['layout'] == 'circular':
        pos = nx.circular_layout(G, scale=3.5)  # Increased scale
    elif config['layout'] == 'kamada_kawai':
        try:
            pos = nx.kamada_kawai_layout(G, scale=3.0)
        except:
            # Fallback to spring if kamada_kawai fails
            pos = nx.spring_layout(G, k=5, iterations=200, seed=42, scale=3.0)
    else:  # random
        pos = nx.random_layout(G, seed=42)
        # Scale up random positions
        pos = {node: (coord[0] * 4, coord[1] * 4) for node, coord in pos.items()}
    
    # Post-process positions to reduce overlaps using force-directed adjustment
    pos = adjust_positions_for_overlap(pos, G, min_distance=0.3)
    
    # Calculate node metrics
    degree_centrality = nx.degree_centrality(G)
    betweenness_centrality = nx.betweenness_centrality(G)
    
    # Detect communities
    try:
        communities = nx.community.greedy_modularity_communities(G)
        community_map = {}
        for i, community in enumerate(communities):
            for node in community:
                community_map[node] = i
    except:
        community_map = {node: 0 for node in G.nodes()}
    
    # Prepare node data
    node_x = []
    node_y = []
    node_text = []
    node_info = []
    node_colors = []
    node_sizes = []
    
    # Enhanced color schemes for better visuals
    type_colors = {
        'person': '#3498DB',           # Professional blue
        'police_officer': '#E74C3C',   # Alert red
        'medical_professional': '#2ECC71', # Medical green
        'witness': '#F39C12',          # Warning orange
        'organization': '#9B59B6',     # Corporate purple
        'location': '#1ABC9C',         # Location teal
        'unknown': '#95A5A6'           # Neutral gray
    }
    
    degree_colors = px.colors.sequential.Plasma
    community_colors = px.colors.qualitative.Set3
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        
        # Node label with improved line breaks
        label = G.nodes[node].get('label', node)
        # Intelligent label splitting for better readability
        if len(label) > 20:
            words = label.split()
            if len(words) > 1:
                # Split at roughly the middle word
                mid = len(words) // 2
                label = ' '.join(words[:mid]) + '<br>' + ' '.join(words[mid:])
            else:
                # Split long single words
                mid = len(label) // 2
                label = label[:mid] + '<br>' + label[mid:]
        elif len(label) > 12 and ' ' in label:
            # Split shorter labels with spaces
            words = label.split()
            if len(words) >= 2:
                mid = len(words) // 2
                label = ' '.join(words[:mid]) + '<br>' + ' '.join(words[mid:])
        
        node_text.append(label if config['show_labels'] else '')
        
        # Node hover info
        degree = G.degree(node)
        node_type = G.nodes[node].get('type', 'unknown')
        node_reportid = G.nodes[node].get('reportid', 'N/A')
        
        # Handle multiple report IDs
        if isinstance(node_reportid, str) and ',' in node_reportid:
            reportid_display = f"Report IDs: {node_reportid}"
        else:
            reportid_display = f"Report ID: {node_reportid}"
        
        neighbors = list(G.neighbors(node))
        neighbor_labels = [G.nodes[n].get('label', n) for n in neighbors[:5]]
        neighbor_text = ", ".join(neighbor_labels)
        if len(neighbors) > 5:
            neighbor_text += f" (and {len(neighbors) - 5} more)"
        
        info = f"<b>{G.nodes[node].get('label', node)}</b><br>"
        info += f"ID: {node}<br>"
        info += f"Type: {node_type}<br>"
        info += f"{reportid_display}<br>"
        info += f"Connections: {degree}<br>"
        info += f"Connected to: {neighbor_text}"
        node_info.append(info)
        
        # Node color
        if config['color_by'] == 'type':
            node_type = G.nodes[node].get('type', 'unknown')
            node_colors.append(type_colors.get(node_type, type_colors['unknown']))
        elif config['color_by'] == 'degree':
            max_degree = max(dict(G.degree()).values())
            color_idx = int((degree / max_degree) * (len(degree_colors) - 1))
            node_colors.append(degree_colors[color_idx])
        else:  # community
            comm_idx = community_map.get(node, 0) % len(community_colors)
            node_colors.append(community_colors[comm_idx])
        
        # Node size
        if config['node_size_column'] and config['node_size_column'] in df.columns:
            # Use specified column for sizing (would need additional logic)
            size = config['node_size_range'][0] + (degree / max(dict(G.degree()).values())) * (config['node_size_range'][1] - config['node_size_range'][0])
        else:
            # Size by degree
            max_degree = max(dict(G.degree()).values()) if G.nodes() else 1
            size = config['node_size_range'][0] + (degree / max_degree) * (config['node_size_range'][1] - config['node_size_range'][0])
        node_sizes.append(size)
    
    # Prepare edge data for lines and labels
    edge_x = []
    edge_y = []
    edge_info = []
    edge_colors = []
    edge_widths = []
    edge_labels_x = []
    edge_labels_y = []
    edge_labels_text = []
    edge_labels_hover = []
    
    relationship_colors = {
        'family': '#FF6B6B',
        'family_member': '#FF6B6B',
        'friend': '#4ECDC4',
        'colleague': '#45B7D1',
        'neighbor': '#96CEB4',
        'business': '#FFEAA7',
        'knows': '#DDA0DD',
        'connected': '#A8A8A8',
        'contacted': '#9B59B6',
        'works_for': '#FFB347',
        'lives_at': '#98D8C8',
        'visited': '#F7DC6F',
        'police_interaction': '#3498DB',
        'medical_care': '#E74C3C',
        'sighting': '#F39C12'
    }
    
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        
        # Calculate midpoint for edge label with slight offset to avoid overlap
        mid_x = (x0 + x1) / 2
        mid_y = (y0 + y1) / 2
        
        # Add slight random offset to edge labels to reduce overlap
        offset = 0.1
        mid_x += np.random.uniform(-offset, offset)
        mid_y += np.random.uniform(-offset, offset)
        
        edge_labels_x.append(mid_x)
        edge_labels_y.append(mid_y)
        
        # Edge info and label
        edge_data = G.edges[edge]
        relationship = edge_data.get('relationship', 'connected')
        weight = edge_data.get('weight', 1)
        source_label = edge_data.get('source_label', edge[0])
        target_label = edge_data.get('target_label', edge[1])
        edge_reportid = edge_data.get('reportid', 'N/A')
        
        # Handle multiple report IDs for edges
        if isinstance(edge_reportid, str) and ',' in edge_reportid:
            reportid_display = f"Report IDs: {edge_reportid}"
        else:
            reportid_display = f"Report ID: {edge_reportid}"
        
        # Shortened relationship text for display
        relationship_display = relationship.replace('_', '\n').title()
        edge_labels_text.append(relationship_display)
        
        info = f"{source_label} ↔ {target_label}<br>Relationship: {relationship}<br>Weight: {weight}<br>{reportid_display}"
        edge_info.append(info)
        edge_labels_hover.append(info)
        
        # Edge color
        if config['edge_color_by'] == 'weight':
            max_weight = max([G.edges[e].get('weight', 1) for e in G.edges()])
            color_intensity = weight / max_weight
            edge_colors.append(f'rgba(100, 100, 100, {0.2 + 0.6 * color_intensity})')
        else:  # by type
            color = relationship_colors.get(relationship, '#A8A8A8')
            # Make edges slightly transparent to reduce visual clutter
            if color.startswith('#'):
                # Convert hex to rgba with transparency
                color = f'rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.7)'
            edge_colors.append(color)
        
        # Edge width
        max_weight = max([G.edges[e].get('weight', 1) for e in G.edges()])
        width = config['edge_width_range'][0] + (weight / max_weight) * (config['edge_width_range'][1] - config['edge_width_range'][0])
        edge_widths.append(width)
    
    # Create the plot
    fig = go.Figure()
    
    # Add edges with improved styling
    for i in range(0, len(edge_x), 3):
        if i + 1 < len(edge_x):
            fig.add_trace(go.Scatter(
                x=edge_x[i:i+2],
                y=edge_y[i:i+2],
                mode='lines',
                line=dict(width=edge_widths[i//3], color=edge_colors[i//3]),
                hoverinfo='skip',
                showlegend=False
            ))
    
    # Add edge labels with improved styling and reduced size
    fig.add_trace(go.Scatter(
        x=edge_labels_x,
        y=edge_labels_y,
        mode='text',
        text=edge_labels_text,
        textfont=dict(size=15, color='#34495e', family='Inter'),
        textposition="middle center",
        hovertemplate='%{hovertext}<extra></extra>',
        hovertext=edge_labels_hover,
        showlegend=False,
        name='Relationships',
        opacity=1  # Slightly transparent to reduce visual clutter
    ))
    
    # Add nodes with improved styling
    fig.add_trace(go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers+text' if config['show_labels'] else 'markers',
        marker=dict(
            size=node_sizes,
            color=node_colors,
            line=dict(width=3, color='white'),  # Thinner border
            sizemode='diameter',
            opacity=0.95
        ),
        text=node_text,
        textposition="middle center",
        textfont=dict(size=12, color='white', family='Inter, system-ui, -apple-system, sans-serif'),
        hovertemplate='%{hovertext}<extra></extra>',
        hovertext=node_info,
        name='Network Nodes',
        customdata=[{'node_id': node, 'neighbors': list(G.neighbors(node))} for node in G.nodes()]
    ))
    
    # Update layout with enhanced styling and better spacing
    fig.update_layout(
        title=dict(
            text="Association Network Graph",
            x=0.5,
            font=dict(size=22, color='#2E86AB', family='Inter, system-ui, -apple-system, sans-serif')
        ),
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20, l=20, r=20, t=50),  # Increased margins
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='#fafafa',
        paper_bgcolor='white',
        height=900,  # Increased height for better spacing
        autosize=True,
        dragmode='pan'
    )
    
    # Generate unique ID for this graph
    import uuid
    graph_id = f"network-graph-{str(uuid.uuid4())[:8]}"
    
    # Create the graph component with enhanced interactivity
    graph_component = dcc.Graph(
        id=graph_id,
        figure=fig,
        style={'width': '100%', 'height': '900px'},
        config={
            'displayModeBar': True, 
            'displaylogo': False,
            'modeBarButtonsToAdd': ['pan2d', 'select2d', 'lasso2d', 'resetScale2d'],
            'modeBarButtonsToRemove': ['autoScale2d'],
            'scrollZoom': True,
            'doubleClick': 'reset'
        }
    )
    
    # Calculate network statistics
    num_nodes = len(G.nodes())
    num_edges = len(G.edges())
    density = nx.density(G)
    
    # Most connected nodes
    top_nodes = sorted(G.degree(), key=lambda x: x[1], reverse=True)[:5]
    top_nodes_text = []
    for node, degree in top_nodes:
        label = G.nodes[node].get('label', node)
        top_nodes_text.append(f"{label} ({degree} connections)")
    
    # Relationship type distribution
    relationship_counts = Counter([G.edges[edge].get('relationship', 'connected') for edge in G.edges()])
    
    # Create statistics summary - Compact version
    stats_component = html.Div([
        html.Div([
            html.Div([
                html.Strong("No. People: ", style={'fontFamily': 'Inter, system-ui, -apple-system, sans-serif'}), 
                html.Span(f"{num_nodes}", style={'fontFamily': 'Inter, system-ui, -apple-system, sans-serif'}),
                html.Strong("    No. Relations: ", style={'fontFamily': 'Inter, system-ui, -apple-system, sans-serif'}), 
                html.Span(f"{num_edges}", style={'fontFamily': 'Inter, system-ui, -apple-system, sans-serif'}),
            ], style={'marginBottom': '8px', 'fontSize': '15px'}),
        ])
    ], style={
        'backgroundColor': '#f8f9fa',
        'padding': '12px 16px',
        'border': '1px solid #e9ecef',
        'borderRadius': '8px',
        'marginTop': '12px',
        'fontFamily': 'Inter, system-ui, -apple-system, sans-serif'
    })
    
    
    # Create the main content
    main_content = html.Div([
        graph_component,
        stats_component
    ], style={
        'backgroundColor': 'white',
        'border': '1px solid #ddd',
        'borderRadius': '8px',
        'padding': '15px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
        'width': '100%',
        'maxWidth': 'none'
    })
    print("BYYYYY", df['reportid'].drop_duplicates().to_list())
    return html.Div([
        html.Details([
            html.Summary([
                html.Div([
                    html.H2("🤖"),
                    html.H2("People & Relations", className="locations-main-title"),
                    html.Span(
                        f"{num_nodes} entities, {num_edges} relationships", 
                        className="item-count-prominent"
                    ),
                    html.Span("▼", className="dropdown-arrow")
                ], className="locations-section-header-prominent")
            ], className="locations-summary-prominent"),
            html.Div([overview, main_content], className="locations-dropdown-content"),
            
    
            html.Div([
                date_from_reportid(x, "mp")
    # dcc.Link(
    #     x,
    #     href=f"/report/mp/{x}",
    #     className="report-link-prominent"
    # )
    for item in df['reportid'].drop_duplicates().to_list()
    for x in str(item).split(',')
])
                
                
                
        ], className="locations-section-prominent", open=True)
    ], style={'width': '100%', 'maxWidth': 'none', 'margin': '0'})


def adjust_positions_for_overlap(pos, G, min_distance=0.3):
    """
    Adjust node positions to minimize overlaps using a simple force-directed approach.
    
    Args:
        pos: Dictionary of node positions
        G: NetworkX graph
        min_distance: Minimum distance between nodes
    
    Returns:
        Dictionary of adjusted positions
    """
    adjusted_pos = pos.copy()
    nodes = list(G.nodes())
    
    # Simple overlap reduction algorithm
    for iteration in range(50):  # Limited iterations to prevent infinite loops
        moved = False
        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes[i+1:], i+1):
                x1, y1 = adjusted_pos[node1]
                x2, y2 = adjusted_pos[node2]
                
                # Calculate distance between nodes
                dx = x2 - x1
                dy = y2 - y1
                distance = math.sqrt(dx*dx + dy*dy)
                
                # If nodes are too close, push them apart
                if distance < min_distance and distance > 0:
                    # Calculate repulsion force
                    force = (min_distance - distance) / distance
                    push_x = dx * force * 0.1
                    push_y = dy * force * 0.1
                    
                    # Move nodes apart
                    adjusted_pos[node1] = (x1 - push_x, y1 - push_y)
                    adjusted_pos[node2] = (x2 + push_x, y2 + push_y)
                    moved = True
        
        if not moved:
            break
    
    return adjusted_pos
