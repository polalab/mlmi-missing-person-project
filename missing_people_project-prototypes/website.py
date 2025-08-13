import dash
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
from rule_based.create_rule_based_summary import CreateSummary, ReadCsvFiles
df_mp = pd.read_csv('DATA/mp.csv')
df_vp = pd.read_csv('DATA/vp.csv')
df_vp.rename(columns={"VPD_NOMINALINCIDENTID_PK": "reportid"}, inplace=True)
df_phys = pd.read_csv('DATA/phys.csv')
df_chr = pd.read_csv('DATA/chr_.csv')
read_csv_files = ReadCsvFiles()

qs_comments_df = read_csv_files.qs_comments_df

dict_dfs = {
    "mp": df_mp,
    "vp": df_vp,
    "phys": df_phys, 
    "chr": df_chr}


print(df_vp.columns.tolist)


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

def main_page_layout():
        return html.Div([
            html.H1("Misperids"),
            html.Ul([
                html.Li(dcc.Link(misperid, href=f"/summaries/{misperid}"))
                for misperid in  df_mp['misperid'].dropna().unique()
            ])
        ])
    # category_options = [{'label': val, 'value': val} for val in df_mp['misperid'].dropna().unique()]
    # return html.Div([
    #     html.H2("Main Page: Select a Category"),
    #     dcc.Dropdown(
    #         id='category-dropdown',
    #         options=category_options,
    #         placeholder="Choose a category"
    #     ),
    #     html.Div(id='category-output', style={"marginTop": "20px"})
    # ])


def report_page(type, reportid):
    try:
        df = dict_dfs[type]
    except (ValueError):
        return html.Div("Invalid type.")
    try:
        row = df[df['reportid'] == int(reportid)].squeeze()
    except (ValueError, KeyError):
        return html.Div("Invalid report ID.")

    if row.empty:
        return html.Div("Report not found.")

    content = []
    content.append(html.H2(f"Report ID: {reportid}"))
    if type =="mp":
        for col in df.columns[0:-25]:
            content.append(html.Div([
                html.H4(str(col)),
                html.P(str(row[col]))
            ]))
        q_n = 1
        for col in df.columns[-25::]:
            
            comment_row = qs_comments_df[(qs_comments_df['reportid']==int(reportid)) & (qs_comments_df['questionid']==q_n)]
            
            comment = str(comment_row.iloc[0]['mcomment']) if not (comment_row.empty or  str(comment_row.iloc[0]['mcomment'])=='nan') else 'no explanation given'
            print("XXX",col, comment_row)
            content.append(html.Div([
                html.H4(read_csv_files.risk_questions_dict[q_n] + ": " + ('YES' if str(row[col])=='1' else 'NO')),
                html.P('explanation: ' + comment)]))
                
            q_n+=1
        
        content.append(html.Br())
        content.append(dcc.Link("Back to home", href="/"))
        return html.Div(content)
    else:
        return html.Div([
            html.H2(f"Report ID: {reportid}"),
            html.Div([
                html.Div([
                    html.H4(str(col)),
                    html.P(str(row[col]))
                ]) for col in df.columns
            ]),
        ])

# App layout with URL routing
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# Callback to render pages
@app.callback(Output('page-content', 'children'), Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/':
        return html.Div([
            html.H1("Report Type"),
            html.Ul([
                html.Li(dcc.Link(type_name, href=f"/reports/{type_name}"))
                for type_name in dict_dfs
            ])
        ])
    
    elif pathname.strip("/").split("/")[-1] in dict_dfs:
        type_name =pathname.strip("/").split("/")[-1]
        return html.Div([
            html.H1("Reports"),
            html.Ul([
                html.Li(dcc.Link(reportid, href=f"/report/{type_name}/{reportid}"))
                for reportid in dict_dfs[type_name]["reportid"].tolist()
            ])
        ])
    elif pathname.startswith("/summaries/"):
        misperid = int(pathname.strip('/').split('/')[-1])
        summary_creator = CreateSummary(misperid)
        
        col_mapping = {'vpd_forename': 'forenames', 'vpd_surname': 'surname'} 
        div_basic = [html.H1("\nBasic Information\n"),
            summary_creator.extract_categorical_common("other", ['forenames', 'surname'], 'reportid', desc='Name: ', other_df=summary_creator.concat_mp_vpd(col_mapping, ['forenames', 'surname', 'reportid', 'source']))[1],
            
            summary_creator.extract_categorical_common("vp", ['vpd_maiden_name'], 'vpd_nominalincidentid_pk', desc='Maiden name: ')[1],
            summary_creator.extract_categorical_common("vp", ['vpd_knownas'], 'vpd_nominalincidentid_pk', 'Also known as: ')[1],
            summary_creator.extract_categorical_common("other", ['sex'], 'reportid', 'Sex/gender: ', other_df=summary_creator.concat_mp_vpd({'vpd_persongender': 'sex'}, ['sex'], treat_equal={'F': 'Female', 'M': 'Male'}))[1],
            summary_creator.extract_categorical_common("vp", ['vpd_personethnicappearance'], 'vpd_nominalincidentid_pk', 'Appearance: ')[1],
            summary_creator.extract_categorical_common("mp", ['dob'], 'reportid', 'Date of Birth: ')[1],
            summary_creator.extract_categorical_common("vp", ['vpd_placeofbirth'],'vpd_nominalincidentid_pk', 'Place of birth: ' )[1],
            summary_creator.extract_categorical_common("other", ['occdesc'], 'reportid', 'Occupation: ',  other_df=summary_creator.concat_mp_vpd({'vpd_occupation': 'occdesc'}, ['occdesc']))[1],

            html.Div([summary_creator.extract_categorical_common("vp", ['vpd_personlanguage'], 'vpd_nominalincidentid_pk', 'Language: ')[1],
            summary_creator.extract_categorical_common("vp", ['vpd_interpreterreqid_fk'], 'vpd_nominalincidentid_pk', 'Interpreter ID: ')[1]])
        ]

        div_vur = [
            html.H1("\nVulnerabilities\n"),
            html.H4("Total missing person incidents: "+ str(len(summary_creator.mp_df_misperid)) + '\n'),
            html.H4("Total vulnerable person reports: "+ str(len(summary_creator.vp_df_misperid)) + '\n'),
        ]

        labels_results, html_labels = summary_creator.extract_categorical_common("mp", ['label'], 'reportid', 'Previously assigned labels: ')
        labels = labels_results['label'].tolist() # Store previously assigned labels for later usage
        div_vur.append(html_labels)
        
        
        # summary_creator.generate_risk_summary("mp")
        div_vur.append(summary_creator.report_disabilities("vp"))
        
        if 'Child' in labels:
            div_vur.append(summary_creator.extract_categorical_common("vp", ['vpd_childprotection'], 'vpd_nominalincidentid_pk', "Involvement in or concern with child protection services: ")[1])
            div_vur.append(summary_creator.extract_categorical_common("vp", ['vpd_chsno'], 'vpd_nominalincidentid_pk', "Child hearing system: ")[1])
        div_vur.append(summary_creator.create_mp_risk_questions_summary())
        div_vur.append(summary_creator.create_vp_risk_questions_summary())
        div_vur.append(summary_creator.report_with_all_ids("vp", 'vpd_threepointtest', 'vpd_nominalincidentid_pk', 'Three point test results: '))
              
        div_loc = [ html.H1("\nLocations\n"),
                   summary_creator.create_summ_mp_home_locations(),
                   summary_creator.create_summ_mp_missing_from_found_locations(),
                   summary_creator.extract_categorical_common("other", ['pob'], 'reportid', 'Place of brith: ', other_df=summary_creator.concat_mp_vpd({'vpd_placeofbirth': 'pob'}, ['pob']))[1]]

        div_asossiations = [html.H1("\nAssociation Network\n"),
                summary_creator.report_with_all_ids("mp", 'reported_missing_by', 'reportid', 'People who reported disappearance: '),
                summary_creator.report_with_all_ids("vp", 'vpd_consentname', 'vpd_nominalincidentid_pk', 'People who gave consent to add a record to VPD: ')
                            ]
        
        div_trends = [
            summary_creator.extract_categorical_common("mp", ['day_reported_missing'], 'reportid', "Day of a week missing: ")[1]
        ]
        return html.Div([html.H1(f"\nSummary of records for missing person with ID {summary_creator.misperid}\n"), 
                         html.Div(div_basic,  className="div-box") , html.Div(div_vur,  className="div-box") , html.Div(div_loc,  className="div-box") , html.Div(div_asossiations,  className="div-box"), html.Div(div_trends,  className="div-box")], className="div-main")
        
        
    elif pathname.startswith("/report/"):
        parts = pathname.split("/")
        if len(parts) == 4:
            _, _, report_type, report_id = parts
            return report_page(report_type, report_id)
        else:
            return html.Div("Invalid report URL.")
    elif pathname == "/main":
        
        
        return main_page_layout()
    else:
        return html.Div("404 - Page not found")

# Run server
if __name__ == '__main__':
    app.run(debug=True, port=8050)
