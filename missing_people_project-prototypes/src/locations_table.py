import pandas as pd
import dash
from dash import html, dcc
import plotly.express as px
from collections import Counter
from datetime import datetime, timedelta


def create_summ_mp_missing_from_found_locations_table(df):
    """Create a compact table of missing person locations in details format"""
    if df.empty:
        return html.Details([
            html.Summary([
                html.Span("Missing From → Traced To (No data)", 
                         style={'fontSize': '20px', 'fontWeight': '600', 'color': '#2E86AB'})
            ], style={
                'cursor': 'pointer', 
                'padding': '10px', 
                'backgroundColor': '#f8f9fa', 
                'border': '1px solid #dee2e6', 
                'borderRadius': '4px'
            }),
            html.Div([
                html.P("No location data available", 
                      style={'color': '#6c757d', 'fontStyle': 'italic', 'textAlign': 'center', 'padding': '20px'})
            ], style={'padding': '10px'})
        ], open=False)
    
    # Count summary stats
    total_reports = len(df)
    traced_count = len(df[df['tl_address'].notna() & 
                         (df['tl_address'] != 'Not traced') & 
                         (df['tl_address'] != '') & 
                         (df['tl_address'] != 'None')])
    
    # Create compact table header
    table_header = html.Thead([
        html.Tr([
            html.Th("Missing From", style={'fontSize': '12px', 'fontWeight': '600', 'color': '#374151', 'padding': '8px', 'backgroundColor': '#f8f9fa', 'border': '1px solid #dee2e6'}),
            html.Th("→", style={'fontSize': '12px', 'textAlign': 'center', 'padding': '8px', 'backgroundColor': '#f8f9fa', 'border': '1px solid #dee2e6', 'width': '30px'}),
            html.Th("Traced To", style={'fontSize': '12px', 'fontWeight': '600', 'color': '#374151', 'padding': '8px', 'backgroundColor': '#f8f9fa', 'border': '1px solid #dee2e6'}),
            html.Th("Date", style={'fontSize': '12px', 'fontWeight': '600', 'color': '#374151', 'padding': '8px', 'backgroundColor': '#f8f9fa', 'border': '1px solid #dee2e6', 'width': '100px'}),
            html.Th("Report", style={'fontSize': '12px', 'fontWeight': '600', 'color': '#374151', 'padding': '8px', 'backgroundColor': '#f8f9fa', 'border': '1px solid #dee2e6', 'width': '80px'})
        ])
    ])
    
    # Define colors for different location types
    location_colors = {
        'home': '#10b981',      # green
        'school': '#3b82f5',    # blue
        'friend': '#f59e0b',    # orange
        'friends': '#f59e0b',   # orange
        'park': '#8b5cf6',      # purple
        'mall': '#ef4444',      # red
        'street': '#06b6d4',    # cyan
        'workplace': '#84cc16', # lime
        'work': '#84cc16',      # lime
        'store': '#f97316',     # orange-red
        'restaurant': '#ec4899', # pink
        'library': '#6366f1',   # indigo
        'hospital': '#dc2626',  # dark red
        'nhs': '#dc2626',        # dark red
        'default': '#6b7280'    # gray
    }
    
    # Function to get color based on location type
    def get_location_color(location_name):
        if not location_name or location_name == 'Unknown':
            return location_colors['default']
        
        location_lower = location_name.lower()
        for key, color in location_colors.items():
            if key in location_lower:
                return color
        return location_colors['default']

    # Create compact table rows
    table_rows = []
    for _, row in df.iterrows():
        missing_from = row.get('missing_from', 'Unknown')
        mf_address = row.get('mf_address', 'Address not specified')
        tl_address = row.get('tl_address', 'Unknown')
        
        # Handle date parsing more safely
        date_reported = row.get('date_reported_missing', 'Unknown')
        try:
            if date_reported != 'Unknown' and pd.notna(date_reported):
                if isinstance(date_reported, str):
                    date_obj = datetime.fromisoformat(date_reported)
                else:
                    date_obj = pd.to_datetime(date_reported)
                date_reported = date_obj.strftime("%m/%d/%y")
            else:
                date_reported = "Unknown"
        except (ValueError, TypeError):
            date_reported = "Invalid"
        
        report_id = row.get('reportid', 'Unknown')
        
        # Get color for this location type
        location_color = get_location_color(missing_from)
        
        # Compact location display with color coding
        missing_location = html.Div([
            html.Div([
                html.Span("●", style={'color': location_color, 'fontSize': '16px', 'marginRight': '6px'}),
                html.Strong(missing_from, style={'fontSize': '13px', 'color': '#1f2937'})
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '2px'}),
            html.Span(mf_address, style={'fontSize': '11px', 'color': '#6b7280', 'lineHeight': '1.2', 'marginLeft': '22px'})
        ])
        
        # Handle traced location with better logic
        is_traced = tl_address and tl_address not in ['Not traced', 'nan', '', 'None'] and pd.notna(tl_address)
        traced_location = html.Div([
            html.Strong(
                tl_address if is_traced else "Not traced",
                style={
                    'fontSize': '13px', 
                    'color': '#50a14f' if is_traced else '#4b5361',
                    'fontWeight': '500'
                }
            )
        ])
        
        table_row = html.Tr([
            html.Td(missing_location, style={'padding': '8px', 'border': '1px solid #e5e7eb', 'verticalAlign': 'top'}),
            html.Td("→", style={'padding': '8px', 'border': '1px solid #e5e7eb', 'textAlign': 'center', 'color': '#6b7280'}),
            html.Td(traced_location, style={'padding': '8px', 'border': '1px solid #e5e7eb', 'verticalAlign': 'top'}),
            html.Td(
                html.Span(date_reported, style={'fontSize': '12px', 'color': '#4b5563'}),
                style={'padding': '8px', 'border': '1px solid #e5e7eb', 'textAlign': 'center'}
            ),
            html.Td([
                dcc.Link(
                    f"#{report_id}",
                    href=f"/report/mp/{report_id}",
                    style={'fontSize': '12px', 'fontWeight': '600', 'color': '#2563eb', 'textDecoration': 'none'}
                )
            ], style={'padding': '8px', 'border': '1px solid #e5e7eb', 'textAlign': 'center'})
        ], style={'backgroundColor': 'white'})
        
        table_rows.append(table_row)
    
    table_body = html.Tbody(table_rows)
    
    return html.Details([
        html.Summary([
            html.Span(f"📍 Table: Missing From → Traced To", 
                     style={'fontSize': '20px', 'fontWeight': '600', 'color': '#2664eb'})
        ], style={
            'cursor': 'pointer', 
            'padding': '10px', 
            'backgroundColor': '#f8f9fa', 
            'border': '1px solid #dee2e6', 
            'borderRadius': '4px'
        }),
        html.Div([
            # Summary stats
            html.Div([
                html.Div([
                    html.Span(f"Total Reports: {total_reports}", 
                             style={'fontSize': '12px', 'color': '#6c757d', 'marginRight': '20px'}),
                    html.Span(f"Successfully Traced: {traced_count} ({round(traced_count/total_reports*100 if total_reports > 0 else 0, 1)}%)", 
                             style={'fontSize': '12px', 'color': '#6c757d'})
                ], style={'marginBottom': '15px', 'padding': '8px', 'backgroundColor': '#f8f9fa', 'borderRadius': '4px'}),
                
                # Compact table
                html.Div([
                    html.Table([table_header, table_body], 
                              style={
                                  'width': '100%', 
                                  'borderCollapse': 'collapse',
                                  'fontSize': '13px',
                                  'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
                              })
                ], style={'overflowX': 'auto', 'maxHeight': '1000px', 'overflowY': 'auto'})
            ])
        ], style={'padding': '10px'})
    ], open=False)


# Helper function to integrate into sections list
def create_locations_table_section(df):
    """
    Create locations table section that can be appended to sections list
    """
    return create_summ_mp_missing_from_found_locations_table(df)


# Example usage function
def create_location_table_dashboard(csv_file_path):
    """
    Create location table dashboard from CSV file
    """
    try:
        df = pd.read_csv(csv_file_path)
        return create_summ_mp_missing_from_found_locations_table(df)
    except Exception as e:
        return html.Details([
            html.Summary([
                html.Span("Missing From → Traced To (Error loading data)", 
                         style={'fontSize': '20px', 'fontWeight': '600', 'color': '#dc3545'})
            ], style={
                'cursor': 'pointer', 
                'padding': '10px', 
                'backgroundColor': '#f8f9fa', 
                'border': '1px solid #dee2e6', 
                'borderRadius': '4px'
            }),
            html.Div([
                html.P(f"Error loading data: {str(e)}", 
                      style={'color': '#dc3545', 'fontStyle': 'italic', 'textAlign': 'center', 'padding': '20px'})
            ], style={'padding': '10px'})
        ], open=False)


# CSS styles that should be added to your app
LOCATION_TABLE_CSS = """
/* Compact details styling */
details > summary {
    list-style: none;
}
details > summary::-webkit-details-marker {
    display: none;
}
details > summary::after {
    content: "▼";
    font-size: 12px;
    color: #6b7280;
    float: right;
    transform: rotate(-90deg);
    transition: transform 0.2s ease;
}
details[open] > summary::after {
    transform: rotate(0deg);
}
details > summary:hover {
    background-color: #e9ecef !important;
}

/* Table hover effects */
tbody tr:hover {
    background-color: #f8f9fa !important;
}

/* Link hover effects */
a:hover {
    text-decoration: underline !important;
}
"""