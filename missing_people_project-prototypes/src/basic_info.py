import pandas as pd
from collections import Counter
from dash import html, dcc
from utils.date_from_report_id import date_from_reportid
def create_person_overview(df, columns_list):
    """
    Create a comprehensive person overview from dataframe columns.
    
    Parameters:
    df (pd.DataFrame): The dataframe containing person data
    columns_list (list): List of columns to analyze for the person
    
    Returns:
    html.Div: Dash HTML component containing formatted person overview
    """
    
    # Filter dataframe to only include specified columns
    person_df = df[columns_list].copy()
    
    # Container for all sections
    sections = []
    
    # Header
    sections.append(
        html.H2(
            "Person Overview",
            style={
                'textAlign': 'center',
                'color': '#2c3e50',
                'borderBottom': '2px solid #3498db',
                'paddingBottom': '4px',
                'marginBottom': '15px',
                'fontSize': '24px',
                'fontWeight': 'bold',
                'marginTop': '0px'
            }
        )
    )
    
    # Helper function to create report link
    def create_report_link(report_id):
        # return html.A(
        #     f"#{report_id}",
        #     href=f"/report/{report_id}",
        #     style={
        #         'color': '#3498db',
        #         'textDecoration': 'none',
        #         'fontWeight': 'normal'
        #     },
        #     target='_blank'
        # )
        return date_from_reportid (report_id, "mp")

    
    
    # Helper function to get value counts and report links
    def get_value_summary(column_name):
        if column_name not in person_df.columns:
            return []
        
        # Handle date formatting for dob column
        if column_name == 'dob':
            # Convert to datetime and format as date only (day month year)
            formatted_values = []
            for value in person_df[column_name].dropna():
                try:
                    # Try to parse as datetime and format as date
                    if pd.notna(value):
                        date_obj = pd.to_datetime(value)
                        formatted_date = date_obj.strftime('%d %B %Y')
                        formatted_values.append(formatted_date)
                except:
                    # If parsing fails, use original value
                    formatted_values.append(str(value))
            
            # Get value counts of formatted dates
            value_counts = Counter(formatted_values)
        else:
            # Get value counts normally for other columns
            value_counts = Counter(person_df[column_name].dropna())
        
        summaries = []
        for value, count in value_counts.items():
            if value and 'reportid' in person_df.columns:
                # For dob, we need to find the original value to get the correct report ID
                if column_name == 'dob':
                    # Find records that match this formatted date
                    matching_records = []
                    for idx, orig_value in enumerate(person_df[column_name].dropna()):
                        try:
                            if pd.notna(orig_value):
                                date_obj = pd.to_datetime(orig_value)
                                formatted_date = date_obj.strftime('%d %B %Y')
                                if formatted_date == value:
                                    matching_records.append(person_df[person_df[column_name] == orig_value])
                        except:
                            if str(orig_value) == value:
                                matching_records.append(person_df[person_df[column_name] == orig_value])
                    
                    if matching_records:
                        # Get most recent report ID from matching records
                        most_recent_id = matching_records[-1]['reportid'].iloc[-1]
                    else:
                        continue
                else:
                    # Get most recent report ID for this value normally
                    records = person_df[person_df[column_name] == value]
                    most_recent_id = records['reportid'].iloc[-1]
                
                # Create the summary text
                if count > 1:
                    summary_text = [
                        html.Span(value, style={'fontWeight': 'bold', 'color': '#e74c3c'}),
                        html.Span(' ('),
                        create_report_link(most_recent_id),
                        html.Span(f') (reported {count} times)')
                    ]
                else:
                    summary_text = [
                        html.Span(value, style={'fontWeight': 'bold', 'color': '#e74c3c'}),
                        html.Span(' ('),
                        create_report_link(most_recent_id),
                        html.Span(')')
                    ]
                
                summaries.append(summary_text)
        
        return summaries
    
    # Helper function to create one-line sections
    def create_section_line(label, summaries):
        if not summaries:
            return None
        
        line_content = [html.Span(f"{label}: ", style={'fontWeight': 'bold', 'color': '#34495e'})]
        
        for i, summary in enumerate(summaries):
            if i > 0:
                line_content.append(html.Span(', also reported as '))
            line_content.extend(summary)
        
        return html.Div(
            line_content,
            style={
                'fontSize': '16px',
                'marginBottom': '8px',
                'lineHeight': '1.4',
                'color': '#2c3e50'
            }
        )
    
    # Extract unique forenames
    forename_summaries = get_value_summary('forenames')
    forename_line = create_section_line("Forenames", forename_summaries)
    if forename_line:
        sections.append(forename_line)
    
    # Extract unique surnames
    surname_summaries = get_value_summary('surname')
    surname_line = create_section_line("Surnames", surname_summaries)
    if surname_line:
        sections.append(surname_line)
    
    # Extract unique sex
    sex_summaries = get_value_summary('sex')
    sex_line = create_section_line("Sex", sex_summaries)
    if sex_line:
        sections.append(sex_line)
    
    # Extract unique date of birth
    dob_summaries = get_value_summary('dob')
    dob_line = create_section_line("Date of Birth", dob_summaries)
    if dob_line:
        sections.append(dob_line)
    
    # Extract unique place of birth
    pob_summaries = get_value_summary('pob')
    pob_line = create_section_line("Place of Birth", pob_summaries)
    if pob_line:
        sections.append(pob_line)

    # Extract unique labels
    label_summaries = get_value_summary('label')
    label_line = create_section_line("Labels", label_summaries)
    if label_line:
        sections.append(label_line)
    
    # Extract unique occupations
    occupation_summaries = get_value_summary('occdesc')
    occupation_line = create_section_line("Occupations", occupation_summaries)
    if occupation_line:
        sections.append(occupation_line)
    
    # Extract unique residence types
    residence_summaries = get_value_summary('residence_type')
    residence_line = create_section_line("Residence Types", residence_summaries)
    if residence_line:
        sections.append(residence_line)
    
    # Handle addresses
    address_summaries = get_value_summary('ha_address')
    address_line = create_section_line("Home Address", address_summaries)
    if address_line:
        sections.append(address_line)
    
    # Return the complete overview as a Dash HTML Div
    return html.Div(
        sections,
        style={
            'padding': '15px',
            'border': '1px solid #bdc3c7',
            'borderRadius': '4px',
            'backgroundColor': 'white',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
            'fontFamily': 'Arial, sans-serif',
            'width': '100%',
            'margin': '0'
        }
    )