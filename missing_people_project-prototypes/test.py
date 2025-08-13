import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime
import pytz

from rule_based.create_rule_based_summary import CreateSummary, ReadCsvFiles



app = dash.Dash(__name__)

summary_creator = CreateSummary(960)
df = summary_creator.mp_df_misperid
df = df[['missing_since', 'date_reported_missing', 'day_reported_missing','length_missing_mins']]
df['reporting_delay_hours'] = (df['date_reported_missing'] - df['missing_since']).dt.total_seconds() / 60/60
df['duration_hours'] = df['length_missing_mins'] / 60
df['incident_number'] = df.index + 1
df['year'] = df['missing_since'].dt.year
df['month'] = df['missing_since'].dt.month
df['hour'] = df['missing_since'].dt.hour

def format_hours_to_hms(hours_float):
    total_seconds = int(hours_float * 3600)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours}h {minutes}m {seconds}s"


app.layout = html.Div([
    html.H1("Missing Persons Patterns Dashboard", 
            style={'textAlign': 'center', 'color': '2c3e50', 'marginBottom': 30}),
    
    html.Div([
    html.Div([
        html.Div([
            html.H3("Key Statistics", style={'color': '#34495e',  'marginBottom': '10px'}),
            html.P(f"Total Incidents: {len(df)}"),
            html.P(f"Average Duration going missing: {format_hours_to_hms(df['length_missing_mins'].mean())}"),
            html.P(f"Longest Incident: {int(df['length_missing_mins'].max())} h"),
            html.P(f"Most Common Day: Monday ({df[df['day_reported_missing']=='Monday'].shape[0]} incidents)")
        ], style={'width': '50%'}),

        html.Div([
            dcc.Dropdown(
                id='demo-dropdown',
                options=[
                    {'label': 'Timeline View', 'value': 'timeline'},
                    {'label': 'Duration Analysis', 'value': 'duration'},
                    {'label': 'Day of Week Pattern', 'value': 'day_pattern'},
                    {'label': 'Time of Day Pattern', 'value': 'time_pattern'}
                ],
                value='timeline',
                style={'marginBottom': 2},
                optionHeight=35,
                maxHeight=100
            ),
        ], style={'width': '48%','overflowY': 'auto',})
    ], style={'display': 'flex', 'alignItems': 'flex-start', 'marginBottom': 0, })
    ]),
    
    dcc.Graph(id='main-graph', style={'height': '600px'}),
    
    html.Div(id='incident-details', style={'marginTop': 20, 'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '10px'})
])

@app.callback(
    Output('main-graph', 'figure'),
    Input('demo-dropdown', 'value')
)
def update_graph(selected_view):
    if selected_view == 'timeline':
        # Timeline scatter plot
        fig = go.Figure()
        
        # Add scatter points for missing incidents
        fig.add_trace(go.Scatter(
            x=df['missing_since'],
            y=df['duration_hours'],
            mode='markers+lines',
            marker=dict(
                size=df['duration_hours'] * 2 + 10,
                color=df['duration_hours'],
                showscale=True,
                colorbar=dict(title="Duration (hours)"),
                line=dict(width=2, color='darkred')
            ),
            text=[f"Incident #{row['incident_number']}<br>" +
                  f"Missing Since: {row['missing_since'].strftime('%Y-%m-%d %H:%M')}<br>" +
                  f"Reported: {row['date_reported_missing'].strftime('%Y-%m-%d %H:%M')}<br>" +
                  f"Duration: {row['duration_hours']:.1f} hours<br>" +
                  f"Reporting Delay: {format_hours_to_hms(row['reporting_delay_hours'])}"
                  for _, row in df.iterrows()],
            hovertemplate='%{text}<extra></extra>',
            name='Missing Incidents'
        ))
        
        fig.update_layout(
            title='Missing Persons Timeline - Duration vs Date',
            xaxis_title='Date Missing',
            yaxis_title='Duration Missing (Hours)',
            hovermode='closest',
            showlegend=False
        )
        
    elif selected_view == 'duration':
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df['incident_number'],
            y=df['duration_hours'],
            marker_color=df['duration_hours'],
            marker_colorscale='Reds',
            text=[f"{dur:.1f}h" for dur in df['duration_hours']],
            textposition='outside',
            hovertemplate='Incident #%{x}<br>Duration: %{y:.1f} hours<extra></extra>'
        ))
        
        fig.update_layout(
            title='Missing Duration by Incident',
            xaxis_title='Incident Number',
            yaxis_title='Duration (Hours)',
            showlegend=False
        )
        
    elif selected_view == 'day_pattern':
        # Day of week pattern
        day_counts = df['day_reported_missing'].value_counts()
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_counts = day_counts.reindex(day_order, fill_value=0)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=day_counts.index,
            y=day_counts.values,
            marker_color=['#e74c3c' if day == 'Monday' else '#3498db' for day in day_counts.index],
            text=day_counts.values,
            textposition='outside'
        ))
        
        fig.update_layout(
            title='Missing Persons Reports by Day of Week',
            xaxis_title='Day of Week',
            yaxis_title='Number of Reports',
            showlegend=False
        )
        
    else:  # time_pattern
        # Time of day pattern
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['hour'],
            y=df['duration_hours'],
            mode='markers',
            marker=dict(
                size=15,
                color=df['duration_hours'],
                colorscale='Reds',
                showscale=True,
                colorbar=dict(title="Duration (hours)")
            ),
            text=[f"Incident #{row['incident_number']}<br>" +
                  f"Time: {row['hour']:02d}:00<br>" +
                  f"Duration: {row['duration_hours']:.1f} hours"
                  for _, row in df.iterrows()],
            hovertemplate='%{text}<extra></extra>'
        ))
        
        fig.update_layout(
            title='Missing Time vs Duration Pattern',
            xaxis_title='Hour of Day Going Mising',
            yaxis_title='Duration Missing (Hours)',
            xaxis=dict(tickmode='array', tickvals=list(range(0, 24, 2))),
            showlegend=False
        )
    
    return fig

@app.callback(
    Output('incident-details', 'children'),
    Input('main-graph', 'clickData')
)
def display_incident_details(clickData):
    if clickData is None:
        return html.Div([
            html.H4("Incident Details"),
            html.P("Click on any point in the graph above to see detailed information about that incident.")
        ])
    
    # Extract the incident information from click data
    point_index = clickData['points'][0]['pointIndex']
    incident = df.iloc[point_index]
    
    return html.Div([
        html.H4(f"Incident #{incident['incident_number']} Details"),
        html.Div([
            html.P(f"Missing Since: {incident['missing_since'].strftime('%A, %B %d, %Y at %H:%M UTC')}"),
            html.P(f"Reported Missing: {incident['date_reported_missing'].strftime('%A, %B %d, %Y at %H:%M UTC')}"),
            html.P(f"Duration Missing: {incident['duration_hours']:.1f} hours ({incident['length_missing_mins']} minutes)"),
            html.P(f"Reporting Delay: {format_hours_to_hms(incident['reporting_delay_hours'])}"),
            html.P(f"Day Reported: {incident['day_reported_missing']}"),
        ], style={'columnCount': 2, 'columnGap': '40px'})
    ])

if __name__ == "__main__":
    app.run(debug=True, port=8053)
