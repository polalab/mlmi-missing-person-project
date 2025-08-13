import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from dash import html, dcc
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from src.pattern_tiles import create_pattern_dashboard
from utils.date_from_report_id import date_from_reportid
# from create_custom_patterns_vis import create_theme_analysis_summary

def create_summ_mp_timeline_visualization(overview, df, llm_themes, patterns_dashboard=False, case_id=None, themes_in_reports=False):
    """
    Creates a comprehensive timeline visualization component from a dataframe with datetime columns.
    Shows multiple foldable sections: date timeline, time-of-day distribution, 
    day-of-week distribution, length over time, and return method distribution.
    
    Args:
        df: DataFrame with 'date_reported_missing', 'day_reported_missing', 'length_missing_mins', 
            'return_method_desc', and 'reportid' columns
    
    Returns:
        html.Details component containing multiple timeline graphs and statistics
    """
    
    def parse_datetime_safely(dt_str):
        """
        Safely parse datetime string with multiple format attempts.
        Handles ISO 8601 format with Z timezone indicator.
        """
        if pd.isna(dt_str) or dt_str is None or dt_str == '':
            return None
        
        # If it's already a datetime object, return it
        if isinstance(dt_str, datetime):
            return dt_str
        
        # Convert to string and strip whitespace
        dt_str = str(dt_str).strip()
        
        # Handle ISO 8601 format with Z (UTC) timezone indicator
        if dt_str.endswith('Z'):
            dt_str = dt_str[:-1]  # Remove the 'Z'
            try:
                return datetime.fromisoformat(dt_str)
            except ValueError:
                pass
        
        # Try pandas datetime parsing first (handles many formats automatically)
        try:
            parsed = pd.to_datetime(dt_str, errors='coerce')
            if pd.notna(parsed):
                return parsed.to_pydatetime()
        except:
            pass
        
        # Common datetime formats to try
        formats = [
            '%Y-%m-%dT%H:%M:%S',      # ISO format without Z
            '%Y-%m-%dT%H:%M:%SZ',     # ISO format with Z
            '%Y-%m-%dT%H:%M:%S.%f',   # ISO format with microseconds
            '%Y-%m-%dT%H:%M:%S.%fZ',  # ISO format with microseconds and Z
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d',
            '%d/%m/%Y %H:%M:%S',
            '%d/%m/%Y %H:%M',
            '%d/%m/%Y',
            '%m/%d/%Y %H:%M:%S',
            '%m/%d/%Y %H:%M',
            '%m/%d/%Y',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(dt_str, fmt)
            except ValueError:
                continue
        
        # If all formats fail, return None
        return None
    
    def create_section_separator():
        """Create a visual separator line between sections."""
        return html.Hr(style={
            'border': 'none',
            'borderTop': '2px solid #e9ecef',
            'margin': '20px 0',
            'width': '100%'
        })
    
    # Parse datetime data and collect valid entries
    valid_datetimes = []
    invalid_datetimes = []
    
    for idx in range(len(df)):
        if 'date_reported_missing' in df.columns and idx < len(df['date_reported_missing']):
            dt_str = df['date_reported_missing'].iloc[idx]
            reporid = df['reportid'].iloc[idx] if 'reportid' in df.columns and idx < len(df['reportid']) else f"Row {idx + 1}"
            
            # Get additional data
            day_week = df['day_reported_missing'].iloc[idx] if 'day_reported_missing' in df.columns and idx < len(df['day_reported_missing']) else None
            length_missing_mins = df['length_missing_mins'].iloc[idx] if 'length_missing_mins' in df.columns and idx < len(df['length_missing_mins']) else None
            return_method_desc = df['return_method_desc'].iloc[idx] if 'return_method_desc' in df.columns and idx < len(df['return_method_desc']) else None
            
            parsed_dt = parse_datetime_safely(dt_str)
            if parsed_dt:
                valid_datetimes.append({
                    'datetime': parsed_dt,
                    'date': parsed_dt.date(),
                    'time': parsed_dt.time(),
                    'hour': parsed_dt.hour,
                    'minute': parsed_dt.minute,
                    'report_id': str(reporid),
                    'original_string': str(dt_str),
                    'day_week': day_week,
                    'length_missing_mins': length_missing_mins,
                    'return_method_desc': return_method_desc
                })
            else:
                invalid_datetimes.append({
                    'report_id': str(reporid),
                    'original_string': str(dt_str) if dt_str else 'Empty/None'
                })
    
    # Calculate statistics
    total_reports = len(df)
    valid_count = len(valid_datetimes)
    invalid_count = len(invalid_datetimes)
    
    if valid_count == 0:
        # No valid datetimes found
        return html.Details([
            html.Summary([
                html.Div([
                    html.H2("Timeline Analysis", className="locations-main-title"),
                    html.Span(
                        f"No valid datetime data found ({invalid_count} invalid entries)", 
                        className="item-count-prominent"
                    ),
                    html.Span("▼", className="dropdown-arrow")
                ], className="locations-section-header-prominent")
            ], className="locations-summary-prominent"),
            html.Div([
                html.P("No valid datetime data could be parsed from the 'date_reported_missing' column.", 
                      style={'color': '#d63384', 'fontWeight': '600', 'textAlign': 'center', 'padding': '20px'})
            ], className="locations-dropdown-content")
        ], className="locations-section-prominent", open=False)
    
    # SECTION 1: Date Timeline
    def create_date_timeline():
        date_counts = Counter([entry['date'] for entry in valid_datetimes])
        dates = sorted(date_counts.keys())
        date_report_mapping = defaultdict(list)
        
        for entry in valid_datetimes:
            date_report_mapping[entry['date']].append(entry['report_id'])
        
        fig = go.Figure()
        
        # Add timeline baseline
        fig.add_trace(
            go.Scatter(
                x=[dates[0], dates[-1]] if len(dates) > 1 else [dates[0], dates[0]],
                y=[1, 1],
                mode='lines',
                name='Timeline',
                line=dict(color='#2E86AB', width=2),
                showlegend=False,
                hoverinfo='skip'
            )
        )
        
        # Add report markers
        hover_text = []
        for date in dates:
            count = date_counts[date]
            report_ids = date_report_mapping[date][:5]
            ids_text = ", ".join(report_ids)
            if len(date_report_mapping[date]) > 5:
                ids_text += f" (and {len(date_report_mapping[date]) - 5} more)"
            hover_text.append(f"Date: {date}<br>Reports: {count}<br>IDs: {ids_text}")
        
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=[1] * len(dates),
                mode='markers',
                name='Reports',
                marker=dict(size=12, color='#2E86AB', symbol='diamond', line=dict(width=2, color='white')),
                hovertemplate='%{hovertext}<extra></extra>',
                hovertext=hover_text,
                showlegend=False,
                customdata=[date_report_mapping[date][0] for date in dates]
            )
        )
        
        fig.update_layout(
            height=200,
            showlegend=False,
            title_text="Timeline of Reports by Date",
            title_x=0.5,
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=40, r=40, t=60, b=40)
        )
        
        fig.update_xaxes(title_text="Date", showgrid=True, gridcolor='rgba(0,0,0,0.1)')
        fig.update_yaxes(title_text="Timeline", showgrid=False, range=[0.5, 1.5], tickvals=[1], ticktext=['Reports'])
        
        return dcc.Graph(figure=fig, style={'width': '100%', 'height': '200px'})
    
    # SECTION 2: Time of Day Distribution
    def create_time_of_day():
        hour_counts = Counter([entry['hour'] for entry in valid_datetimes])
        hour_report_mapping = defaultdict(list)
        
        for entry in valid_datetimes:
            hour_report_mapping[entry['hour']].append(entry['report_id'])
        
        # Create data for all 24 hours
        hours = list(range(24))
        hour_values = [hour_counts.get(hour, 0) for hour in hours]
        
        # Convert hours to theta (degrees) - 360 degrees / 24 hours = 15 degrees per hour
        theta_values = [hour * 15 for hour in hours]
        
        # Create hour labels in 12-hour format
        hour_labels = []
        for hour in hours:
            if hour == 0:
                hour_labels.append("12 am")
            elif hour < 12:
                hour_labels.append(f"{hour} am")
            elif hour == 12:
                hour_labels.append("12 pm")
            else:
                hour_labels.append(f"{hour-12} pm")
        
        # Create hover text
        hover_text = []
        for hour in hours:
            count = hour_counts.get(hour, 0)
            if count > 0:
                report_ids = hour_report_mapping[hour][:5]
                ids_text = ", ".join(report_ids)
                if len(hour_report_mapping[hour]) > 5:
                    ids_text += f" (and {len(hour_report_mapping[hour]) - 5} more)"
                hover_text.append(f"Hour: {hour_labels[hour]}<br>Reports: {count}<br>IDs: {ids_text}")
            else:
                hover_text.append(f"Hour: {hour_labels[hour]}<br>Reports: 0")
        
        fig = go.Figure()
        
        # Add radial bar chart
        fig.add_trace(
            go.Barpolar(
                theta=theta_values,
                r=hour_values,
                width=[15] * 24,  # Width of each bar in degrees
                marker=dict(
                    color='#4A4A4A',  # Dark gray like the reference
                    opacity=0.8,
                    line=dict(width=1, color='white')
                ),
                hovertemplate='%{hovertext}<extra></extra>',
                hovertext=hover_text
            )
        )
        
        fig.update_layout(
            height=400,
            title_text="Reports by Hour of Day",
            title_x=0.5,
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=40, r=40, t=60, b=40),
            polar=dict(
                radialaxis=dict(
                    title="Number of Reports",
                    showgrid=True,
                    gridcolor='rgba(0,0,0,0.1)',
                    visible=True,
                    range=[0, max(hour_values) * 1.1] if hour_values else [0, 1]
                ),
                angularaxis=dict(
                    tickmode='array',
                    tickvals=theta_values,
                    ticktext=hour_labels,
                    direction='clockwise',
                    rotation=90  # Start at top (12 am)
                )
            ),
            showlegend=False
        )
    
        return dcc.Graph(figure=fig, style={'width': '100%', 'height': '400px'})    
    
    # SECTION 3: Day of Week Distribution
    def create_day_of_week():
        # Get day of week data
        day_week_data = []
        for entry in valid_datetimes:
            if entry['day_week'] is not None and entry['day_week'] != '':
                day_week_data.append({
                    'day': entry['day_week'],
                    'report_id': entry['report_id']
                })
        
        if not day_week_data:
            return html.Div([
                html.P("No day of week data available", style={'textAlign': 'center', 'color': '#666', 'padding': '20px'})
            ])
        
        day_counts = Counter([item['day'] for item in day_week_data])
        day_report_mapping = defaultdict(list)
        
        for item in day_week_data:
            day_report_mapping[item['day']].append(item['report_id'])
        
        # Order days properly
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        days = [day for day in day_order if day in day_counts]
        day_values = [day_counts.get(day, 0) for day in days]
        
        hover_text = []
        for day in days:
            count = day_counts.get(day, 0)
            if count > 0:
                report_ids = day_report_mapping[day][:5]
                ids_text = ", ".join(report_ids)
                if len(day_report_mapping[day]) > 5:
                    ids_text += f" (and {len(day_report_mapping[day]) - 5} more)"
                hover_text.append(f"Day: {day}<br>Reports: {count}<br>IDs: {ids_text}")
            else:
                hover_text.append(f"Day: {day}<br>Reports: 0")
        
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=days,
                y=day_values,
                name='Reports by Day',
                marker=dict(color='#F18F01', opacity=0.8),
                hovertemplate='%{hovertext}<extra></extra>',
                hovertext=hover_text
            )
        )
        
        fig.update_layout(
            height=300,
            showlegend=False,
            title_text="Reports by Day of Week",
            title_x=0.5,
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=40, r=40, t=60, b=40)
        )
        
        fig.update_xaxes(title_text="Day of Week", showgrid=True, gridcolor='rgba(0,0,0,0.1)')
        fig.update_yaxes(title_text="Number of Reports", showgrid=True, gridcolor='rgba(0,0,0,0.1)')
        
        return dcc.Graph(figure=fig, style={'width': '100%', 'height': '300px'})
    
    # SECTION 4: Length Over Time
    def create_length_over_time():
        # Get length data
        length_data = []
        for entry in valid_datetimes:
            if entry['length_missing_mins'] is not None and entry['length_missing_mins'] != '':
                try:
                    length_val = float(entry['length_missing_mins'])
                    if not np.isnan(length_val):
                        length_data.append({
                            'date': entry['date'],
                            'length': length_val,
                            'report_id': entry['report_id']
                        })
                except (ValueError, TypeError):
                    continue
        
        if not length_data:
            return html.Div([
                html.P("No length data available", style={'textAlign': 'center', 'color': '#666', 'padding': '20px'})
            ])
        
        # Sort by date
        length_data.sort(key=lambda x: x['date'])
        
        dates = [item['date'] for item in length_data]
        lengths = [item['length'] for item in length_data]
        report_ids = [item['report_id'] for item in length_data]
        
        # Create hover text with human-readable time format
        hover_text = []
        for date, length, report_id in zip(dates, lengths, report_ids):
            # Convert minutes to human-readable format
            if length >= 1440:  # 24 hours or more
                days = int(length // 1440)
                remaining_hours = int((length % 1440) // 60)
                if remaining_hours > 0:
                    time_str = f"{days} day{'s' if days != 1 else ''}, {remaining_hours} hour{'s' if remaining_hours != 1 else ''}"
                else:
                    time_str = f"{days} day{'s' if days != 1 else ''}"
            elif length >= 60:  # 1 hour or more
                hours = int(length // 60)
                remaining_mins = int(length % 60)
                if remaining_mins > 0:
                    time_str = f"{hours} hour{'s' if hours != 1 else ''}, {remaining_mins} minute{'s' if remaining_mins != 1 else ''}"
                else:
                    time_str = f"{hours} hour{'s' if hours != 1 else ''}"
            else:  # Less than 1 hour
                time_str = f"{length:.0f} minute{'s' if length != 1 else ''}"
            
            hover_text.append(f"Date: {date}<br>Length: {time_str}<br>Report: {report_id}")
        
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=dates,
                y=lengths,
                name='Length Over Time',
                marker=dict(color='#C73E1D'),
                hovertemplate='%{hovertext}<extra></extra>',
                hovertext=hover_text
            )
        )
        
        fig.update_layout(
            height=300,
            showlegend=False,
            title_text="Length of Missing Time Over Date",
            title_x=0.5,
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=40, r=40, t=60, b=40)
        )
        
        fig.update_xaxes(title_text="Date", showgrid=True, gridcolor='rgba(0,0,0,0.1)')
        fig.update_yaxes(title_text="Length (Minutes)", showgrid=True, gridcolor='rgba(0,0,0,0.1)')
        
        return dcc.Graph(figure=fig, style={'width': '100%', 'height': '300px'})
    
    # SECTION 5: Return Method Distribution (NEW PIE CHART)
    def create_return_method_pie():
        # Get return method data
        return_method_data = []
        for entry in valid_datetimes:
            if entry['return_method_desc'] is not None and entry['return_method_desc'] != '':
                return_method_data.append({
                    'method': str(entry['return_method_desc']).strip(),
                    'report_id': entry['report_id']
                })
        
        if not return_method_data:
            return html.Div([
                html.P("No return method data available", style={'textAlign': 'center', 'color': '#666', 'padding': '20px'})
            ])
        
        method_counts = Counter([item['method'] for item in return_method_data])
        method_report_mapping = defaultdict(list)
        
        for item in return_method_data:
            method_report_mapping[item['method']].append(item['report_id'])
        
        # Sort methods by count (descending)
        sorted_methods = sorted(method_counts.items(), key=lambda x: x[1], reverse=True)
        methods = [item[0] for item in sorted_methods]
        method_values = [item[1] for item in sorted_methods]
        
        # Create hover text
        hover_text = []
        for method in methods:
            count = method_counts[method]
            report_ids = method_report_mapping[method][:5]
            ids_text = ", ".join(report_ids)
            if len(method_report_mapping[method]) > 5:
                ids_text += f" (and {len(method_report_mapping[method]) - 5} more)"
            
            # Calculate percentage
            percentage = (count / len(return_method_data)) * 100
            hover_text.append(f"Method: {method}<br>Count: {count} ({percentage:.1f}%)<br>Report IDs: {ids_text}")
        
        # Create a color palette for the pie chart
        colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#4A4A4A', '#8B5A2B', '#228B22', '#8A2BE2', '#DC143C', '#FF8C00']
        # Extend colors if needed
        while len(colors) < len(methods):
            colors.extend(colors)
        
        fig = go.Figure()
        fig.add_trace(
            go.Pie(
                labels=methods,
                values=method_values,
                hole=0.3,  # Creates a donut chart
                marker=dict(colors=colors[:len(methods)]),
                hovertemplate='%{hovertext}<extra></extra>',
                hovertext=hover_text,
                textinfo='label+percent',
                textposition='auto'
            )
        )
        
        fig.update_layout(
            height=400,
            showlegend=True,
            title_text="Return Method Distribution",
            title_x=0.5,
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=40, r=40, t=60, b=40),
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.05
            )
        )
        
        return dcc.Graph(figure=fig, style={'width': '100%', 'height': '400px'})
    
    # Create all sections
    sections = [overview]
    
    # Section 1: Date Timeline
    sections.append(
        html.Details([
            html.Summary([
                html.Span("Timeline of Reports", style={'fontSize': '14px', 'fontWeight': '600', 'color': '#2E86AB'})
            ], style={'cursor': 'pointer', 'padding': '10px', 'backgroundColor': '#f8f9fa', 'border': '1px solid #dee2e6', 'borderRadius': '4px'}),
            html.Div([
                create_date_timeline()
            ], style={'padding': '10px'})
        ], open=False)
    )
    
    sections.append(create_section_separator())
    
    # Section 2: Time of Day
    sections.append(
        html.Details([
            html.Summary([
                html.Span("Time of Day Distribution", style={'fontSize': '14px', 'fontWeight': '600', 'color': '#A23B72'})
            ], style={'cursor': 'pointer', 'padding': '10px', 'backgroundColor': '#f8f9fa', 'border': '1px solid #dee2e6', 'borderRadius': '4px'}),
            html.Div([
                create_time_of_day()
            ], style={'padding': '10px'})
        ], open=False)
    )
    
    sections.append(create_section_separator())
    
    # Section 3: Day of Week
    sections.append(
        html.Details([
            html.Summary([
                html.Span("Day of Week Distribution", style={'fontSize': '14px', 'fontWeight': '600', 'color': '#F18F01'})
            ], style={'cursor': 'pointer', 'padding': '10px', 'backgroundColor': '#f8f9fa', 'border': '1px solid #dee2e6', 'borderRadius': '4px'}),
            html.Div([
                create_day_of_week()
            ], style={'padding': '10px'})
        ], open=False)
    )
    
    sections.append(create_section_separator())
    
    # Section 4: Length Over Time
    sections.append(
        html.Details([
            html.Summary([
                html.Span("Length Over Time", style={'fontSize': '14px', 'fontWeight': '600', 'color': '#C73E1D'})
            ], style={'cursor': 'pointer', 'padding': '10px', 'backgroundColor': '#f8f9fa', 'border': '1px solid #dee2e6', 'borderRadius': '4px'}),
            html.Div([
                create_length_over_time()
            ], style={'padding': '10px'})
        ], open=False)
    )
    
    sections.append(create_section_separator())
    
    # Section 5: Return Method Distribution (NEW SECTION)
    sections.append(
        html.Details([
            html.Summary([
                html.Span("Return Method Distribution", style={'fontSize': '14px', 'fontWeight': '600', 'color': '#8B5A2B'})
            ], style={'cursor': 'pointer', 'padding': '10px', 'backgroundColor': '#f8f9fa', 'border': '1px solid #dee2e6', 'borderRadius': '4px'}),
            html.Div([
                create_return_method_pie()
            ], style={'padding': '10px'})
        ], open=False)
    )
    
    sections.append(create_section_separator())
    
    # Section 6: Themes in Reports
    if themes_in_reports:
        sections.append(
            html.Details([
                html.Summary([
                    html.Span("🤖 Themes in Reports", style={'fontSize': '14px', 'fontWeight': '600', 'color': '#C73E1D'})
                ], style={'cursor': 'pointer', 'padding': '10px', 'backgroundColor': '#f8f9fa', 'border': '1px solid #dee2e6', 'borderRadius': '4px'}),
                html.Div([
                    llm_themes
                ], style={'padding': '10px'})
            ], open=False)
        )
    
    # Calculate summary statistics
    if valid_datetimes:
        earliest_date = min(entry['date'] for entry in valid_datetimes)
        latest_date = max(entry['date'] for entry in valid_datetimes)
        date_range = (latest_date - earliest_date).days
    else:
        earliest_date = latest_date = None
        date_range = 0
    
    # Add invalid datetime entries component if needed
    if invalid_datetimes:
        sections.append(create_section_separator())
        
        invalid_items = []
        for entry in invalid_datetimes:
            invalid_items.append(
                html.Div([
                    html.Span("❌", style={'marginRight': '4px', 'fontSize': '12px'}),
                    html.Span(f"Report {entry['report_id']}: ", style={'fontWeight': '600', 'fontSize': '11px', 'marginRight': '4px'}),
                    html.Span(entry['original_string'], style={'fontSize': '10px', 'color': '#666', 'fontStyle': 'italic'})
                ], style={'display': 'inline-block', 'margin': '2px 8px 2px 0', 'padding': '3px 6px', 'backgroundColor': '#fff5f5', 'border': '1px solid #fed7d7', 'borderRadius': '3px', 'fontSize': '10px'})
            )
        
        sections.append(
            html.Details([
                html.Summary([
                    html.Span(f"⚠️ Invalid DateTime Entries ({invalid_count})", style={'fontSize': '12px', 'fontWeight': '600', 'color': '#d63384'})
                ], style={'cursor': 'pointer', 'padding': '6px', 'backgroundColor': '#fff5f5', 'border': '1px solid #fed7d7', 'borderRadius': '4px'}),
                html.Div([
                    html.P("DateTime entries that could not be parsed:", style={'fontSize': '10px', 'color': '#666', 'margin': '8px 0 6px 0'}),
                    html.Div(invalid_items, style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '2px'})
                ], style={'padding': '8px'})
            ])
        )
    
    if patterns_dashboard and case_id:
        sections.append(create_section_separator())
        sections.append(create_pattern_dashboard(f"NEW/{case_id}/patterns/pattern_types.csv"))
    
    return html.Details([
        html.Summary([
            html.Div([
                html.H2("Patterns", className="locations-main-title"),
                html.Span("▼", className="dropdown-arrow")
            ], className="locations-section-header-prominent")
        ], className="locations-summary-prominent"),
        html.Div(sections, className="locations-dropdown-content")
    ], className="locations-section-prominent", open=False)