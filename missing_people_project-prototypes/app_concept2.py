import os
import ast
import pandas as pd
import dash
from dash import dcc, html, Input, Output, callback, State, ALL
import plotly.express as px
from collections import Counter, defaultdict
from urllib.parse import urlparse
from datetime import datetime, timedelta
from rule_based.create_rule_based_summary import CreateSummary, ReadCsvFiles
import os
from src.map_functions import create_summ_mp_missing_from_found_locations_map
from src.create_timeline import create_summ_mp_timeline_visualization
from src.vurnabilities import create_mp_risk_questions_summary, create_vp_risk_questions_summary
from src.create_custom_patterns_vis import create_theme_analysis_summary
from flask import request
from src.assograph import create_association_network_graph
from src.basic_info import create_person_overview
from src.patterns_overview import patterns_section
from src.helper_reports import create_question_card

app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=['/assets/styles.css'])
server = app.server
dcc.Location(id='url', refresh=False)


# Simple password protection
@server.before_request
def require_password():
    auth = request.authorization
    username = os.environ.get('AUTH_USERNAME', 'adsssmin')
    password = os.environ.get('AUTH_PASSWORD', 'secret123')
    
    print(f"Using username: {username}")
    print(f"Using password: {password}")
    
    if not auth or auth.username != username or auth.password != password:
        return ('Please enter username and password', 401, {
            'WWW-Authenticate': 'Basic realm="Protected Site"'
        })


# Data loading
df_mp = pd.read_csv('DATA/mp_new_geolocations.csv')

df_mp['dob'] = pd.to_datetime(df_mp['dob'])
df_mp['missing_since'] = pd.to_datetime(df_mp['missing_since'])
df_mp['date_reported_missing'] = pd.to_datetime(df_mp['date_reported_missing'])
df_mp['whentraced'] = pd.to_datetime(df_mp['whentraced'])
df_mp.loc[:, 'source'] = 'mp'
df_vp = pd.read_csv('DATA/vp_new.csv')
df_vp.rename(columns={"VPD_NOMINALINCIDENTID_PK": "reportid"}, inplace=True)
df_vp.columns = df_vp.columns.str.replace('.', '_', regex=False).str.lower()

df_phys = pd.read_csv('DATA/phys.csv')
df_chr = pd.read_csv('DATA/chr_.csv')
read_csv_files = ReadCsvFiles()
qs_comments_df = read_csv_files.qs_comments_df

dict_dfs = {"mp": df_mp, "vp": df_vp, "phys": df_phys, "chr": df_chr}




def create_summ_mp_missing_from_found_locations(df):
    """Create a prominent table of missing person locations - now foldable"""
    if df.empty:
        return html.Details([
            html.Summary([
                html.Div([
                    html.H2("Missing From → Traced To", className="locations-main-title"),
                    html.Span("▼", className="dropdown-arrow")
                ], className="locations-section-header-prominent")
            ], className="locations-summary-prominent"),
            html.Div([
                html.P("No location data available", className="no-data-message-large")
            ], className="locations-dropdown-content")
        ], className="locations-section-prominent")
    
    # Create table header with more prominent styling
    table_header = html.Thead([
        html.Tr([
            html.Th("📍 Missing From Location", className="table-header-primary"),
            html.Th("→", className="table-header-arrow-prominent"),
            html.Th("Traced To Location", className="table-header-primary"),
            html.Th("📅 Date", className="table-header-secondary"),
            html.Th("📋 Report", className="table-header-secondary")
        ])
    ])
    
    # Create table rows with enhanced styling
    table_rows = []
    for _, row in df.iterrows():
        missing_from = row.get('missing_from', 'Unknown')
        mf_address = row.get('mf_address', 'Address not specified')
        tl_address = row.get('tl_address', 'Not traced')
        
        date_reported = str(row.get('date_reported_missing', 'Unknown'))
        date_reported = datetime.fromisoformat(date_reported)

        # Format it with date and time on separate lines
        date_reported = date_reported.strftime("%Y-%m-%d\n%H:%M:%S")
        report_id = row.get('reportid', 'Unknown')
        
        # Enhanced location display
        missing_location = html.Div([
            html.Strong(missing_from, className="location-name-prominent"),
            html.Br(),
            html.Span(mf_address, className="location-address-prominent")
        ])
        
        traced_location = html.Div([
            html.Strong(
                tl_address if tl_address not in ['Not traced', 'nan', ''] else "Not yet traced",
                className="traced-location-prominent" if tl_address not in ['Not traced', 'nan', ''] else "not-traced-prominent"
            )
        ])
        
        table_row = html.Tr([
            html.Td(missing_location, className="table-cell-prominent"),
            html.Td("→", className="table-cell-arrow-prominent"),
            html.Td(traced_location, className="table-cell-prominent"),
            html.Td(date_reported, className="report-date-btn-prominent table-cell-date"),
            html.Td([
                dcc.Link(
                    str(report_id),
                    href=f"/report/mp/{report_id}",
                    className="report-link-prominent"
                )
            ], className="table-cell-prominent table-cell-center")
        ], className="table-row-prominent")
        
        table_rows.append(table_row)
    
    table_body = html.Tbody(table_rows)
    
    return html.Details([
        html.Summary([
            html.Div([
                html.H2("Missing From → Traced To", className="locations-main-title"),
                html.Span(f"{len(table_rows)} location record{'s' if len(table_rows) != 1 else ''}", 
                         className="item-count-prominent"),
                html.Span("▼", className="dropdown-arrow")
            ], className="locations-section-header-prominent")
        ], className="locations-summary-prominent"),
        html.Div([
            html.Div([
                html.Table([table_header, table_body], className="locations-table-prominent")
            ], className="table-container-prominent")
        ], className="locations-dropdown-content")
    ], className="locations-section-prominent", open=True)


def create_summ_mp_home_locations(mp_df_misperid):
    """Create a compact home addresses display"""
    if mp_df_misperid.empty:
        return html.Div([
            html.Div([
                html.H4("Home Addresses", className="compact-section-title"),
                html.P("No address data", className="no-data-compact")
            ], className="compact-section empty-section")
        ])
    
    # Get unique addresses
    unique_addresses = mp_df_misperid['ha_address'].dropna().unique()
    
    address_duration = mp_df_misperid.groupby('ha_address')['missing_since'].agg(['min', 'max'])
    address_duration['first_date'] = address_duration['min'].dt.strftime('%d-%m-%Y')
    address_duration['last_date'] = address_duration['max'].dt.strftime('%d-%m-%Y')
    address_duration = address_duration[['first_date', 'last_date']]
    address_duration = address_duration.reset_index()
    
    print("WWWW", address_duration)
    # Create compact address chips
    address_chips = []
    
    for id, row in address_duration.iterrows(): 
        address_chips.append(
            html.Details([
                html.Summary([
                    html.Span(row['ha_address'], className="entity-name-large"),
                    html.Span(str(row['first_date'] + " to " + str(row['last_date'])), className="comment-text-medium"),
                ], className="home-address-prominent"),
            ], className="home-address-prominent")
        )
           
    content = html.Div(address_chips)
    
    return html.Div([
        html.Div([
            html.H4("Home Addresses", className="compact-section-title"),
            html.Span(f"{len(unique_addresses)}", className="item-count-small")
        ], className="compact-section-header"),
        html.Div(content, className="address-chips-container")
    ], className="compact-section")


def report_page(type, reportid):
    try:
        df = dict_dfs[type]
        row = df[df['reportid'] == int(reportid)].squeeze()
    except (ValueError, KeyError):
        return html.Div("Invalid report.", className="error-card")

    if row.empty:
        return html.Div("Report not found.", className="error-card")

    content = [html.H2(f"Report #{reportid}", className="report-title")]
    
    if type == "mp":
        # Basic info section
        basic_info = html.Div([
            html.H3("Basic Information", className="section-header"),
            html.Div([
                html.Div([
                    html.Span(f"{col}: ", className="field-label"),
                    html.Span(str(row[col]), className="field-value")
                ], className="field-row") for col in  row.index
            ], className="info-grid")
        ], className="section-card")
        
        # Questions section
        questions_section = html.Div([
            html.H3("Risk Assessment Questions", className="section-header"),
            html.Div([
                create_question_card(q_n, row)
                for q_n in [f'q_{n}' for n in range (1, 26)]
            ], className="questions-grid")
        ], className="section-card")
        
        content.extend([basic_info, questions_section])
    else:
        # Other report types
        content.append(html.Div([
            html.Div([
                html.Span(f"{col}: ", className="field-label"),
                html.Span(str(row[col]), className="field-value")
            ], className="field-row") for col in df.columns
        ], className="info-grid section-card"))

    content.append(html.Div([
        dcc.Link("← Back to Home", href="/", className="btn btn-secondary")
    ], className="actions"))
    
    return html.Div(content, className="report-page")



def remove_leading_stop_words(text):
    stop_words = ['the', 'a', 'an', 'and', 'or', 'of', 'in', 'to', 'for', 'with', 'by', 'at', 'on', 'from', 'as']
    words = text.split()
    while words and words[0].lower() in [sw.lower() for sw in stop_words]:
        words.pop(0)
    return ' '.join(words)

def is_relevant(entity, irrelevant_list):
    entity = remove_leading_stop_words(entity)
    return not any(entity.lower().startswith(prefix.lower()) for prefix in irrelevant_list)

def process_entities(file):
    df = pd.read_csv(file, names=['id', 'type', 'value'])
    irrelevant_entities = ['MP', 'nan']
    
    names_dict = defaultdict(list)
    desc_dict = defaultdict(list)
    
    for _, row in df.iterrows():
        if row['type'] == 'people_names_relations':
            names_dict[row['value']].append(row['id'])
        elif row['type'] == 'people_desc':
            desc_dict[row['value']].append(row['id'])
    
    # Filter and sort
    names_dict = {k: v for k, v in names_dict.items() if is_relevant(str(k), irrelevant_entities)}
    desc_dict = {k: v for k, v in desc_dict.items() if is_relevant(str(k), irrelevant_entities)}
    
    names_summary = sorted([(entity, len(ids), ids) for entity, ids in names_dict.items()], 
                          key=lambda x: x[1], reverse=True)
    desc_summary = sorted([(entity, len(ids), ids) for entity, ids in desc_dict.items()], 
                         key=lambda x: x[1], reverse=True)
    
    return names_summary, desc_summary

def process_entities_locations(file):
    df = pd.read_csv(file, names=['id', 'type', 'value'])
    irrelevant_entities = ['MP', 'nan']
    
    addresses_dict = defaultdict(list)
    locations_dict = defaultdict(list)
    
    for _, row in df.iterrows():
        if row['type'] == 'addresses':
            addresses_dict[row['value']].append(row['id'])
        elif row['type'] == 'landmarks_other_locations':
            locations_dict[row['value']].append(row['id'])
    
    # Filter and sort
    addresses_dict = {k: v for k, v in addresses_dict.items() if is_relevant(str(k), irrelevant_entities)}
    locations_dict = {k: v for k, v in locations_dict.items() if is_relevant(str(k), irrelevant_entities)}
    
    addresses_summary = sorted([(entity, len(ids), ids) for entity, ids in addresses_dict.items()], 
                          key=lambda x: x[1], reverse=True)
    locations_summary = sorted([(entity, len(ids), ids) for entity, ids in locations_dict.items()], 
                         key=lambda x: x[1], reverse=True)
    
    return addresses_summary, locations_summary

def load_case_data(case_id):
    folder_path = f"NEW/{str(case_id)}/assosiation_network"
    entities_path = os.path.join(folder_path, 'people_llama3.1_both.txt')
    if not os.path.exists(folder_path):
        names = []
        descriptions = []
    else:
        names, descriptions = process_entities(entities_path)
    narrative_path = os.path.join(folder_path, 'people_llama3.1_both_narrative.txt')
    narrative_people = ""
    if os.path.exists(narrative_path):
        with open(narrative_path, 'r', encoding='utf-8') as f:
            narrative_people = f.read()
    
    folder_path = f"NEW/{str(case_id)}/vul"
    narrative_path = os.path.join(folder_path, 'vul_llama3.1_narrative.txt')
    narrative_vul = ""
    if os.path.exists(narrative_path):
        with open(narrative_path, 'r', encoding='utf-8') as f:
            narrative_vul = f.read()
    
    folder_path = f"NEW/{str(case_id)}/locations"
    entities_path = os.path.join(folder_path, 'locations3.1_both.txt')
    if not os.path.exists(folder_path):
        addresses = []
        locations = []
    else:
        addresses, locations = process_entities_locations(entities_path)
    
    narrative_path = os.path.join(folder_path, 'locations3.1_both_narrative.txt')
    narrative_locations = ""
    if os.path.exists(narrative_path):
        with open(narrative_path, 'r', encoding='utf-8') as f:
            narrative_locations = f.read()

    return narrative_people, names, descriptions,narrative_locations,  addresses, locations, narrative_vul

def create_entity_section_large(entities, title, icon, max_items=12):
    """Create larger entity section with clickable cells that reveal report tags"""
    if not entities:
        content = html.P("No entities found", className="no-data-compact")
    else:
        entity_cards = []
        for i, (entity, count, positions) in enumerate(entities[:max_items]):  
            positions = list(set(positions))
            
            # Create clickable larger entity card
            report_links = [
                dcc.Link(f"R{p}", href=f"/report/mp/{p}", className="report-tag-large")
                for p in sorted(positions)
            ]
            
            entity_cards.append(
                html.Details([
                    html.Summary([
                        html.Span(entity, className="entity-name-large"),
                        html.Span(str(len(positions)), className="entity-count-large")
                    ], className="entity-summary-large"),
                    html.Div(report_links, className="report-tags-dropdown")
                ], className="entity-card-large")
            )
        
        if len(entities) > max_items:
            entity_cards.append(
                html.Div([
                    html.Span(f"+{len(entities) - max_items} more", className="more-entities-large")
                ], className="more-entities-card-large")
            )
            
        content = html.Div(entity_cards, className="entity-grid-large")
    
    return html.Div([
        html.Div([
            html.I(className=f"icon-large {icon}"),
            html.H4(title, className="entity-section-title-large"),
            html.Span(f"{len(entities)}", className="section-count-large")
        ], className="entity-section-header-large"),
        content
    ], className="entity-section-large")

# def patterns_sectionx(df_mp_misperid, df_vp_misperid, case_id, overview=False):
#     """Create a simple patterns and statistics section"""
    
#     patterns = []
    
#     # MP incidents count with expandable list
#     if not df_mp_misperid.empty:
#         mp_report_ids = sorted(df_mp_misperid['reportid'].tolist())
#         patterns.append(create_expandable_pattern("👤", "MP Reports", len(df_mp_misperid), mp_report_ids, "mp"))
    
#     # VP records count with expandable list
#     if not df_vp_misperid.empty:
#         vp_report_ids = sorted(df_vp_misperid['reportid'].tolist())
#         patterns.append(create_expandable_pattern("🚨", "VP Records", len(df_vp_misperid), vp_report_ids, "vp"))
    
#     # Average time missing (no expansion needed)
#     if not df_mp_misperid.empty and 'length_missing_mins' in df_mp_misperid.columns:
#         avg_time = df_mp_misperid['length_missing_mins'].mean()
#         if pd.notna(avg_time):
#             patterns.append(create_simple_pattern("⏱️", "Avg Missing", format_minutes(avg_time)))
    
#     # Longest time missing with link to specific report
#     if not df_mp_misperid.empty and 'length_missing_mins' in df_mp_misperid.columns:
#         valid_times = df_mp_misperid.dropna(subset=['length_missing_mins'])
#         if not valid_times.empty:
#             longest_idx = valid_times['length_missing_mins'].idxmax()
#             longest_report = valid_times.loc[longest_idx]
#             max_time = longest_report['length_missing_mins']
#             report_id = longest_report['reportid']
#             patterns.append(create_expandable_pattern("📅", "Max Missing", format_minutes(max_time), [report_id], "mp"))
    
#     # Most common day with reports on that day
#     if not df_mp_misperid.empty and 'day_reported_missing' in df_mp_misperid.columns:
#         valid_days = df_mp_misperid.dropna(subset=['day_reported_missing'])
#         if not valid_days.empty:
#             common_day = valid_days['day_reported_missing'].mode()
#             if not common_day.empty:
#                 day_name = common_day.iloc[0]
#                 reports_on_day = valid_days[valid_days['day_reported_missing'] == day_name]['reportid'].tolist()
#                 patterns.append(create_expandable_pattern("📆", "Common Day", day_name + " (" + f"in {str(len(reports_on_day))} /{len(df_mp_misperid)})", reports_on_day, "mp"))
    
#     # Build the section content
#     content = []
    
#     patterns_overview = create_pattern_quotes(case_id)
#     # Add Quick Stats section
#     if patterns:
#         content.append(html.Div([
#             html.Div([
#                 html.H4("General Patterns", className="compact-section-title"),
#                 html.Span(f"{len(patterns)}", className="item-count-small")
#             ], className="compact-section-header"),
#             html.Div(patterns, className="stats-horizontal-grid"),
#             patterns_overview
#         ], className="compact-section"))
#     if not overview:
#         if patterns:
#             return  html.Div(patterns, className="stats-horizontal-grid")
    
#     return html.Div(content)



    
def summary_page(case_id):
    try:
        df_mp_misperid = df_mp[df_mp['misperid']==int(case_id)]
        df_vp_misperid = df_vp[df_vp['misper_misperid']==int(case_id)]
        
        narrative_people, names, descriptions, narrative_locations, addresses, locations, narrative_vul = load_case_data(case_id)
        
        if narrative_people is None:
            return html.Div([
                html.Div([
                    html.H1("Case Not Found", className="error-title"),
                    html.P(f"Case {case_id} could not be loaded", className="error-message"),
                    dcc.Link("← Back to Home", href="/", className="btn btn-primary")
                ], className="error-container")
            ], className="error-page")
            
        if narrative_locations is None:
            return html.Div([
                html.Div([
                    html.H1("Case Not Found", className="error-title"),
                    html.P(f"Case {case_id} could not be loaded", className="error-message"),
                    dcc.Link("← Back to Home", href="/", className="btn btn-primary")
                ], className="error-container")
            ], className="error-page")
        
        if narrative_vul is None:
            return html.Div([
                html.Div([
                    html.H1("Case Not Found", className="error-title"),
                    html.P(f"Case {case_id} could not be loaded", className="error-message"),
                    dcc.Link("← Back to Home", href="/", className="btn btn-primary")
                ], className="error-container")
            ], className="error-page")
        
        return html.Div([
            # Header
            html.Div([
                html.H1(f"Case {case_id}", className="case-title"),
                html.Div([
                    html.Span("Association Network Analysis", className="subtitle"),
                    dcc.Link("← Home", href="/", className="btn btn-outline btn-sm"),
                ], className="header-actions")
            ], className="page-header"),
            
            # Main content in single column layout
            html.Div([
                create_person_overview(df_mp_misperid, ['reportid', 'forenames', 'surname', 'ha_address', 'residence_type','label', 'sex', 'dob', 'pob', 'occdesc']),
                # Patterns Section
                
                create_summ_mp_timeline_visualization(patterns_section(df_mp_misperid, df_vp_misperid, case_id), df_mp_misperid, create_theme_analysis_summary(case_id, df_mp_misperid['reportid'].to_list(),df_vp_misperid['reportid'].to_list()), themes_in_reports=True),

                create_association_network_graph( html.Div([
                        # Overview card
                        html.Div([
                            html.Div([
                                html.P(narrative_people if narrative_people.strip() else "No narrative available.", 
                                       className="narrative-text")
                            ], className="card-content")
                        ], className="overview-card")]), pd.read_csv(f"NEW/{case_id}/assosiation_network/graph_network.csv")),
                
                # Vulnerabilities
                html.Details([
                    html.Summary([
                        html.Div([
                            html.H2("Vulnerabilities", className="column-title-main")
                        ], className="dropdown-summary-content"),
                        html.Span("▼", className="dropdown-arrow")
                    ], className="column-header-people dropdown-summary"),
                    html.Div([
                        create_vp_risk_questions_summary(df_vp_misperid),
                        create_mp_risk_questions_summary(df_mp_misperid)
                        
                    ], className="dropdown-content")
                ], className="dropdown-section", open=True),

                # Location Information
                html.Details([
                    html.Summary([
                        html.Div([
                            html.H2("Location Information", className="column-title-main")
                        ], className="dropdown-summary-content"),
                        html.Span("▼", className="dropdown-arrow")
                    ], className="column-header-locations dropdown-summary"),
                    html.Div([                        
                        # Location sections - prominent missing/found table at top
                        create_summ_mp_missing_from_found_locations_map(df_mp_misperid, locations),
                        
                        # html.Div([
                        #     create_entity_section_large(locations, "Other mentioned locations", "📍")
                        # ], className="entities-container-large")
                    ], className="dropdown-content")
                ], className="dropdown-section", open=True)
                
            ], className="main-content-single-column")
            
        ], className="summary-page-single")
        
    except Exception as e:
        return html.Div([
            html.Div([
                html.H1("Error", className="error-title"),
                html.P(f"Error loading case: {str(e)}", className="error-message"),
                dcc.Link("← Back to Home", href="/", className="btn btn-primary")
            ], className="error-container")
        ], className="error-page")

def home_page():
    return html.Div([
        html.Div([
            html.H1("📊 Association Network", className="home-title"),
            html.P("Analyze case reports and entity relationships", className="home-subtitle")
        ], className="home-header"),
        
        html.Div([
            html.Div([
                html.H3("Load Case Analysis", className="card-title"),
                html.Div([
                    dcc.Input(
                        id='case-id-input',
                        type='text',
                        placeholder='Enter case ID...',
                        className="input-field"
                    ),
                    html.Button('Load Case', id='load-button', n_clicks=0, className="btn btn-primary")
                ], className="input-group"),
                html.Div([
                    html.P("💡 Direct URL format:", className="help-label"),
                    html.Code("/summary_people/{case_id}", className="code-example")
                ], className="help-section")
            ], className="load-card")
        ], className="home-content"),
        
        html.Div(id='home-content')
    ], className="home-page")

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)


def display_page(pathname):
    if pathname is None or pathname == '/':
        return home_page()
    elif pathname.startswith("/summary_people/"):
        parts = pathname.split("/")
        if len(parts) >= 3:
            return summary_page(parts[2])
        else:
            return html.Div("Invalid URL format", className="error-card")
    elif pathname.startswith("/report/"):
        parts = pathname.split("/")
        if len(parts) == 4:
            return report_page(parts[2], parts[3])
        else:
            return html.Div("Invalid report URL", className="error-card")
    else:
        return html.Div("404 - Page Not Found", className="error-card")

@app.callback(
    Output('url', 'pathname'),
    [Input('load-button', 'n_clicks')],
    [State('case-id-input', 'value')]
)
def navigate_to_summary(n_clicks, case_id):
    if n_clicks > 0 and case_id:
        return f'/summary_people/{case_id}'
    return dash.no_update


app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Summary/title>
        {%favicon%}
        {%css%}
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

if __name__ == '__main__':
    app.run(debug=True, port=8051)