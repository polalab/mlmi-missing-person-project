from dash import html, dcc
import plotly.graph_objects as go
import ast
import re


def create_theme_analysis_summary(case_id, mp_ids, vp_ids):
    """
    Creates a bar plot analysis of themes from a text file.
    
    Parameters:
    text_file_path (str): Path to the text file containing theme data
    mp_ids (list): List of MP report IDs
    vp_ids (list): List of VP report IDs
    
    Returns:
    html.Div: Dash component containing the theme analysis
    """
    text_file_path = f"NEW/{case_id}/patterns/custom_llm_pattersllama3.1_list.txt"
    # Combine both ID lists for filtering
    valid_ids = set(mp_ids + vp_ids)
    
    # Read and parse the text file
    themes_data = {}
    
    try:
        with open(text_file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                
                # Parse each line: theme_name, [id1, id2, id3, ...]
                if ',' in line:
                    parts = line.split(',', 1)
                    theme_name = parts[0].strip()
                    
                    # Extract the list part and safely evaluate it
                    list_part = parts[1].strip()
                    try:
                        # Use ast.literal_eval for safe evaluation of the list
                        ids_list = ast.literal_eval(list_part)
                        
                        # Filter IDs to only include those in valid_ids
                        filtered_ids = [id for id in ids_list if id in valid_ids]
                        
                        # Only include themes that have at least one valid ID
                        if filtered_ids:
                            themes_data[theme_name] = filtered_ids
                            
                    except (ValueError, SyntaxError) as e:
                        print(f"Error parsing line: {line}. Error: {e}")
                        continue
                        
    except FileNotFoundError:
        return html.Div([
            html.Div([
                html.I("⚠️", className="icon-medium"),
                html.P(f"File not found: {text_file_path}", className="no-data-compact")
            ], className="entity-section empty-section")
        ])
    
    if not themes_data:
        return html.Div([
            html.Div([
                html.I("⚠️", className="icon-medium"),
                html.P("No valid themes found after filtering", className="no-data-compact")
            ], className="entity-section empty-section")
        ])
    
    # Sort themes by count (descending)
    themes_data = dict(sorted(themes_data.items(), key=lambda item: len(item[1]), reverse=True))
    
    # Calculate total reports for context
    total_reports = len(valid_ids)
    
    # Prepare data for bar plot
    theme_names = []
    counts = []
    proportions = []
    hover_texts = []
    report_ids_lists = []
    
    for theme, report_ids in themes_data.items():
        count = len(report_ids)
        proportion = f"{count}/{total_reports}"
        
        # Create readable theme name (replace underscores with spaces and title case)
        readable_theme = theme.replace('_', ' ').title()
        
        theme_names.append(readable_theme)
        counts.append(count)
        proportions.append(proportion)
        report_ids_lists.append(report_ids)
        
        # Create hover text with theme info and report IDs
        report_ids_text = ", ".join([str(rid) for rid in report_ids[:10]])
        if len(report_ids) > 10:
            report_ids_text += f" (and {len(report_ids) - 10} more)"
        
        hover_text = f"<b>{readable_theme}</b><br>" \
                    f"Count: {proportion}<br>" \
                    f"Report IDs: {report_ids_text}"
        hover_texts.append(hover_text)
    
    # Create the bar plot
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=counts,
        y=theme_names,
        orientation='h',
        marker=dict(
            color='#28a745',  # Green color for themes
            opacity=1,
            line=dict(width=1, color='white')
        ),
        hovertemplate='%{customdata}<extra></extra>',
        customdata=hover_texts,
        name='Themes'
    ))
    
    # Update layout
    fig.update_layout(
        xaxis=dict(
            title="Number of Reports",
            showgrid=False,
            tickangle=45 if len(theme_names) > 25 else 0
        ),
        yaxis=dict(
            title="Themes",
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(0,0,0,0.1)',
            zeroline=True,
            zerolinecolor='rgba(0,0,0,0.2)'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=max(500, len(themes_data) * 35),  # Dynamic height based on number of themes
        margin=dict(l=150, r=40, t=80, b=100),  # More left margin for theme names
        showlegend=False
    )
    
    # Create the graph component
    graph_component = dcc.Graph(
        id='theme-analysis-bar',
        figure=fig,
        style={'width': '100%'},
        config={'displayModeBar': True, 'displaylogo': False}
    )
    
    # Create detailed themes table for reference
    def get_report_type(report_id):
        """Determine if report is MP or VP based on ID lists"""
        if report_id in mp_ids:
            return 'mp'
        elif report_id in vp_ids:
            return 'vp'
        else:
            return 'unknown'
    
    themes_table = html.Div([
        html.Details([
            html.Summary([
                html.Span("Details", style={
                    'fontSize': '14px',
                    'fontWeight': '600',
                    'color': '#2c3e50'
                })
            ], style={
                'cursor': 'pointer',
                'padding': '10px',
                'backgroundColor': '#f8f9fa',
                'border': '1px solid #e9ecef',
                'borderRadius': '4px',
                'marginTop': '15px'
            }),
            html.Div([
                html.Div([
                    html.Div([
                        html.Strong(f"{theme.replace('_', ' ').title()}: "),
                        html.Span(f"{len(report_ids)} reports"),
                        html.Br(),
                        html.Small([
                            "Reports: ",
                            *[
                                html.A(f"{get_report_type(rid)}{str(rid)}", 
                                      href=f"/report/{get_report_type(rid)}/{rid}" if get_report_type(rid) != 'unknown' else f"/report/{rid}", 
                                      style={'color': '#007bff', 'textDecoration': 'underline', 'marginRight': '5px'},
                                      target="_blank") 
                                if i < 100 else None
                                for i, rid in enumerate(report_ids[:100])
                            ],
                            html.Span(f" (and {len(report_ids)-10} more)" if len(report_ids) > 10 else "")
                        ], style={'color': '#6c757d', 'fontSize': '12px'})
                    ], style={
                        'padding': '10px',
                        'margin': '5px 0',
                        'backgroundColor': 'white',
                        'border': '1px solid #e9ecef',
                        'borderRadius': '4px'
                    })
                    for theme, report_ids in themes_data.items()
                ])
            ], style={'padding': '10px'})
        ])
    ])
    
    return html.Div([
        # html.Div([
        #     html.Span(f"{len(themes_data)} themes", className="section-count")
        # ], className="entity-section-header"),
        html.Div([
            graph_component,
            themes_table
        ])
    ], className="entity-section")

