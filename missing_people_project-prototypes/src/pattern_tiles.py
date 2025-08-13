import pandas as pd
import dash
from dash import html, dcc
import plotly.express as px
from collections import Counter
from utils.date_from_report_id import date_from_reportid


def create_pattern_tiles(csv_file_path):
    """
    Read CSV file and create simple pattern behavior tiles
    
    CSV should have columns: report_id, explanation, pattern_name, quote
    """
    
    # Read the CSV file
    df = pd.read_csv(csv_file_path)
    print("<<<<<", df['pattern_name'])
    # Count frequency of each pattern
    pattern_counts = df['pattern_name'].value_counts()
    
    # Define colors for different pattern types
    pattern_colors = {
        'friend_association_pattern': '#3b82f5',
        'refusal_to_disclose_pattern': '#ef4444', 
        'return_own_accord_pattern': '#10b981',
        'arden_area_pattern': '#f59e0b',
        'weekly_pattern': '#8b5cf6',
        'criminal_activity_pattern': '#dc2626',
        'family_contact_pattern': '#06b6d4',
        'default': '#6b7280'
    }
    
    # Create tiles for each pattern type
    tiles = []
    
    for pattern_name, count in pattern_counts.items():
        # Get incidents for this pattern
        incidents = df[df['pattern_name'] == pattern_name]
        
        # Get sample incidents with quotes
        sample_incidents = incidents.head(3)
        
        # Get color for this pattern
        color = pattern_colors.get(pattern_name, pattern_colors['default'])
        
        # Create incident list with quotes and links
        incident_divs = []
        for _, row in sample_incidents.iterrows():
            quote_text = row['quote'] if pd.notna(row['quote']) else 'No quote available'
            explanation_text = row['explanation'] if pd.notna(row['explanation']) else 'No explanation available'
            
            incident_divs.append(
                html.Div([
                    date_from_reportid(row['report_id'], "mp"),

                    # dcc.Link(f"#{row['report_id']}", 
                    #        href=f"/report/mp/{row['report_id']}",
                    #        style={'fontWeight': '600', 'fontSize': '14px', 'color': color, 
                    #              'textDecoration': 'none', 'marginRight': '8px'}),
                    html.Div([
                        html.Div(explanation_text, 
                               style={'fontSize': '13px', 'color': '#374151', 'lineHeight': '1.3', 'marginBottom': '4px'}),
                        html.Div(f'"{quote_text}"', 
                               style={'fontSize': '12px', 'color': '#6b7280', 'fontStyle': 'italic', 'lineHeight': '1.2'})
                    ])
                ], style={
                    'backgroundColor': '#f8fafc', 
                    'padding': '8px 10px', 
                    'marginBottom': '6px', 
                    'borderRadius': '4px', 
                    'borderLeft': f'3px solid {color}',
                    'display': 'block'
                })
            )
        
        # Format pattern name for display
        display_name = pattern_name.replace('_', ' ').title().replace('Pattern', '')
        
        # Create tile
        tile = html.Div([
            html.Summary([
                        html.Span(display_name, className=f"entity-name-large"),
                        html.Span(str(count), className=f"entity-count-large")
                    ], className=f"entity-summary-large"),
            # Sample incidents with quotes
            html.Div(incident_divs, style={
                'overflowY': 'auto',
                'maxHeight': '150px'
            })
            
        ], style={
            'backgroundColor': 'white',
            'border': f'1px solid #e2e8f0',
            'borderTop': f'4px solid {color}',
            'borderRadius': '6px',
            'padding': '16px',
            'margin': '8px',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.05)',
            'height': '220px',
            'width': '320px',
            'display': 'inline-block',
            'verticalAlign': 'top',
            'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
            'cursor': 'default'
        }, className='pattern-tile')
        
        tiles.append(tile)
    
    return tiles

def create_pattern_dashboard(csv_file_path, title="Pattern Analysis Dashboard"):
    """
    Create a complete Dash layout with pattern tiles in a compact details format
    """
    
    # Read data for summary stats
    df = pd.read_csv(csv_file_path)
    
    # Create summary stats
    total_incidents = len(df)
    unique_patterns = df['pattern_name'].nunique()
    most_frequent = df['pattern_name'].value_counts().index[0]
    most_frequent_count = df['pattern_name'].value_counts().iloc[0]
    
    # Create the compact details section
    pattern_section = html.Details([
        html.Summary([
            html.Span(f"🤖 Pattern Analysis ({unique_patterns} patterns found)", 
                     style={'fontSize': '14px', 'fontWeight': '600', 'color': '#c7401e'})
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
                    html.Span(f"Total Incidents: {total_incidents}", 
                             style={'fontSize': '12px', 'color': '#6c757d', 'marginRight': '20px'}),
                    html.Span(f"Most Common: {most_frequent.replace('_', ' ').title()} ({most_frequent_count})", 
                             style={'fontSize': '12px', 'color': '#6c757d'})
                ], style={'marginBottom': '15px', 'padding': '8px', 'backgroundColor': '#f8f9fa', 'borderRadius': '4px'}),
                
                # Pattern tiles
                html.Div(create_pattern_tiles(csv_file_path), 
                        style={'textAlign': 'left'})
            ])
        ], style={'padding': '10px'})
    ], open=False)
    
    return pattern_section

def run_pattern_dashboard(csv_file_path, port=8051):
    """
    Run the pattern dashboard app
    """
    app = dash.Dash(__name__)
    
    # Add custom CSS for hover effects
    app.index_string = '''
    <!DOCTYPE html>
    <html>
        <head>
            {%metas%}
            <title>{%title%}</title>
            {%favicon%}
            {%css%}
            <style>
                .pattern-tile:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 8px 15px rgba(0,0,0,0.1), 0 3px 6px rgba(0,0,0,0.1) !important;
                    transition: all 0.2s ease-in-out;
                }
                .pattern-tile a:hover {
                    text-decoration: underline !important;
                }
                .entity-name-large {
                    font-size: 16px;
                    font-weight: 600;
                    color: #1f2937;
                    margin-right: 8px;
                }
                .entity-count-large {
                    font-size: 14px;
                    font-weight: 700;
                    color: #6b7280;
                    background-color: #f3f4f6;
                    padding: 2px 8px;
                    border-radius: 12px;
                }
                .entity-summary-large {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    margin-bottom: 12px;
                    padding-bottom: 8px;
                    border-bottom: 1px solid #e5e7eb;
                }
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
            </style>
        </head>
        <body>
            {%app_entry%}
            <footer>
                {%config%}
                {%scripts%}
                {%renderer%}
            </footer>
        </body>
    </html>
    '''
    
    # Determine title based on filename or content
    try:
        df = pd.read_csv(csv_file_path)
        if 'lucas' in csv_file_path.lower():
            title = "Lucas Ross - Pattern Analysis"
        elif 'abigail' in csv_file_path.lower():
            title = "Abigail Ferguson - Pattern Analysis"
        else:
            title = "Missing Person Pattern Analysis"
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return
    
    # Create a simple layout with just the pattern section
    app.layout = html.Div([
        create_pattern_dashboard(csv_file_path, title)
    ], style={
        'padding': '20px',
        'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
    })
    
    app.run_server(debug=True, port=port)

# Helper function to integrate into sections list
def create_pattern_section(csv_file_path):
    """
    Create pattern section that can be appended to sections list
    """
    df = pd.read_csv(csv_file_path)
    unique_patterns = df['pattern_name'].nunique()
    
    return html.Details([
        html.Summary([
            html.Span(f"Pattern Analysis ({unique_patterns} patterns found)", 
                     style={'fontSize': '14px', 'fontWeight': '600', 'color': '#2E86AB'})
        ], style={
            'cursor': 'pointer', 
            'padding': '10px', 
            'backgroundColor': '#f8f9fa', 
            'border': '1px solid #dee2e6', 
            'borderRadius': '4px'
        }),
        html.Div([
            create_pattern_tiles(csv_file_path)
        ], style={'padding': '10px'})
    ], open=False)

# Simple test function to verify CSV format
def test_pattern_csv_format(csv_file_path):
    """
    Test if CSV has the required columns for pattern analysis
    """
    try:
        df = pd.read_csv(csv_file_path)
        required_cols = ['report_id', 'explanation', 'pattern_name', 'quote']
        
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            print(f"Missing required columns: {missing_cols}")
            print(f"Available columns: {list(df.columns)}")
            return False
        else:
            print(f"CSV format is correct. Found {len(df)} rows.")
            print(f"Pattern types: {df['pattern_name'].unique()}")
            print(f"Sample explanations: {df['explanation'].dropna().head(3).tolist()}")
            return True
            
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return False

# Example usage:
if __name__ == "__main__":
    # Test your CSV first
    csv_file = "lucas_patterns.csv"  # Replace with your file
    
    if test_pattern_csv_format(csv_file):
        run_pattern_dashboard(csv_file)
    else:
        print("Please fix CSV format before running dashboard.")

# To use in your sections list, simply append:
# sections.append(create_pattern_section("your_patterns.csv"))