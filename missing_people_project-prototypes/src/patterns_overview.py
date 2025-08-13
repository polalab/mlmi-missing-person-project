import pandas as pd
import dash
from dash import html, dcc
import plotly.express as px
from collections import Counter
from utils.formatting import format_minutes
from utils.date_from_report_id import date_from_reportid
import os

def create_section_separator():
        """Create a visual separator line between sections."""
        return html.Hr(style={
            'border': 'none',
            'borderTop': '2px solid #e9ecef',
            'margin': '20px 0',
            'width': '100%'
        })
        
def create_pattern_quotes(case_id):
    folder_path = f"NEW/{str(case_id)}/patterns"
    quotes_path = os.path.join(folder_path, 'vul_llama3.1_list.txt')
    quotes = ""
    
    try:
        with open(quotes_path, 'r', encoding='utf-8') as f:
            quotes = f.read()
                     
        parsed_quotes = [(line.split(',', 1)[0].strip(), line.split(',', 1)[1].strip()) 
                        for line in quotes.strip().split('\n') if ',' in line]
        
        narrative_path = os.path.join(folder_path, 'vul_llama3.1_narrative.txt')
        narrative = ""
        with open(narrative_path, 'r', encoding='utf-8') as f:
            narrative = f.read()
                     
        # Create list items for bulleted display
        list_items = []
        for id, quote in parsed_quotes:
            if quote:
                list_items.append(
                    html.Li([
                        html.Span(quote, className="comment-text"),
                        html.Span(" (", className="comment-source"),
                        date_from_reportid(id, "mp"),
                        html.Span(")", className="comment-source")
                    ], style={'marginBottom': '8px'})
                )
        
        # Create summary with narrative and quote count
        quote_count = len(parsed_quotes)
        summary_text = f"🤖 Patterns ({quote_count} quotes)"
        if narrative.strip():
            summary_text += f":{narrative}"
        else:
            summary_text = f"🤖 Patterns ({quote_count} quotes) - No narrative available"
                 
        return html.Details([
            html.Summary([
                html.Span(summary_text, style={
                    'fontSize': '14px', 
                    'fontWeight': '600', 
                    'color': '#f8f9fa',
                })
            ], style={
                'cursor': 'pointer', 
                'padding': '10px', 
                'backgroundColor': '#2664eb', 
                'border': '1px solid #dee2e6', 
                'borderRadius': '4px'
            }),
            html.Div([
                html.Ul(list_items, style={
                    'paddingLeft': '20px',
                    'margin': '0'
                }) if list_items else html.P("No pattern quotes available.", style={'color': '#666', 'fontStyle': 'italic'})
            ], style={'padding': '10px'})
        ], open=False)
             
    except (FileNotFoundError, Exception):
        # Return empty foldable pattern if files don't exist
        return html.Details([
            html.Summary([
                html.Span("🤖 Patterns (0 quotes) - Files not found", style={
                    'fontSize': '14px', 
                    'fontWeight': '600', 
                    'color': '#F18F01'
                })
            ], style={
                'cursor': 'pointer', 
                'padding': '10px', 
                'backgroundColor': '#e6ebf2', 
                'border': '1px solid #dee2e6', 
                'borderRadius': '4px'
            }),
            html.Div([
                html.P("Pattern files not found for this case.", style={'color': '#666', 'fontStyle': 'italic'})
            ], style={'padding': '10px'})
        ], open=False)

def create_expandable_pattern(icon, label, value, report_ids, report_type):
    """Create a pattern that can expand to show related reports"""
    if report_ids and len(report_ids) > 0:
        # Create list items for report links
        report_list_items = [
            
            date_from_reportid(rid, report_type) for rid in report_ids
        ]
       
        return html.Details([
            html.Summary([
                html.Div([
                    html.Span(icon, className="stat-icon-horizontal"),
                    html.Div([
                        html.Span(label, className="stat-label-horizontal"),
                        html.Span(str(value), className="stat-value-horizontal")
                    ], className="stat-text-vertical")
                ], className="stat-chip-horizontal")
            ], className="stat-summary-chip"),
            html.Div([
                html.Ul(report_list_items, style={
                    'paddingLeft': '20px',
                    'margin': '0'
                })
            ], className="report-dropdown")
        ], className="stat-expandable-chip")
    else:
        # Simple version without expansion
        return create_simple_pattern(icon, label, value)

def create_simple_pattern(icon, label, value):
    """Create a simple non-expandable stat"""
    return html.Div([
        html.Span(icon, className="stat-icon-horizontal"),
        html.Div([
            html.Span(label, className="stat-label-horizontal"),
            html.Span(str(value), className="stat-value-horizontal")
        ], className="stat-text-vertical")
    ], className="stat-chip-horizontal stat-chip-simple")


def patterns_section(df_mp_misperid, df_vp_misperid, case_id, includenarrative=False):
    """Create a simple patterns and statistics section"""
    
    general_patterns = []
    initial_risk_patterns = []
    final_risk_patterns = []
    
    # MP incidents count with expandable list
    if not df_mp_misperid.empty:
        mp_report_ids = sorted(df_mp_misperid['reportid'].tolist())
        general_patterns.append(create_expandable_pattern("👤", "MP Reports", len(df_mp_misperid), mp_report_ids, "mp"))
    
    # VP records count with expandable list
    if not df_vp_misperid.empty:
        vp_report_ids = sorted(df_vp_misperid['reportid'].tolist())
        general_patterns.append(create_expandable_pattern("🚨", "VP Records", len(df_vp_misperid), vp_report_ids, "vp"))
    
    # Average time missing (no expansion needed)
    if not df_mp_misperid.empty and 'length_missing_mins' in df_mp_misperid.columns:
        avg_time = df_mp_misperid['length_missing_mins'].mean()
        if pd.notna(avg_time):
            general_patterns.append(create_simple_pattern("⏱️", "Avg Missing", format_minutes(avg_time)))
    
    # Longest time missing with link to specific report
    if not df_mp_misperid.empty and 'length_missing_mins' in df_mp_misperid.columns:
        valid_times = df_mp_misperid.dropna(subset=['length_missing_mins'])
        if not valid_times.empty:
            longest_idx = valid_times['length_missing_mins'].idxmax()
            longest_report = valid_times.loc[longest_idx]
            max_time = longest_report['length_missing_mins']
            report_id = longest_report['reportid']
            general_patterns.append(create_expandable_pattern("📅", "Max Missing", format_minutes(max_time), [report_id], "mp"))
    
    # Most common day with reports on that day
    if not df_mp_misperid.empty and 'day_reported_missing' in df_mp_misperid.columns:
        valid_days = df_mp_misperid.dropna(subset=['day_reported_missing'])
        if not valid_days.empty:
            common_day = valid_days['day_reported_missing'].mode()
            if not common_day.empty:
                day_name = common_day.iloc[0]
                reports_on_day = valid_days[valid_days['day_reported_missing'] == day_name]['reportid'].tolist()
                general_patterns.append(create_expandable_pattern("📆", "Common Day", day_name + " (" + f"in {str(len(reports_on_day))} /{len(df_mp_misperid)})", reports_on_day, "mp"))

    # Risk level tiles for initial_risk_level
    combined_df = pd.concat([df_mp_misperid, df_vp_misperid], ignore_index=True)
    if not combined_df.empty and 'initial_risk_level' in combined_df.columns:
        initial_risk_counts = combined_df['initial_risk_level'].value_counts()
        
        # High risk initial
        if 'High' in initial_risk_counts:
            high_initial_reports = combined_df[combined_df['initial_risk_level'] == 'High']['reportid'].tolist()
            initial_risk_patterns.append(create_expandable_pattern("🔴", "High Initial Risk", initial_risk_counts['High'], high_initial_reports, "mp"))
        
        # Medium risk initial
        if 'Medium' in initial_risk_counts:
            medium_initial_reports = combined_df[combined_df['initial_risk_level'] == 'Medium']['reportid'].tolist()
            initial_risk_patterns.append(create_expandable_pattern("🟡", "Medium Initial Risk", initial_risk_counts['Medium'], medium_initial_reports, "mp"))
        
        # Low risk initial
        if 'Low' in initial_risk_counts:
            low_initial_reports = combined_df[combined_df['initial_risk_level'] == 'Low']['reportid'].tolist()
            initial_risk_patterns.append(create_expandable_pattern("🟢", "Low Initial Risk", initial_risk_counts['Low'], low_initial_reports, "mp"))
    
    # Risk level tiles for current_final_risk_level
    if not combined_df.empty and 'current_final_risk_level' in combined_df.columns:
        final_risk_counts = combined_df['current_final_risk_level'].value_counts()
        
        # High risk final
        if 'High' in final_risk_counts:
            high_final_reports = combined_df[combined_df['current_final_risk_level'] == 'High']['reportid'].tolist()
            final_risk_patterns.append(create_expandable_pattern("🔴", "High Final Risk", final_risk_counts['High'], high_final_reports, "mp"))
        
        # Medium risk final
        if 'Medium' in final_risk_counts:
            medium_final_reports = combined_df[combined_df['current_final_risk_level'] == 'Medium']['reportid'].tolist()
            final_risk_patterns.append(create_expandable_pattern("🟡", "Medium Final Risk", final_risk_counts['Medium'], medium_final_reports, "mp"))
        
        # Low risk final
        if 'Low' in final_risk_counts:
            low_final_reports = combined_df[combined_df['current_final_risk_level'] == 'Low']['reportid'].tolist()
            final_risk_patterns.append(create_expandable_pattern("🟢", "Low Final Risk", final_risk_counts['Low'], low_final_reports, "mp"))
    
    # Build the section content
    content = []
    
    patterns_overview = create_pattern_quotes(case_id) if includenarrative else None
    
    # Combine all patterns into grid rows
    all_patterns = []
    if general_patterns:
        all_patterns.append(html.Div(general_patterns, className="stats-horizontal-grid"))
    if initial_risk_patterns:
        all_patterns.append(html.Div(initial_risk_patterns, className="stats-horizontal-grid"))
    if final_risk_patterns:
        all_patterns.append(html.Div(final_risk_patterns, className="stats-horizontal-grid"))
    
    # Add Quick Stats section
    if all_patterns:
        total_pattern_count = len(general_patterns) + len(initial_risk_patterns) + len(final_risk_patterns)
        content.append(html.Div([
            html.Div([
                html.H4("General Patterns", className="compact-section-title"),
                html.Span(f"{total_pattern_count}", className="item-count-small")
            ], className="compact-section-header"),
            html.Div(all_patterns, className="stats-grid-rows")
        ], className="compact-section"))
    
    # Add patterns overview if requested
    if patterns_overview:
        content.append(patterns_overview)
        content.append(create_section_separator())
    
    return html.Div(content)