from dash import html, dcc
import plotly.graph_objects as go
import plotly.express as px
from rule_based.create_rule_based_summary import CreateSummary, ReadCsvFiles
import pandas as pd
from rule_based.risk_questions_dicts import vpd_mapping
from utils.date_from_report_id import date_from_reportid
def load_question_comments(case_id):
        file_path=f"NEW/{case_id}/vul/vul_explanation_perquestion.txt"
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
            size=16,  # Increased from 10 to 12
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
    
    
    # Load comments from file
    question_comments = load_question_comments(case_id)
    
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
                html.Span("Details", style={
                    'fontSize': '20px',
                    'fontWeight': '800',
                    'color': '#f8f9fa'
                })
            ], style={
                'cursor': 'pointer',
                'padding': '10px',
                'backgroundColor': '#2e85ab',
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
                                date_from_reportid(rid, "mp")
                                # html.A(f"R{str(rid)}", 
                                #       href=f"/report/mp/{rid}", 
                                #       target="_blank", className="report-tag-medium") 
                                if i < 50 else None
                                for i, rid in enumerate(report_ids)
                            ],
                            html.Span(f" (and {len(report_ids)-50} more)" if len(report_ids) > 50 else "")
                        ], className="report-tags-medium"),
                        # Add the comment if available
                        html.Br() if get_question_comment(col) else "",
                        html.Div([
                            html.Strong("Comment 🤖: ", style={'color': '#495057', 'fontSize': '16px'}),
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
                    for col, report_ids in reversed(list(column_to_ids.items()))
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



def create_mp_risk_questions_summary(mp_df_misperid):  
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
       
    fig.add_trace(go.Bar(
        x=counts ,
        y=qs,  # Reverse order for top-down display
        orientation='h',
        marker=dict(
            color='#2e85ab',
            opacity=1,
            line=dict(width=1, color='white')
        ),
        hovertemplate='%{customdata}<extra></extra>',
        text=[csv_files.risk_questions_dict[int(col.split('_')[1])] for col in qs],
        textposition=text_positions,  # List of positions for each bar
        textfont=dict(
            size=16,  # Increased from 10 to 12
            color=text_colors  # List of colors for each bar
        ),
        texttemplate='%{text}',
        customdata=hover_texts,  # Reverse to match y-axis order
        name='Vulnerability Questions'
    ))
    
    
    # Update layout
    fig.update_layout(
        xaxis=dict(
            title="Reports Answering 'Yes' to Each Question",
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
        height=max(600, len(qs) * 60), 
        margin=dict(l=80, r=40, t=80, b=100),  # More bottom margin for rotated labels
        showlegend=False
    )
    
    # Create the graph component
    graph_component = dcc.Graph(
        id='vulnerability-questions-bar',
        figure=fig,
        style={'width': '100%'},
        config={'displayModeBar': True, 'displaylogo': False}
    )    
    
    # Helper function to get first available comment for a question
    def get_first_comment(col, report_ids):
        explanation_col = f"{col}_explanation"
        if explanation_col not in mp_df_misperid.columns:
            return None, None
        
        # Find the first non-empty comment for this question
        for report_id in report_ids:
            comment = mp_df_misperid.loc[mp_df_misperid['reportid'] == report_id, explanation_col]
            if not comment.empty:
                comment_text = comment.iloc[0]
                if pd.notna(comment_text) and str(comment_text).strip():
                    return str(comment_text).strip(), report_id
        return None, None
    
    # Create detailed questions table for reference
    questions_table = html.Div([
        html.Details([
            html.Summary([
                html.Span("Question Details", style={
                    'fontSize': '16px',
                    'fontWeight': '600',
                    'backgroundColor': '#f8f9fa',
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
                            *[ date_from_reportid(rid, "mp")
                                # html.A(f"R{str(rid)}", 
                                #       href=f"/report/mp/{rid}", 
                                #       target="_blank", className="report-tag-medium") 
                                if i < 50 else None
                                for i, rid in enumerate(report_ids)
                            ],
                            html.Span(f" (and {len(report_ids)-50} more)" if len(report_ids) > 50 else "")
                        ], className="report-tags-medium"),
                        # Add the first comment if available
                        html.Br() if get_first_comment(col, report_ids)[0] else "",
                        html.Div([
                            date_from_reportid(get_first_comment(col, report_ids)[1], "mp"),
                            html.Strong("Most Recent Comment: ", style={'color': '#495057', 'fontSize': '16px'}),
                            
                           
                            html.A( get_first_comment(col, report_ids)[0], 
                                  href=f"/report/mp/{ get_first_comment(col, report_ids)[1]}", 
                                  style={'color': "#48515a", 'fontSize': '16px', 'fontStyle': 'italic', 'textDecoration': 'underline'},
                                  target="_blank")
                        ]) if get_first_comment(col, report_ids)[0] else ""
                    ], style={
                        'padding': '10px',
                        'margin': '5px 0',
                        'backgroundColor': 'white',
                        'border': '1px solid #e9ecef',
                        'borderRadius': '4px'
                    })
                    
                    for col, report_ids in reversed(list(column_to_ids.items()))
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
    
def create_mp_risk_questions_summary_combined_concepts(mp_df_misperid, case_id):  
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
       
    fig.add_trace(go.Bar(
        x=counts ,
        y=qs,  # Reverse order for top-down display
        orientation='h',
        marker=dict(
            color='#2e85ab',
            opacity=1,
            line=dict(width=1, color='white')
        ),
        hovertemplate='%{customdata}<extra></extra>',
        text=[csv_files.risk_questions_dict[int(col.split('_')[1])] for col in qs],
        textposition=text_positions,  # List of positions for each bar
        textfont=dict(
            size=16,  # Increased from 10 to 12
            color=text_colors  # List of colors for each bar
        ),
        texttemplate='%{text}',
        customdata=hover_texts,  # Reverse to match y-axis order
        name='Vulnerability Questions'
    ))
    
    
    # Update layout
    fig.update_layout(
        xaxis=dict(
            title="Reports Answering 'Yes' to Each Question",
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
        height=max(600, len(qs) * 60), 
        margin=dict(l=80, r=40, t=80, b=100),  # More bottom margin for rotated labels
        showlegend=False
    )
    
    # Create the graph component
    graph_component = dcc.Graph(
        id='vulnerability-questions-bar',
        figure=fig,
        style={'width': '100%'},
        config={'displayModeBar': True, 'displaylogo': False}
    )    
    
    # Helper function to get first available comment for a question
    def get_first_comment(col, report_ids):
        explanation_col = f"{col}_explanation"
        if explanation_col not in mp_df_misperid.columns:
            return None, None
        
        # Find the first non-empty comment for this question
        for report_id in report_ids:
            comment = mp_df_misperid.loc[mp_df_misperid['reportid'] == report_id, explanation_col]
            if not comment.empty:
                comment_text = comment.iloc[0]
                if pd.notna(comment_text) and str(comment_text).strip():
                    return str(comment_text).strip(), report_id
        return None, None
    
    # Load comments from file
    question_comments = load_question_comments(case_id)
    
    def get_question_comment(col):
        comment = question_comments.get(col, "")
        if comment and comment != "[]":
            return comment
        return None
    
    
    # Create detailed questions table for reference
    questions_table = html.Div([
        html.Details([
            html.Summary([
                html.Span("Details", style={
                    'fontSize': '20px',
                    'fontWeight': '800',
                    'color': '#f8f9fa'
                })
            ], style={
                'cursor': 'pointer',
                'padding': '10px',
                'backgroundColor': '#2e85ab',
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
                                date_from_reportid(rid, "mp")
                                # html.A(f"R{str(rid)}", 
                                #       href=f"/report/mp/{rid}", 
                                #       target="_blank", className="report-tag-medium") 
                                if i < 50 else None
                                for i, rid in enumerate(report_ids)
                            ],
                            html.Span(f" (and {len(report_ids)-50} more)" if len(report_ids) > 50 else "")
                        ], className="report-tags-medium"),
                        
                        # Add the generated comment if available (stacked on top)
                        html.Br() if get_question_comment(col) else "",
                        html.Div([
                            html.Strong("Comment 🤖: ", style={'color': '#495057', 'fontSize': '16px'}),
                            html.Span(get_question_comment(col),
                                   style={'color': "#48515a", 'fontSize': '16px', 'fontStyle': 'italic'})
                        ], style={
                            'padding': '8px 12px',
                            'margin': '8px 0',
                            'backgroundColor': '#e3f2fd',
                            'border': '1px solid #bbdefb',
                            'borderRadius': '6px',
                            'borderLeft': '4px solid #2196f3'
                        }) if get_question_comment(col) else "",
                        
                        # Add the most recent comment if available (below the generated comment)
                        html.Br() if get_first_comment(col, report_ids)[0] and get_question_comment(col) else "",
                        html.Div([
                            html.Strong("Most Recent Comment: ", style={'color': '#495057', 'fontSize': '16px'}),
                           
                            html.A(get_first_comment(col, report_ids)[0], 
                                  href=f"/report/mp/{get_first_comment(col, report_ids)[1]}", 
                                  style={'color': "#48515a", 'fontSize': '16px', 'fontStyle': 'italic', 'textDecoration': 'underline'},
                                  target="_blank"),
                            date_from_reportid(get_first_comment(col, report_ids)[1], "mp")
                        ], style={
                            'padding': '8px 12px',
                            'margin': '8px 0',
                            'backgroundColor': '#fff3e0',
                            'border': '1px solid #ffcc02',
                            'borderRadius': '6px',
                            'borderLeft': '4px solid #ff9800'
                        }) if get_first_comment(col, report_ids)[0] else ""
                    ], style={
                        'padding': '10px',
                        'margin': '5px 0',
                        'backgroundColor': 'white',
                        'border': '1px solid #e9ecef',
                        'borderRadius': '4px'
                    })
                    
                    for col, report_ids in reversed(list(column_to_ids.items()))
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
    column_to_ids = dict(sorted(column_to_ids.items(), key=lambda item: len(item[1]), reverse=False))
    
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
        height=max(500, len(column_to_ids) * 50),  # Dynamic height based on number of vulnerabilities
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
                    'fontSize': '16px',
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
                            html.A(get_first_comment(col, report_ids)[0], 
                                  href=f"/report/vp/{get_first_comment(col, report_ids)[1]}", 
                                  style={'color': '#48515a', 'fontSize': '16px', 'fontStyle': 'italic', 'textDecoration': 'underline'},
                                  )
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
    
def create_vp_risk_questions_summary_concept3(vp_df_misperid, comments_file_path=None):
    binary_columns = vp_df_misperid.columns[-43:-1]
    column_to_ids = {}
    for col in binary_columns:
        ids_with_1 = vp_df_misperid.loc[vp_df_misperid[col] == 1, 'reportid'].tolist()
        column_to_ids[col] = ids_with_1
    
    # Filter out empty results and sort by count
    column_to_ids = {k: v for k, v in column_to_ids.items() if v}
    column_to_ids = dict(sorted(column_to_ids.items(), key=lambda item: len(item[1]), reverse=False))
    
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
    
    # Load comments from text file
    def load_comments_from_file(file_path):
        """Load comments from text file with format: column_name: comment [report_ids]"""
        comments_mapping = {}
        if not file_path:
            return comments_mapping
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or ':' not in line:
                        continue
                    
                    # Split on first colon to separate column name from rest
                    parts = line.split(':', 1)
                    if len(parts) != 2:
                        continue
                    
                    column_name = parts[0].strip()
                    rest = parts[1].strip()
                    
                    # Check if there's content before the brackets or if it's empty []
                    if rest == '[]':
                        comments_mapping[column_name] = None
                    else:
                        # Find the last occurrence of '[' to separate comment from report IDs
                        bracket_index = rest.rfind('[')
                        if bracket_index != -1:
                            comment = rest[:bracket_index].strip()
                            comments_mapping[column_name] = comment if comment else None
                        else:
                            # No brackets found, treat entire rest as comment
                            comments_mapping[column_name] = rest if rest else None
        except FileNotFoundError:
            print(f"Warning: Comments file not found at {file_path}")
        except Exception as e:
            print(f"Error reading comments file: {e}")
        
        return comments_mapping
    
    # Load the comments mapping
    comments_mapping = load_comments_from_file(comments_file_path)
    
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
        height=max(500, len(column_to_ids) * 50),  # Dynamic height based on number of vulnerabilities
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
    
    # Helper function to get comment from the loaded mapping
    def get_comment_from_file(col):
        """Get comment for a vulnerability from the loaded comments mapping"""
        return comments_mapping.get(col, None)
    
    # Create detailed vulnerabilities table for reference
    vulnerabilities_table = html.Div([
        html.Details([
            html.Summary([
                html.Span("Vulnerability Details", style={
                    'fontSize': '20px',
                    'fontWeight': '600',
                    'color': '#f8f9fa'
                })
            ], style={
                'cursor': 'pointer',
                'padding': '10px',
                'backgroundColor': '#db3545',
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
                                html.A(f"R{str(rid)}", 
                                      href=f"/report/vp/{rid}", 
                                      target="_blank", className="report-tag-medium") 
                                if i < 50 else None
                                for i, rid in enumerate(report_ids)
                            ],
                            html.Span(f" (and {len(report_ids)-50} more)" if len(report_ids) > 50 else "")
                        ], className="report-tags-medium"),
                        # Add the comment from file if available
                        html.Div([
                            html.Strong("Comment 🤖: ", style={'color': '#495057', 'fontSize': '16px'}),
                            html.Span(get_comment_from_file(col), 
                                     style={'color': '#48515a', 'fontSize': '16px', 'fontStyle': 'italic'})
                        ]) if get_comment_from_file(col) else ""
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