from rule_based.risk_questions_dicts import vpd_mapping
from rule_based.create_rule_based_summary import CreateSummary, ReadCsvFiles
import pandas as pd
import dash
from dash import dcc, html, Input, Output, callback, State, ALL
read_csv_files = ReadCsvFiles()

def create_question_card(q_n, row):     
    comment_row = row.copy()   
    print("WHROT5", comment_row[f'{q_n}_explanation'])
    comment = comment_row[f'{q_n}_explanation'] if not pd.isna(comment_row[f'{q_n}_explanation']) else "No comment."
    print(comment, "YYYYY")
    answer = 'YES' if str(comment_row[q_n]) == '1' else 'NO'     
    answer_class = 'answer-yes' if answer == 'YES' else 'answer-no'          
    print("SZNIOO", int(q_n.split('_')[1]))
    return html.Div([         
        html.Div([             
            html.Span(f"Q{int(q_n.split('_')[1])}", className="question-number"),             
            html.Span(read_csv_files.risk_questions_dict[int(q_n.split('_')[1])], className="question-text"),             
            html.Span(answer, className=f"answer-badge {answer_class}")         
        ], className="question-header"),         
        html.Div(comment, className="question-comment") if comment != 'No explanation provided' else None     
    ], className="question-card")