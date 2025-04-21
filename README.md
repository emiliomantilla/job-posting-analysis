Job Posting Analysis

A lean, end‑to‑end Python & Tableau project to analyze Stack Overflow Developer Survey & LinkedIn job postings data.Fetch raw data via the Kaggle API, clean and prepare with pandas, then visualize in Tableau.

📁 Project Structure

job-posting-analysis/
├── data/
│   ├── raw/               # Kaggle downloads (ignored in Git)
│   └── cleaned/           # Output of cleaning scripts
├── notebooks/
│   └── 1_data_prep.ipynb  # Exploration & validation
├── src/
│   └── download_and_clean.py  # Download & cleaning pipeline
├── steame-env/            # Python virtual environment
├── .gitignore
├── requirements.txt
└── README.md

🛠️ Setup

Clone the repo

git clone git@github.com:your-username/job-posting-analysis.git
cd job-posting-analysis

Create & activate virtualenv

python3 -m venv steame-env
source steame-env/bin/activate

Install dependencies

pip install --upgrade pip
pip install -r requirements.txt

📥 Getting the Data

We rely on two public Kaggle datasets:

Dataset

URL

Stack Overflow Developer Survey 2024

https://www.kaggle.com/datasets/berkayalan/stack-overflow-annual-developer-survey-2024?select=survey_results_public.csv

LinkedIn Job Postings 2023–2024

https://www.kaggle.com/datasets/arshkon/linkedin-job-postings?select=postings.csv

1. Install & configure the Kaggle CLI

pip install kaggle

Go to https://www.kaggle.com/me/account → API → Create New API Token.

Download kaggle.json and move it to your home folder:

mkdir -p ~/.kaggle
mv ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json

Note: ~/.kaggle/kaggle.json is in your home directory and is never committed.

2. Download & unzip datasets

Place the following at the top of your notebook or in src/download_and_clean.py:

from kaggle.api.kaggle_api_extended import KaggleApi

api = KaggleApi()
api.authenticate()

# Download Stack Overflow Survey 2024
api.dataset_download_files(
  'berkayalan/stack-overflow-annual-developer-survey-2024',
  path='data/raw',
  unzip=True
)

# Download LinkedIn Job Postings 2023–2024
api.dataset_download_files(
  'arshkon/linkedin-job-postings',
  path='data/raw',
  unzip=True
)

After running, you will have:

data/raw/survey_results_public.csv
data/raw/postings.csv

If desired, rename the LinkedIn file for clarity:

mv data/raw/postings.csv data/raw/linkedin_postings.csv

🧹 Data Cleaning & Preparation

Run the downloader & cleaner script to produce tidy CSVs:

python src/download_and_clean.py

This outputs:
- data/cleaned/so_survey_cleaned.csv- data/cleaned/linkedin_cleaned.csv

🔎 Exploration & Validation

Open the Jupyter notebook to explore and validate your cleaned data:

jupyter lab

notebooks/1_data_prep.ipynb contains pandas-based EDA: value counts, distributions, sample plots.

📊 Visualization in Tableau

Open Tableau Desktop (or Public)

Connect to Text File → point at

data/cleaned/so_survey_cleaned.csv

then add a second source: data/cleaned/linkedin_cleaned.csv

Build Dashboards

Developer Landscape (SO Survey): top DevTypes, language usage, salary distributions.

US Job Map (LinkedIn): filled map by state, coloring by median salary for a selected job title.

Comparison View: national bars comparing SO dev‑type counts vs. LinkedIn posting counts for key roles.

Publish your workbook to Tableau Public and record the shareable link.

📄 README Maintenance

Update this file as you add new scripts, notebooks, or dependencies.

Keep .gitignore in sync with any new generated folders you don’t want in Git.

⚖️ License

This project is released under the MIT License. See LICENSE for details.