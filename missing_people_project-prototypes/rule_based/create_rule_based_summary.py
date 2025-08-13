import pandas as pd
from rule_based.risk_questions_dicts import vpd_mapping, risk_assessment_questions
from datetime import datetime
from dash import html, dcc

@pd.api.extensions.register_dataframe_accessor("clean")
class CleanAccessor:
    def __init__(self, pandas_object):
        self._obj = pandas_object

    def lowercase_headers(self):
        """
        Lowercase all column headers, replace dots with underscores.
        """
        columns = self._obj.columns.str.strip().str.lower()
        columns = columns.str.replace(".", "_")
        self._obj.columns = columns
        return self._obj  
    
    def strip_strings(self):
        """
        Strip leading/trailing whitespace from all string columns.
        """
        self._obj = self._obj.apply(
            lambda col: col.str.strip() if col.dtype == "object" or pd.api.types.is_string_dtype(col) else col
        )
        return self._obj
    
class ReadCsvFiles:
    def __init__(self):
        self.mp_df = self.read_mp_df()
        self.vp_df = self.read_vpd_df()
        self.chr_df = self.read_chr_df()
        self.phys_df = self.read_phys_df()
        self.qs_comments_df = self.read_qs_comments_df()
        
        self.risk_questions_dict = risk_assessment_questions
        self.vpd_statements_dict = vpd_mapping

    def read_mp_df(self):
        mp_df = pd.read_csv('./DATA/mp.csv', encoding='utf-8')
        mp_df = mp_df.clean.lowercase_headers().clean.strip_strings()

        mp_df['dob'] = pd.to_datetime(mp_df['dob'])
        mp_df['missing_since'] = pd.to_datetime(mp_df['missing_since'])
        mp_df['date_reported_missing'] = pd.to_datetime(mp_df['date_reported_missing'])
        mp_df['whentraced'] = pd.to_datetime(mp_df['whentraced'])
        mp_df.loc[:, 'source'] = 'mp'
        
        return mp_df

    def read_vpd_df(self):
        vp_df = pd.read_csv('./DATA/vp.csv', encoding='utf-8')
        vp_df = vp_df.clean.lowercase_headers().clean.strip_strings()
        vp_df.loc[:, 'source'] = 'vp'
        print(vp_df['vpd_lastupdatedon_1'][0])
        vp_df['vpd_createdon'] = pd.to_datetime(
            vp_df['vpd_createdon'].str.replace('Z\[UTC\]', '', regex=True), format='mixed'
        )
        vp_df['vpd_createdon_1'] = pd.to_datetime(
            vp_df['vpd_createdon_1'].str.replace('Z\[UTC\]', '', regex=True), format='mixed'
        )
        vp_df['vpd_lastupdatedon_1'] = pd.to_datetime(
            vp_df['vpd_lastupdatedon_1'].str.replace('Z\[UTC\]', '', regex=True), format='mixed'
        )
    
        vp_df.loc[:, 'source'] = 'vp'
        return vp_df
    
    def read_chr_df(self):
        chr_df = pd.read_csv('./DATA/chr_.csv')
        chr_df.clean.lowercase_headers().clean.strip_strings()
        chr_df['contactdate'] = pd.to_datetime(
            chr_df['contactdate'], format='mixed'
        )
        return chr_df
    
    def read_phys_df(self):
        phys_df = pd.read_csv('./DATA/phys.csv')
        phys_df.clean.lowercase_headers().clean.strip_strings()

        return phys_df
    
    def read_qs_comments_df(self):
        qs_comments_df =  pd.read_csv('./DATA/qs_comments.csv')
        qs_comments_df.clean.lowercase_headers().clean.strip_strings()
        return qs_comments_df
        


class CreateSummary:
    def __init__(self, misperid):
        self.csv_files = ReadCsvFiles()
        self.summ_file = open('summary_' + str(misperid)+'.txt', "w+")
        
        self.misperid = misperid
        self.mp_df_misperid = self.extract_for_misperid(self.csv_files.mp_df, 'misperid', misperid)
        self.mp_df_misperid.sort_values(by="missing_since",  ascending=False, inplace=True)

        self.vp_df_misperid = self.extract_for_misperid(self.csv_files.vp_df, 'misper_misperid', misperid)
        self.vp_df_misperid.sort_values(by="vpd_createdon",   ascending=False, inplace=True)

        self.phys_df_misperid = self.extract_for_misperid(self.csv_files.phys_df, 'misperid', misperid)
        self.qs_comments_df_misperid = self.extract_for_misperid(self.csv_files.qs_comments_df, 'misperid', misperid)
        
        if len(self.vp_df_misperid['vpd_nominalid_fk'].drop_duplicates()) > 1:
            raise ValueError("Wrong extraction - duplicates in vp dataframe.")
        nominalid_fk = self.vp_df_misperid['vpd_nominalid_fk'].drop_duplicates().to_list()[0]
        
        self.chr_df_misperid = self.extract_for_misperid(self.csv_files.chr_df, 'nominalid_fk', nominalid_fk)

        
    def extract_for_misperid(self, df, col, val):
        try:
            return df[df[col]==val]
        except:
            raise ValueError("Wrong column of value passed.")
        
    def get_df_by_type(self, df_type: str, other_df=None):
        if df_type == "mp":
            return self.mp_df_misperid
        elif df_type == "vp":
            return self.vp_df_misperid
        elif df_type == "chr":
            return self.chr_df_misperid
        elif df_type == "phys":
            return self.phys_df_misperid
        elif df_type == "other":
            if other_df is None:
                raise ValueError("Please pass your dataframe.")
            return other_df
        else:
            raise ValueError("Wrong type of dataframe passed.")

    def extract_categorical_common(self, df_type, keys, by_id, desc='', summ=None, other_df=None):
        """
        Function to report if all categorical values are the same and else report all the differences.
        For example, reported as Adult 5 times and Child 3.    
        :param df: the adequate dataframe
        :param summ: the file to which the summary will be written 
        
        :param keys: columns that the info should be extracted from in a list
        :param by_id: misper_id or vpd_nominalid_fk identifying a person
        :param desc: some description if we want to add before the summary of the values
        :return: 
        """
        
        def create_string_to_summ(keys, row, n_times):
            string_row = ""
            # corner case DOB
            if len(keys)==1 and keys[0]=='dob':
                try:
                    dob = row['dob'].strftime('%d %b %Y')
                    string_row += dob
                except:
                    string_row += 'N/A or not given'
         
            else:
                for k in keys:
                    string_row+= str(row[k]) if str(row[k]) !="nan" else 'N/A or not given' + ' '
                    string_row+=' '
                    print(str(row[k]))
            if n_times:
                string_row+=' (' + str(int(row['count'])) + (' reports) ' if row['count'] >1 else ' report) ')
            return string_row, str(int(row['id']))


        df = self.get_df_by_type(df_type, other_df)      
        if summ is None:
            summ = self.summ_file
    
        
        
        result = df.groupby(keys,dropna=False ).agg(
            id=(by_id, 'first'),
            count=(by_id, 'size'),
            source=('source', 'first'),
        ).reset_index()
            
        content = []
        
        print(result)
        result = result.sort_values(by='count', ascending=False)
        print(result)
        if len(desc):
                content.append(html.H3(desc))
                summ.write(desc)
                
        if len(result) == 0:
            content.append(html.H3('N/A or not given'))
            summ.write(' N/A or not given') 
        elif len(result) > 1:
            details = []
            primary_row = result.iloc[0]
            string_to_summ = create_string_to_summ(keys, primary_row, True)
            details.append(html.Summary(f"{string_to_summ[0]}"))
            details.append(
                html.Ul([
                    html.Li([
                        html.Span("Most recently in report: "),
                        dcc.Link(
                            string_to_summ[1],
                            href=f"/report/{primary_row['source']}/{string_to_summ[1]}"
                        ),
                        
                    ])
                ])
            )
            
            
            content.append(html.Details(details))
            # content.append(html.Br())
            content.append(html.Div("also reported as: \n"))
            # content.append(html.Br())
            summ.write(f"Primarily reported as {string_to_summ}")
            summ.write("also reported as: ")
            
            
            
            result_no_primary = result[result['id'] != primary_row['id']]

            for index, row in result[1::].iterrows():
                details = []
                string_to_summ = create_string_to_summ(keys, row, True)
                details.append(html.Summary(string_to_summ[0]+ ' '))
                details.append(
                    html.Ul([
                    html.Li([
                        html.Span("Most recently in report: "),
                        dcc.Link(
                            string_to_summ[1],
                            href=f"/report/{row['source']}/{string_to_summ[1]}"
                        ),
                        
                    ])
                ]))
                content.append(html.Details(details))
                    
                    
                summ.write(string_to_summ[0])
            
                

        else:
            details = []
            row = result.iloc[0]
            string_to_summ = create_string_to_summ(keys, row, True)
            details.append(html.Summary(string_to_summ[0]))
            details.append(html.Ul([
                html.Li([
                        html.Span("Most recently in report: "),
                        dcc.Link(
                            string_to_summ[1],
                            href=f"/report/{row['source']}/{string_to_summ[1]}"
                        ),
                        
                    ])
            ]))  
            content.append(html.Details(details))
            
            
            summ.write(string_to_summ[0])

        summ.write('\n')
        return result, html.Div(content)

    def concat_mp_vpd(self, col_mapping, keys, treat_equal=None):
        col_mapping['vpd_nominalincidentid_pk'] = 'reportid'
        vpd_new = self.vp_df_misperid.rename(columns=col_mapping)
        keys = set(keys)
        keys.add('reportid')
        keys.add('source')
        combined_df = pd.concat([self.mp_df_misperid, vpd_new], ignore_index=True)[list(keys)]
        if treat_equal:
            for k in keys:
                for equal_key in treat_equal.keys():
                    combined_df[k] = combined_df[k].replace(equal_key, treat_equal[equal_key])
        return combined_df
    
    def generate_risk_summary(self, df_type, other_df=None):
        df = self.get_df_by_type(df_type, other_df)
        
        risk_summary = "Risk levels:\n"
        risk_levels = ['High', 'Medium', 'Low']

        grouped = df.groupby(['initial_risk_level', 'current_final_risk_level'])['reportid'].agg(list).reset_index()
        initial_counts = df.groupby('initial_risk_level')['reportid'].agg(list).to_dict()

        for initial_level in risk_levels:
            ids = initial_counts.get(initial_level, [])
            total = len(ids)
            if total == 0:
                continue

            risk_summary += f"  - {initial_level} initial risk levels {total} times (ids: {ids})\n"
            transitions = grouped[grouped['initial_risk_level'] == initial_level]
            for final_level in risk_levels:
                matching = transitions[transitions['current_final_risk_level'] == final_level]
                if not matching.empty:
                    transition_ids = matching.iloc[0]['reportid']
                    count = len(transition_ids)
                    if initial_level == final_level:
                        risk_summary += f"    - {count} remained {initial_level} (ids: {transition_ids})\n"
                    else:
                        risk_summary += f"    - {count} changed to {final_level} (ids: {transition_ids})\n"
        self.summ_file.write(risk_summary)
        return risk_summary


    def report_with_all_ids(self, df_type, key, by_id, desc='', other_df=None):
        df = self.get_df_by_type(df_type, other_df)

        df_dict = df.groupby(key, dropna=False)[by_id].agg(list).to_dict()
        df_dict = dict(sorted(df_dict.items(), key=lambda item: len(item[1])))
        
        content = []
        
        if df_dict:
            self.summ_file.write(desc + '\n')
            content.append(html.H3(desc))

            for k, report_ids in df_dict.items():
                label = str(k) if str(k) != 'nan' else 'N/A or not reported'
                self.summ_file.write(
                    f"Reported: {label} ({len(report_ids)} times) (reports {report_ids})\n"
                )

                details = html.Details([
                    html.Summary(f"{label} ({len(report_ids)} reports)"),
                    html.Ul([
                        html.Li(dcc.Link(f"Report {rid}", href=f"/report/{df_type}/{rid}"))
                        for rid in report_ids
                    ])
                ])
                content.append(details)

        return html.Div(content)
        
        
    def report_disabilities(self, df_type, desc='', other_df=None):
        df = self.get_df_by_type(df_type, other_df)
        content = []
        
        content.append(html.H3('Disability: \n'))
        self.summ_file.write('Disability: \n')
        disability_not_known = df[df['vpd_disability'] == 'Not Known']
        disability_no = df[df['vpd_disability'] == 'No']
        disability_yes = df[df['vpd_disability'] == 'Yes (please specify)']
        print(len(disability_yes))
        grouped_yes = disability_yes.groupby(['vpd_disabilitydesc'])['vpd_nominalincidentid_pk'].unique().reset_index()

        
        details = []
        if len(disability_no): 
            details.append(html.Summary(f"Reported lack of disability in {len(disability_no)} reports"))
            details.append(html.Ul([
                        html.Li(dcc.Link(f"Report {rid}", href=f"/report/{df_type}/{rid}"))
                        for rid in disability_no['vpd_nominalincidentid_pk'].tolist()
                    ]))       
            self.summ_file.write(f"Reported lack of disability in {len(disability_no)} reports")
        if len(disability_not_known): 
            details.append(html.Summary(f"Reported no information regarding disability in {len(disability_not_known)} reports "))
            details.append(html.Ul([
                        html.Li(dcc.Link(f"Report {rid}", href=f"/report/{df_type}/{rid}"))
                        for rid in disability_not_known['vpd_nominalincidentid_pk'].tolist()
                    ])) 
            self.summ_file.write(f"Reported no information regarding disability in {len(disability_not_known)} reports [{disability_not_known['vpd_nominalincidentid_pk'].tolist()}]\n ")
        if len(disability_yes):
            text = "Reported following disabilities: " 
            self.summ_file.write(text)
            content.append(html.H4("Reported following disabilities: " ))
            
            for _, row in grouped_yes.iterrows():
                text = row['vpd_disabilitydesc']
                details.append(html.Summary(text))
                details.append(html.Ul([
                        html.Li(dcc.Link(f"Report {rid}", href=f"/report/{df_type}/{rid}"))
                        for rid in row['vpd_nominalincidentid_pk']
                    ])) 
                
            
            self.summ_file.write(text)
            
        content.append(html.Details(details))
        return html.Div(content)

    
    def report_repeated_victim_offender(self, df_type, other_df=None):
        df = self.get_df_by_type(df_type, other_df)
        repeated_victim_df = df[df['vpd_repeatvictim'] == 'Yes']
        repeat_perpetrator_df = df[df['vpd_repeatperpetrator'] == 'Yes']
        self.summ_file.write('Repeater victim/perpetrator: ')
        if len(repeated_victim_df)>1:
            self.summ_file.write(f"\nReported as a repeated victim (ids: {repeated_victim_df['vpd_nominalincidentid_pk'].tolist()})")
        if len(repeat_perpetrator_df)>1:
            self.summ_file.write(f"\nReported as a repeated perpetrator (ids: {repeat_perpetrator_df['vpd_nominalincidentid_pk'].tolist()})")
        else:
            self.summ_file.write('N\A')
        self.summ_file.write('\n')
        
    def create_mp_risk_questions_summary(self):  
        binary_columns = self.mp_df_misperid.columns[-26:-1]
        
        column_to_ids = {}
        for col in binary_columns:
            ids_with_1 = self.mp_df_misperid.loc[self.mp_df_misperid[col] == 1, 'reportid'].tolist()
            column_to_ids[col] = ids_with_1
        
        content = [html.H3('Vulnerability Questions')]
        column_to_ids = dict(sorted(column_to_ids.items(), key=lambda item: len(item[1]), reverse=True))
        for col in column_to_ids.keys():
            q_n = int(col.split('_')[0][1::])
            if len(column_to_ids[col])==0:
                continue
            details = []

            text = self.csv_files.risk_questions_dict[int(q_n)] + " answered yes in " + str(len(column_to_ids[col])) + " report(s)"
            details.append(html.Summary(text))
            
            ul_items = []
            for rid in column_to_ids[col]:
                comment_row = self.qs_comments_df_misperid[
                (self.qs_comments_df_misperid['reportid'] == rid) & 
                (self.qs_comments_df_misperid['questionid'] == q_n)
                ]
                comment = comment_row.iloc[0]['mcomment'] if not comment_row.empty else ''
                ul_items.append(
                html.Li([
                    dcc.Link(f"report {rid}", href=f"/report/mp/{rid}"),
                    html.Span(f": {comment}" if comment else "")
                ])
                )
            details.append(html.Ul(ul_items))
            content.append(html.Details(details))
        return html.Div(content)
    
    
    
    def create_vp_risk_questions_summary(self):  
        binary_columns = self.vp_df_misperid.columns[-43:-1]
        column_to_ids = {}
        for col in binary_columns:
            ids_with_1 = self.vp_df_misperid.loc[self.vp_df_misperid[col] == 1, 'vpd_nominalincidentid_pk'].tolist()
            column_to_ids[col] = ids_with_1
        
        content = [html.H3('Vulnerabilies from VPD')]
        column_to_ids = dict(sorted(column_to_ids.items(), key=lambda item: len(item[1]), reverse=True))
        
        for col, report_ids in column_to_ids.items():
            if not report_ids:
                continue

            summary_text = f"{vpd_mapping[col]}: in {len(report_ids)} report(s)"
            detail_block = html.Details([
                html.Summary(summary_text),
                html.Ul([
                    html.Li(
                        dcc.Link(f"report {rid}", href=f"/report/vp/{rid}")
                    )
                    for rid in report_ids
                ])
            ])
            content.append(detail_block)
        return html.Div(content)



    def create_summ_mp_home_locations(self):
        periods = []
        prev_address = None
        start_date = None
        end_date = None
                
        for _, row in self.mp_df_misperid.iterrows():
                curr_address = row['ha_address'] + ' (residence type: ' + row['residence_type'] + ')' 
                curr_date = row['date_reported_missing']
                curr_report_id = row['reportid']

                
                if curr_address != prev_address:
                    if prev_address is not None:
                        periods.append((prev_address, start_date, end_date, start_report_id, end_report_id))
                    start_date = curr_date
                    start_report_id = curr_report_id
                    prev_address = curr_address
                end_date = curr_date
                end_report_id = curr_report_id

            # Add last period
        if prev_address is not None:
            periods.append((prev_address, start_date, end_date, start_report_id, end_report_id))

        content = html.Div(
                [ html.Li([
                    f"{address} — reports from {start.strftime('%b %Y')} to {end.strftime('%b %Y')} (Report ",
                    dcc.Link(f"{start_rid}", href=f"/report/mp/{start_rid}"),
                    " to ",
                    dcc.Link(f"{end_rid}", href=f"/report/mp/{end_rid}"),
                    ")"
                ])
                for address, start, end, start_rid, end_rid in periods
    
        ])
        return html.Div([html.H3("Address of Residence \n"),  content])

    def create_summ_mp_missing_from_found_locations(self):
        results = []
        
        for _, row in self.mp_df_misperid.iterrows():
            address = f"from: {row['missing_from']} ({row['mf_address']}) → traced: {row['tl_address']}"
            date = row['date_reported_missing'].strftime('%b %Y')  # format like 'Jan 2020'
            rid = row['reportid']

            results.append(
                html.Li([
                    f"{address} —({date} Report ",
                    dcc.Link(f"{rid}", href=f"/report/mp/{rid}"),
                    ")"
                ])
            )
            
        return html.Div([html.H3("Going missing \n"),  html.Div(results)])

    def create_trends_summary(self):
        
        pass

    def create_summary(self):
        col_mapping = {'vpd_forename': 'forenames', 'vpd_surname': 'surname'}
        self.extract_categorical_common("other", ['forenames', 'surname'], 'reportid', desc='Name: ', other_df=self.concat_mp_vpd(col_mapping, ['forenames', 'surname', 'reportid', 'source']))

        self.extract_categorical_common("vp", ['vpd_maiden_name'], 'vpd_nominalincidentid_pk', desc='Maiden name: ')
        self.extract_categorical_common("vp", ['vpd_knownas'], 'vpd_nominalincidentid_pk', 'Also known as: ')
        self.extract_categorical_common("other", ['sex'], 'reportid', 'Sex/gender: ', other_df=self.concat_mp_vpd({'vpd_persongender': 'sex'}, ['sex'], treat_equal={'F': 'Female'}))
        self.extract_categorical_common("vp", ['vpd_personethnicappearance'], 'vpd_nominalincidentid_pk', desc='Appearance: ')
        self.extract_categorical_common("mp", ['dob'], 'reportid', 'Date of Birth: ')
        self.extract_categorical_common("vp", ['vpd_placeofbirth'],'vpd_nominalincidentid_pk', 'Place of birth: ' )
        self.extract_categorical_common("other", ['occdesc'], 'reportid', 'Occupation: ',  other_df=self.concat_mp_vpd({'vpd_occupation': 'occdesc'}, ['occdesc']))

        self.extract_categorical_common("vp", ['vpd_personlanguage'], 'vpd_nominalincidentid_pk', 'Language: ')
        self.extract_categorical_common("vp", ['vpd_interpreterreqid_fk'], 'vpd_nominalincidentid_pk', 'Interpreter ID: ')


        self.summ_file.write("Total missing person incidents: "+ str(len(self.mp_df_misperid)) + '\n')
        
        self.summ_file.write("\nVulnerabilities\n")
        labels_results, _ = self.extract_categorical_common("mp", ['label'], 'reportid', 'Previously assigned labels: ')
        labels = labels_results['label'].tolist() # Store previously assigned labels for later usage
        self.generate_risk_summary("mp")
        self.report_disabilities("vp")
        
        if 'Child' in labels:
            self.extract_categorical_common("vp", ['vpd_childprotection'], 'vpd_nominalincidentid_pk', "Involvement in or concern with child protection services: ")
            self.extract_categorical_common("vp", ['vpd_chsno'], 'vpd_nominalincidentid_pk', "Child hearing system: ")
        self.report_repeated_victim_offender("vp")
        self.report_with_all_ids("vp", 'vpd_threepointtest', 'vpd_nominalincidentid_pk', 'Three point test score: ')
        self.summ_file.close()

CreateSummary(410).create_summary()