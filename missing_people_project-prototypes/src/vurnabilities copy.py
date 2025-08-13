from dash import html, dcc
import plotly.graph_objects as go
import plotly.express as px
from rule_based.create_rule_based_summary import CreateSummary, ReadCsvFiles
import pandas as pd
from rule_based.risk_questions_dicts import vpd_mapping
from utils.date_from_report_id import date_from_reportid


def create_mp_risk_questions_summary_concept3(mp_df_misperid, case_id):  
    csv_files = ReadCsvFiles()
    binary_columns = [f'q_{i}' for i in range(1, 26)]
    
    column_to_ids = {}
    for col in binary_columns:
        ids_with_1 = mp_df_misperid.loc[mp_df_misperid[col] == 1, 'reportid'].tolist()
        column_to_ids[col] = ids_with_1
   
    # Filter out empty results and sort by count
    column_to_ids = {k: v for k, v in column_to_ids.items() if v}
    
    column_to_ids = dict(sorted(column_to_ids.items(), key=lambda item: len(item[1]), reverse=False))
    if not column_to_ids:
        return html.Div([
            html.Div([
                html.I("⚠️", className="icon-medium"),
                html.H3("Vulnerability Questions", className="entity-section-title"),
                html.P("No vulnerability indicators found", className="no-data-compact")
            ], className="entity-section empty-section")
        ])
    
    # Calculate total reports for percentage
    total_reports = len(mp_df_misperid)
    
    # Prepare data for bar plot
    questions = []
    question_texts = []
    counts = []
    qs = []
    percentages = []
    report_ids_lists = []
    hover_texts = []
    
    
    for col, report_ids in column_to_ids.items():
       
        q_n = int(col.split('_')[1])
        question_text = csv_files.risk_questions_dict[int(q_n)]
        count = len(report_ids)
       
        proportion = f"{count}/{total_reports}"
        # Truncate question text for y-axis labels (keep first 40 characters)
        short_question = question_text[:40] + "..." if len(question_text) > 40 else question_text
        
        questions.append(f"Q{q_n}")
        question_texts.append(short_question)
        counts.append(count)
        qs.append(col)
        percentages.append(proportion)
        report_ids_lists.append(report_ids)
        
        # Create hover text with full question and report IDs
        report_ids_text = ", ".join([str(rid) for rid in report_ids[:10]])  # Show first 10 report IDs
        if len(report_ids) > 10:
            report_ids_text += f" (and {len(report_ids) - 10} more)"
        
        hover_text = f"<b>{question_text}</b><br>" \
                    f"Count: {proportion}" \
                    f" Report IDs: {report_ids_text}"
        hover_texts.append(hover_text)
    
    # Create the bar plot
    fig = go.Figure()
    
    # Add bars with color coding based on percentage
    colors = []
    for pct in percentages:
        colors.append('#d63384')  # High risk - red
       
    # Create single trace but with mixed text positioning
    max_count = max(counts) if counts else 1
    
    # Determine text positions and colors for each bar
    text_positions = []
    text_colors = []
    
    for count in counts:
        if count < max_count * 0.4:  # Less than 40% - put text outside
            text_positions.append('outside')
            text_colors.append('black')
        else:  # 40% or more - put text inside
            text_positions.append('inside')
            text_colors.append('white')
    
    # Add single trace with all bars
    fig.add_trace(go.Bar(
        x=counts,
        y=qs,
        orientation='h',
        marker=dict(
            color='#2e85ab',
            opacity=1,
            line=dict(width=1, color='white')
        ),
        hovertemplate='%{customdata}<extra></extra>',
        customdata=hover_texts,
        name='Vulnerability Questions',
        text=[csv_files.risk_questions_dict[int(col.split('_')[1])] for col in qs],
        textposition=text_positions,  # List of positions for each bar
        textfont=dict(
            size=12,  # Increased from 10 to 12
            color=text_colors  # List of colors for each bar
        ),
        texttemplate='%{text}',
        cliponaxis=False,
        showlegend=False
    ))
    
    
    # Update layout
    fig.update_layout(
        title=dict(
            text="Vulnerability Questions Analysis",
            x=0.5,
            font=dict(size=16, color='#2c3e50')
        ),
        xaxis=dict(
            title="Number of Reports",
            showgrid=False,
            tickangle=45 if len(questions) >25 else 0,  # Angle labels if many questions
            categoryorder='array',
            categoryarray=questions  # Maintain sorted order
        ),
        yaxis=dict(
            title="Questions",
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(0,0,0,0.1)',
            zeroline=True,
            zerolinecolor='rgba(0,0,0,0.2)'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=max(600, len(qs) * 60),  # Increased bar height: 40 -> 60 pixels per bar, min height 500 -> 600
        margin=dict(l=80, r=200, t=80, b=100),  # More right margin for outside text
        showlegend=False
    )
    
    # Create the graph component
    graph_component = dcc.Graph(
        id='vulnerability-questions-bar',
        figure=fig,
        style={'width': '100%'},
        config={'displayModeBar': True, 'displaylogo': False}
    )    
    
    # Helper function to read comments from text file
    def load_question_comments(file_path=f"NEW/{case_id}/vul/vul_explanation_perquestion.txt"):
        """Load question comments from text file"""
        question_comments = {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the text file format
            lines = content.strip().split('\n')
            current_question = None
            current_comment = ""
            
            for line in lines:
                if line.startswith('q_') and ':' in line:
                    # Save previous question if exists
                    if current_question and current_comment.strip():
                        question_comments[current_question] = current_comment.strip()
                    
                    # Start new question
                    parts = line.split(':', 1)
                    current_question = parts[0].strip()
                    comment_part = parts[1].strip() if len(parts) > 1 else ""
                    
                    # Remove report IDs in brackets at the end
                    if comment_part.endswith(']') and '[' in comment_part:
                        bracket_pos = comment_part.rfind('[')
                        comment_part = comment_part[:bracket_pos].strip()
                    
                    current_comment = comment_part
                else:
                    # Continue multiline comment
                    if current_question:
                        current_comment += " " + line.strip()
            
            # Save last question
            if current_question and current_comment.strip():
                question_comments[current_question] = current_comment.strip()
                
        except FileNotFoundError:
            print(f"Warning: {file_path} not found")
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            
        return question_comments
    
    # Load comments from file
    question_comments = load_question_comments()
    
    # Helper function to get comment for a question
    def get_question_comment(col):
        comment = question_comments.get(col, "")
        if comment and comment != "[]":
            return comment
        return None
    
    # Create detailed questions table for reference
    questions_table = html.Div([
        html.Details([
            html.Summary([
                html.Span("Question Details", style={
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
                        html.Strong(f"Q{int(col.split('_')[1])}: "),
                        html.Span(csv_files.risk_questions_dict[int(col.split('_')[1])]),
                        html.Br(),
                        html.Small([
                            "Reports: ",
                            *[
                                html.A(f"R{str(rid)}", 
                                      href=f"/report/mp/{rid}", 
                                      target="_blank", className="report-tag-medium") 
                                if i < 50 else None
                                for i, rid in enumerate(report_ids)
                            ],
                            html.Span(f" (and {len(report_ids)-50} more)" if len(report_ids) > 50 else "")
                        ], className="report-tags-medium"),
                        # Add the comment if available
                        html.Br() if get_question_comment(col) else "",
                        html.Div([
                            html.Strong("Analysis: ", style={'color': '#495057', 'fontSize': '16px'}),
                            html.Span(get_question_comment(col), 
                                  style={'color': "#48515a", 'fontSize': '16px', 'fontStyle': 'italic'})
                        ]) if get_question_comment(col) else ""
                    ], style={
                        'padding': '10px',
                        'margin': '5px 0',
                        'backgroundColor': 'white',
                        'border': '1px solid #e9ecef',
                        'borderRadius': '4px'
                    })
                    for col, report_ids in column_to_ids.items()
                ])
            ], style={'padding': '10px'})
        ])
    ])
    
    return html.Div([
        html.Div([
            html.H3("Vulnerability Questions from MP Database", className="entity-section-title"),
        ], className="entity-section-header"),
        html.Div([
            graph_component,
            questions_table
        ])
    ], className="entity-section")


def create_vp_risk_questions_summary(vp_df_misperid):
    binary_columns = vp_df_misperid.columns[-43:-1]
    column_to_ids = {}
    for col in binary_columns:
        ids_with_1 = vp_df_misperid.loc[vp_df_misperid[col] == 1, 'reportid'].tolist()
        column_to_ids[col] = ids_with_1
    
    # Filter out empty results and sort by count
    column_to_ids = {k: v for k, v in column_to_ids.items() if v}
    column_to_ids = dict(sorted(column_to_ids.items(), key=lambda item: len(item[1]), reverse=True))
    
    if not column_to_ids:
        return html.Div([
            html.Div([
                html.I("⚠️", className="icon-medium"),
                html.H3("VPD Vulnerabilities", className="entity-section-title"),
                html.P("No VPD vulnerability indicators found", className="no-data-compact")
            ], className="entity-section empty-section")
        ])
    
    # Calculate total reports for percentage
    total_reports = len(vp_df_misperid)
    
    # Prepare data for bar plot
    vulnerabilities = []
    vulnerability_texts = []
    counts = []
    cols = []
    percentages = []
    report_ids_lists = []
    hover_texts = []
    
    for col, report_ids in column_to_ids.items():
        vulnerability_text = vpd_mapping[col]
        count = len(report_ids)
        
        proportion = f"{count}/{total_reports}"
        # Truncate vulnerability text for y-axis labels (keep first 50 characters)
        short_vulnerability = vulnerability_text[:50] + "..." if len(vulnerability_text) > 50 else vulnerability_text
        
        vulnerabilities.append(col)
        vulnerability_texts.append(short_vulnerability)
        counts.append(count)
        cols.append(vulnerability_text)
        percentages.append(proportion)
        report_ids_lists.append(report_ids)
        
        # Create hover text with full vulnerability and report IDs
        report_ids_text = ", ".join([str(rid) for rid in report_ids[:10]])  # Show first 10 report IDs
        if len(report_ids) > 10:
            report_ids_text += f" (and {len(report_ids) - 10} more)"
        
        hover_text = f"<b>{vulnerability_text}</b><br>" \
                    f"Count: {proportion}<br>" \
                    f"Report IDs: {report_ids_text}"
        hover_texts.append(hover_text)
    
    # Create the bar plot
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=counts,
        y=cols,  # Use column names for y-axis
        orientation='h',
        marker=dict(
            color='#dc3545',  # Red color for vulnerabilities
            opacity=1,
            line=dict(width=1, color='white')
        ),
        hovertemplate='%{customdata}<extra></extra>',
        customdata=hover_texts,
        name='VPD Vulnerabilities'
    ))
    
    # Update layout
    fig.update_layout(
        xaxis=dict(
            title="Vulnerability Reporting Frequency",
            showgrid=False,
            tickangle=45 if len(vulnerabilities) > 25 else 0,
            categoryorder='array',
            categoryarray=vulnerabilities
        ),
        yaxis=dict(
            title="Vulnerabilities",
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(0,0,0,0.1)',
            zeroline=True,
            zerolinecolor='rgba(0,0,0,0.2)'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=max(500, len(column_to_ids) * 25),  # Dynamic height based on number of vulnerabilities
        margin=dict(l=80, r=40, t=80, b=100),
        showlegend=False
    )
    
    # Create the graph component
    graph_component = dcc.Graph(
        id='vpd-vulnerabilities-bar',
        figure=fig,
        style={'width': '100%'},
        config={'displayModeBar': True, 'displaylogo': False}
    )
    
    # Helper function to get first available comment for a vulnerability
    def get_first_comment(col, report_ids):
        explanation_col = f"vpd_nominalsynopsis"
        if explanation_col not in vp_df_misperid.columns:
            return None, None
        
        # Find the first non-empty comment for this vulnerability
        for report_id in report_ids:
            comment = vp_df_misperid.loc[vp_df_misperid['reportid'] == report_id, explanation_col]
            if not comment.empty:
                comment_text = comment.iloc[0]
                if pd.notna(comment_text) and str(comment_text).strip():
                    return str(comment_text).strip(), report_id
        return None, None
    
    # Create detailed vulnerabilities table for reference
    vulnerabilities_table = html.Div([
        html.Details([
            html.Summary([
                html.Span("Vulnerability Details", style={
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
                        html.Strong(f"{vpd_mapping[col]} "),
                       
                        html.Br(),
                        html.Small([
                            *[
                                date_from_reportid(rid, "vp")
                                # html.A(f"R{str(rid)}", 
                                #       href=f"/report/vp/{rid}", 
                                #       target="_blank", className="report-tag-medium") 
                                if i < 50 else None
                                for i, rid in enumerate(report_ids)
                            ],
                            html.Span(f" (and {len(report_ids)-50} more)" if len(report_ids) > 50 else "")
                        ], className="report-tags-medium"),
                        # Add the first comment if available
                        html.Div([
                            html.Strong("Last available synopsis: ", style={'color': '#495057', 'fontSize': '16px'}),
                            
                            
                             date_from_reportid({get_first_comment(col, report_ids)[1]}, "vp")
                            # html.A(get_first_comment(col, report_ids)[0], 
                            #       href=f"/report//}", 
                            #       style={'color': '#48515a', 'fontSize': '16px', 'fontStyle': 'italic', 'textDecoration': 'underline'},
                            #       )
                        ]) if get_first_comment(col, report_ids)[0] else ""
                    ], style={
                        'padding': '10px',
                        'margin': '5px 0',
                        'backgroundColor': 'white',
                        'border': '1px solid #e9ecef',
                        'borderRadius': '4px'
                    })
                    for col, report_ids in column_to_ids.items()
                ])
            ], style={'padding': '10px'})
        ])
    ])
    
    return html.Div([
        html.Div([
            html.H3("VPD Vulnerabilities", className="entity-section-title"),
            html.Span(f"{len(column_to_ids)} vulnerabilities", className="section-count")
        ], className="entity-section-header"),
        html.Div([
            graph_component,
            vulnerabilities_table
        ])
    ], className="entity-section")