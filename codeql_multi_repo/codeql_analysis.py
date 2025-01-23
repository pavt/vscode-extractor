import os
import subprocess
import pandas as pd
from tqdm import tqdm

# Define the path to CodeQL suites with correct $HOME expansion
CODEQL_SUITES_PATH = os.path.expanduser('~/codeql/codeql-repo')

# Define supported languages and their corresponding suites
language_suites = {
    'JavaScript': 'javascript/ql/src/codeql-suites/javascript-security-extended.qls',
    'TypeScript': 'javascript/ql/src/codeql-suites/javascript-security-extended.qls',
    'Python': 'python/ql/src/codeql-suites/python-security-extended.qls',
    'Go': 'go/ql/src/codeql-suites/go-security-extended.qls',
    'Java': 'java/ql/src/codeql-suites/java-security-extended.qls',
    'C': 'cpp/ql/src/codeql-suites/cpp-security-extended.qls',
    'C#': 'csharp/ql/src/codeql-suites/csharp-security-extended.qls'
}

def create_directories(results_dir):
    """
    Create the necessary directories for storing CodeQL databases and results.
    """
    databases_dir = os.path.join(results_dir, 'databases')
    codeql_results_dir = os.path.join(results_dir, 'codeql-results')
    os.makedirs(databases_dir, exist_ok=True)
    os.makedirs(codeql_results_dir, exist_ok=True)
    return databases_dir, codeql_results_dir

def create_codeql_database(repo_owner, repo_name, repo_path, db_name, language):
    """
    Check if the CodeQL database exists for a repository. If not, create it.
    """
    if os.path.exists(db_name):
        print(f"Database already exists for {repo_owner}/{repo_name}")
        return True

    create_db_command = [
        'codeql', 'database', 'create', db_name,
        '--language=' + language.lower(), '--source-root', repo_path
    ]
    try:
        print(f"Creating database for {repo_owner}/{repo_name}...")
        subprocess.run(create_db_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error creating database for {repo_owner}/{repo_name}")
        print("Command:", " ".join(create_db_command))
        print("Standard output:", e.stdout.decode('utf-8'))
        print("Standard error:", e.stderr.decode('utf-8'))
        return False

def analyze_repository(repo_owner, repo_name, db_name, result_file, language):
    """
    Analyze the CodeQL database for a repository using the appropriate suite.
    """
    suite_path = os.path.join(CODEQL_SUITES_PATH, language_suites.get(language, ""))
    if not os.path.exists(suite_path):
        print(f"Suite not found for language {language}: {suite_path}")
        return False

    analyze_command = [
        'codeql', 'database', 'analyze', db_name,
        suite_path, '--format=sarifv2.1.0', '--output', result_file
    ]
    try:
        print(f"Analyzing {repo_owner}/{repo_name}...")
        subprocess.run(analyze_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error analyzing {repo_owner}/{repo_name}")
        print("Command:", " ".join(analyze_command))
        print("Standard output:", e.stdout.decode('utf-8'))
        print("Standard error:", e.stderr.decode('utf-8'))
        return False

def process_repositories(df, base_dir, results_dir, num_repos):
    """
    Process a specified number of repositories by creating databases and running CodeQL analysis.
    """
    databases_dir, codeql_results_dir = create_directories(results_dir)
    df = df.head(num_repos)  # Limit processing to specified number of repositories

    with tqdm(total=len(df), desc="Analyzing repositories") as pbar:
        for _, row in df.iterrows():
            repo_owner = row['repo_owner']
            repo_name = row['repo_name']
            language = row['language']

            # Skip unsupported languages
            if language not in language_suites:
                print(f"Skipping {repo_owner}/{repo_name}: Unsupported language {language}")
                pbar.update(1)
                continue

            repo_path = os.path.join(base_dir, repo_owner, repo_name)
            db_name = os.path.join(databases_dir, f"{repo_owner}-{repo_name}-db")
            result_file = os.path.join(codeql_results_dir, f"{repo_owner}____{repo_name}____results.sarif")

            # Validate repository path
            if not os.path.exists(repo_path):
                print(f"Repository path does not exist: {repo_path}")
                pbar.update(1)
                continue

            # Create the CodeQL database
            if not create_codeql_database(repo_owner, repo_name, repo_path, db_name, language):
                pbar.update(1)
                continue

            # Analyze the repository
            if not analyze_repository(repo_owner, repo_name, db_name, result_file, language):
                pbar.update(1)
                continue

            pbar.update(1)

def run_analysis(csv_file_path, base_dir, results_dir, num_repos=2):
    """
    Load the CSV file and start processing repositories for analysis.
    """
    try:
        df = pd.read_csv(csv_file_path)
    except Exception as e:
        print(f"Error loading CSV file: {e}")
        return

    process_repositories(df, base_dir, results_dir, num_repos)
