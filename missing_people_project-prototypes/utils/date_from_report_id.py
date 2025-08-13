import pandas as pd
from functools import lru_cache
import datetime
import re
from dash import dcc, html

# Cache to store loaded CSV data to avoid repeated file reads
_csv_cache = {}

@lru_cache(maxsize=2)
def load_csv_data(file_type):
    """Load and cache CSV data for the specified file type."""
    if file_type == "vp":
        csv_path = "DATA/vp_new.csv"
        df = pd.read_csv(csv_path)
        df = df.rename(columns={"VPD_NOMINALINCIDENTID_PK": "reportid", "VPD_CREATEDON": "date_report"})
    elif file_type == "mp":
        csv_path = "DATA/mp_new.csv"
        df = pd.read_csv(csv_path)
        df = df.rename(columns={"missing_since": "date_report"})
    else: 
        return pd.DataFrame()
    return df 

def date_from_reportid_extract(report_id, file_type):
    """
    Look up the date for a given report_id in the specified file_type CSV.
    If not found, search in both mp and vp data sources.
    
    Args:
        report_id: The report ID to search for
        file_type: The type of file (used to determine which CSV to search first)
    
    Returns:
        str: The date associated with the report_id, or the report_id if not found
    """
    # Convert report_id to int for consistent matching
    try:
        report_id_int = int(report_id)
    except (ValueError, TypeError):
        return str(report_id)
    
    def extract_date_from_df(df, report_id_int):
        """Helper function to extract date from dataframe."""
        if df.empty:
            return None
            
        matching_rows = df[df['reportid'] == report_id_int]
        
        if not matching_rows.empty:
            date_value = matching_rows.iloc[0]['date_report']
            
            # Handle different date formats
            if pd.isna(date_value):
                return None
            
            try:
                # Extract date using regex pattern
                match = re.match(r'(\d{1,2}-[A-Za-z]{3}-\d{4}|\d{4}-\d{2}-\d{2})', str(date_value))
                if match:
                    return match.group(0)
            except Exception:
                pass
        
        return None
    
    # First, try the specified file_type
    df = load_csv_data(file_type)
    date_result = extract_date_from_df(df, report_id_int)
    
    if date_result:
        return date_result
    
    # If not found, search in both data sources
    for search_type in ["mp", "vp"]:
        if search_type != file_type:  # Don't search the same type twice
            df_search = load_csv_data(search_type)
            date_result = extract_date_from_df(df_search, report_id_int)
            if date_result:
                return date_result
    
    # If still not found, return the original report_id
    return str(report_id)

def date_from_reportid(report_id, file_type):
    """
    Create a Dash link component with date and report ID.
    
    Args:
        report_id: The report ID
        file_type: The file type to search in
        
    Returns:
        dcc.Link component or None if report_id is invalid
    """
    if report_id == "nan" or pd.isna(report_id):
        return None
    
    date = date_from_reportid_extract(report_id, file_type)
    
    return dcc.Link([
        html.Span(date, className="date-part"),
        html.Span(f"R{report_id}", className="report-id-part")
    ], href=f"/report/{file_type}/{report_id}", className="report-tag-medium-split")

if __name__ == '__main__':
    # Test the function
    result = date_from_reportid("1240", "mp")
    print(result)