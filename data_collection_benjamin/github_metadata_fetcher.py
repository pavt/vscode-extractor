import json
import requests
from tqdm import tqdm

class GitHubMetadataFetcher:
    def __init__(self, github_token):
        self.github_token = github_token

    def fetch_code_metrics(self, owner, repo):
        url = f"https://api.github.com/repos/{owner}/{repo}/stats/code_frequency"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.github_token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                additions = sum(week[1] for week in data)
                deletions = sum(week[2] for week in data)
                code_lines = additions - deletions
                blank_lines = 0  # GitHub API does not provide blank lines directly
                comment_lines = 0  # GitHub API does not provide comment lines directly
                return {
                    "blankLines": blank_lines,
                    "codeLines": code_lines,
                    "commentLines": comment_lines,
                    "metrics": f"Blank Lines: {blank_lines}, Code Lines: {code_lines}, Comment Lines: {comment_lines}"
                }
        except Exception as e:
            print(f"Error al obtener las métricas de código desde {url}: {e}")
        return {"blankLines": 0, "codeLines": 0, "commentLines": 0, "metrics": "No data"}

    def fetch_last_commit(self, owner, repo):
        url = f"https://api.github.com/repos/{owner}/{repo}/commits"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.github_token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                commits = response.json()
                if commits:
                    last_commit = commits[0]
                    return {
                        "lastCommit": last_commit.get("commit", {}).get("message", ""),
                        "lastCommitSHA": last_commit.get("sha", "")
                    }
            else:
                print(f"Error al obtener el último commit de {url}: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Excepción al obtener el último commit de {url}: {e}")
        return {"lastCommit": "", "lastCommitSHA": ""}

    def fetch_github_metadata(self, owner, repo):
        if repo.endswith(".git"):
            repo = repo[:-4]

        url = f"https://api.github.com/repos/{owner}/{repo}"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.github_token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                repo_data = response.json()
                last_commit_data = self.fetch_last_commit(owner, repo)
                code_metrics = self.fetch_code_metrics(owner, repo)
                return {
                    "id": repo_data.get("id", "N/A"),
                    "name": repo_data.get("name", "N/A"),
                    "isFork": repo_data.get("fork", False),
                    "commits": repo_data.get("commits_url", "").split("{")[0],
                    "branches": repo_data.get("branches_url", "").split("{")[0],
                    "releases": repo_data.get("releases_url", "").split("{")[0],
                    "forks": repo_data.get("forks_count", 0),
                    "mainLanguage": repo_data.get("language", "N/A"),
                    "defaultBranch": repo_data.get("default_branch", "N/A"),
                    "license": repo_data.get("license", {}).get("name", "N/A"),
                    "homepage": repo_data.get("homepage", "N/A"),
                    "watchers": repo_data.get("watchers_count", 0),
                    "stargazers": repo_data.get("stargazers_count", 0),
                    "contributors": repo_data.get("contributors_url", ""),
                    "size": repo_data.get("size", 0),
                    "createdAt": repo_data.get("created_at", "N/A"),
                    "pushedAt": repo_data.get("pushed_at", "N/A"),
                    "updatedAt": repo_data.get("updated_at", "N/A"),
                    "totalIssues": repo_data.get("open_issues_count", 0),
                    "openIssues": repo_data.get("open_issues_count", 0),
                    "totalPullRequests": repo_data.get("pulls_url", "").split("{")[0],
                    "openPullRequests": repo_data.get("pulls_url", "").split("{")[0],
                    "blankLines": code_metrics.get("blankLines", 0),
                    "codeLines": code_metrics.get("codeLines", 0),
                    "commentLines": code_metrics.get("commentLines", 0),
                    "metrics": code_metrics.get("metrics", ""),
                    "lastCommit": last_commit_data.get("lastCommit", ""),
                    "lastCommitSHA": last_commit_data.get("lastCommitSHA", ""),
                    "hasWiki": repo_data.get("has_wiki", False),
                    "isArchived": repo_data.get("archived", False),
                    "isDisabled": repo_data.get("disabled", False),
                    "isLocked": repo_data.get("locked", False),
                    "languages": repo_data.get("languages_url", ""),
                    "labels": repo_data.get("labels_url", ""),
                    "topics": ", ".join(repo_data.get("topics", []))
                }
            elif response.status_code == 403 and 'X-RateLimit-Remaining' in response.headers and response.headers['X-RateLimit-Remaining'] == '0':
                reset_time = int(response.headers['X-RateLimit-Reset'])
                print(f"Rate limit exceeded. Please try again after {reset_time}.")
                return None
            elif response.status_code == 404:
                print(f"Repositorio no encontrado: {url}")
                return None
            else:
                print(f"Error al obtener metadata de {url}: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Excepción al obtener metadata de {url}: {e}")
        return None
    
    def extract_github_metadata_to_json(self, input_json, output_json):
        with open(input_json, "r", encoding="utf-8") as json_file:
            extensions = json.load(json_file)

        updated_extensions = []
        for ext in tqdm(extensions, desc="Obteniendo metadata de GitHub", unit="ext"):
            repo_url = ext.get("repository", "")
            if "github.com" in repo_url:
                owner, repo = repo_url.split("/")[-2], repo_url.split("/")[-1]
                metadata = self.fetch_github_metadata(owner, repo)
                if metadata:
                    ext.update(metadata)
                    updated_extensions.append(ext)
                else:
                    print(f"Error al obtener metadata de GitHub para: {repo_url}")

        with open(output_json, 'w', encoding='utf-8') as json_file:
            json.dump(updated_extensions, json_file, ensure_ascii=False, indent=4)