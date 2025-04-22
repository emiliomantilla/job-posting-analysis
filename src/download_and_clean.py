import os
import re
from kaggle.api.kaggle_api_extended import KaggleApi
import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer

# Determine project root (one level up from src)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RAW_DIR = os.path.join(PROJECT_ROOT, 'data', 'raw')
CLEANED_DIR = os.path.join(PROJECT_ROOT, 'data', 'cleaned')

# State name to abbreviation mapping
STATE_ABBREV = {
    'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR', 'california': 'CA',
    'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE', 'florida': 'FL', 'georgia': 'GA',
    'hawaii': 'HI', 'idaho': 'ID', 'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA',
    'kansas': 'KS', 'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
    'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS', 'missouri': 'MO',
    'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV', 'new hampshire': 'NH', 'new jersey': 'NJ',
    'new mexico': 'NM', 'new york': 'NY', 'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH',
    'oklahoma': 'OK', 'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC',
    'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT', 'vermont': 'VT',
    'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV', 'wisconsin': 'WI', 'wyoming': 'WY'
}

# Metro area overrides for state extraction
METRO_OVERRIDES = {
    'san francisco bay': 'CA',
    'new york city metropolitan': 'NY',
    'austin, texas metropolitan': 'TX',
    'atlanta metropolitan': 'GA',
    'kansas city metropolitan': 'MO',
    'raleigh-durham': 'NC',
    'portland, oregon metropolitan': 'OR',
    'greater st. louis': 'MO',
    'charlotte metro': 'NC',
    'cincinnati metropolitan': 'OH',
    'greater seattle': 'WA',
    'washington dc': 'DC',
    'columbia, south carolina': 'SC',
    'los angeles metropolitan': 'CA'
}


def download_data():
    """
    Download raw datasets from Kaggle into {PROJECT_ROOT}/data/raw/
    """
    os.makedirs(RAW_DIR, exist_ok=True)
    api = KaggleApi()
    api.authenticate()

    # Download Stack Overflow Survey 2024
    api.dataset_download_files(
        'berkayalan/stack-overflow-annual-developer-survey-2024',
        path=RAW_DIR,
        unzip=True
    )

    # Download LinkedIn Job Postings 2023-2024
    api.dataset_download_files(
        'arshkon/linkedin-job-postings',
        path=RAW_DIR,
        unzip=True
    )

def clean_so_survey():
    """
    Clean and subset Stack Overflow survey:
    - Filter to US respondents and select roles
    - Clean Age and Employment
    - One-hot LearnCode, Language, Database, Platform (top 5 + Other)
    """
    raw_path = os.path.join(RAW_DIR, 'survey_results_public.csv')
    df = pd.read_csv(raw_path, low_memory=False)

    # Filter US
    df = df[df.Country.str.contains('United States', na=False)].copy()

    # Filter to specific roles
    roles = [
        'Data or business analyst',
        'Data scientist or machine learning specialist',
        'Data engineer'
    ]
    df = df[df.DevType.str.contains('|'.join(roles), na=False)].copy()

    # Clean Age
    df['Age'] = df['Age'].str.replace(' years old', '', regex=False)

    # Map Employment to simpler status
    def map_emp(x):
        if any(k in x for k in ['Employed, full-time', 'Employed, part-time',
                                 'Independent contractor, freelancer, or self-employed']):
            return 'employed'
        if 'Not employed' in x:
            return 'unemployed'
        if 'Student' in x:
            return 'student'
        return 'other'
    df['Employment_Status'] = df['Employment'].fillna('').apply(map_emp)

    # One-hot encode multi-value columns, limit to top 5 each
    multi_cols = {
        'LearnCode': ';',
        'LanguageHaveWorkedWith': ';',
        'DatabaseHaveWorkedWith': ';',
        'PlatformHaveWorkedWith': ';'
    }
    for col, sep in multi_cols.items():
        lists = df[col].fillna('').str.split(sep).apply(lambda x: [i.strip() for i in x if i.strip()])
        all_vals = pd.Series([v for sub in lists for v in sub])
        top5 = all_vals.value_counts().index[:5].tolist()
        for v in top5:
            safe = v.replace(' ', '_').replace('/', '_')
            df[f"{col}_{safe}"] = lists.apply(lambda lst: int(v in lst))
        df[f"{col}_Other"] = lists.apply(lambda lst: int(any(v not in top5 for v in lst)))

    # Drop original and unwanted columns
    drop_cols = list(multi_cols.keys()) + ['LearnCode.1', 'LearnCodeOnline']
    df.drop(columns=[c for c in drop_cols if c in df.columns], inplace=True)

    # Select demographics + dummy columns
    demo_cols = [
        'ResponseId', 'MainBranch', 'Age', 'Employment_Status',
        'CodingActivities', 'EdLevel', 'DevType', 'Country'
    ]
    dummy_cols = [c for c in df.columns if any(c.startswith(prefix) for prefix in multi_cols)]
    output_cols = demo_cols + dummy_cols

    # Write cleaned data
    os.makedirs(CLEANED_DIR, exist_ok=True)
    df[output_cols].to_csv(os.path.join(CLEANED_DIR, 'so_survey_cleaned.csv'), index=False)


def extract_state(loc):
    """
    Extract two-letter state code, using overrides and generic logic.
    """
    if not isinstance(loc, str):
        return 'Other'
    lower = loc.lower()
    # Metro overrides
    for key, code in METRO_OVERRIDES.items():
        if key in lower:
            return code
    # Generic
    parts = [p.strip() for p in loc.split(',')]
    for part in parts:
        low = part.lower()
        if low in STATE_ABBREV:
            return STATE_ABBREV[low]
        if len(part) == 2 and part.isupper() and part in STATE_ABBREV.values():
            return part
    # Nationwide exact
    if len(parts) == 1 and parts[0] in ['United States', 'USA']:
        return 'Nationwide'
    return 'Other'


def clean_linkedin():
    """
    Clean LinkedIn postings:
    - Filter titles
    - Extract state
    - Clean title and assign DevType
    - Dedupe and drop missing salary
    """
    raw = pd.read_csv(os.path.join(RAW_DIR, 'postings.csv'), low_memory=False)
    # Title filter
    patterns = [
        r'(?i)\bdata engineer\b',
        r'(?i)\b(?:machine learning|ml|ai|artificial intelligence)\b',
        r'(?i)\bdata scientist\b',
        r'(?i)\b(?:data analyst|business analyst)\b'
    ]
    mask = raw['title'].fillna('').str.contains('|'.join(patterns), regex=True)
    df = raw[mask].copy()
    # State
    df['State'] = df['location'].apply(extract_state)
    # Clean title
    df['JobTitle'] = df['title'].str.strip().str.title()
    # DevType mapping priority
    def map_devtype(title):
        t = title.lower()
        if re.search(r'\bdata engineer\b', t):
            return 'Data engineer'
        if re.search(r'\bdata scientist\b',t): 
            return 'Data scientist or machine learning specialist'
        if re.search(r'\b(machine learning|ml|ai|artificial intelligence)\b', t):
            return 'Data scientist or machine learning specialist'
        if re.search(r'\b(data analyst|business analyst)\b', t):
            return 'Data or business analyst'
        return None
    df['DevType'] = df['JobTitle'].apply(map_devtype)
    # Select and dedupe
    final = ['JobTitle', 'location', 'State', 'normalized_salary', 'work_type', 'pay_period', 'DevType']
    avail = [c for c in final if c in df.columns]
    df = df.drop_duplicates(subset=avail)[avail]
    df = df[df['normalized_salary'].notna()]
    os.makedirs(CLEANED_DIR, exist_ok=True)
    df.to_csv(
        os.path.join(CLEANED_DIR, 'linkedin_cleaned.csv'),
        index=False
    )


if __name__ == '__main__':
    download_data()
    clean_so_survey()
    clean_linkedin()
