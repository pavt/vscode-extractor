import os
import requests
import json
from tqdm import tqdm
from file_handler import FileHandler
from github_metadata_fetcher import GitHubMetadataFetcher

class ExtensionMetadataExtractor:
    def __init__(self, github_token):
        self.github_token = github_token
        self.data_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.file_handler = FileHandler()
        self.github_fetcher = GitHubMetadataFetcher(github_token)

    def fetch_extensions(self, max_results=50):
        url = "https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json;api-version=3.0-preview.1"
        }
        extensions_data = []
        page_number = 1
        page_size = 54

        while len(extensions_data) < max_results:
            payload = {
                "filters": [{
                    "criteria": [
                        {"filterType": 8, "value": "Microsoft.VisualStudio.Code"},
                        {"filterType": 10, "value": 'target:"Microsoft.VisualStudio.Code"'},
                        {"filterType": 12, "value": "37888"}
                    ],
                    "pageNumber": page_number,
                    "pageSize": page_size,
                    "sortBy": 4,
                    "sortOrder": 0
                }],
                "flags": 870
            }
            response = requests.post(url, headers=headers, data=json.dumps(payload))

            if response.status_code == 200:
                data = response.json()
                extensions = data.get("results", [])[0].get("extensions", [])

                if not extensions:
                    print(f"No hay más extensiones disponibles.")
                    break

                for ext in extensions:
                    if len(extensions_data) >= max_results:
                        break
                    publisher_name = ext.get("publisher", {}).get("publisherName", "N/A")
                    ext_name = ext.get("extensionName", "N/A")
                    link_to_extension = f"https://marketplace.visualstudio.com/items?itemName={publisher_name}.{ext_name}"

                    extensions_data.append({
                        "publisher_name": publisher_name,
                        "ext_name": ext_name,
                        "link_to_extension": link_to_extension
                    })

                page_number += 1
            else:
                print(f"Error en la solicitud: {response.status_code} - {response.text}")
                break

        return extensions_data
    
    def fetch_manifest_data(self, manifest_url):
        try:
            response = requests.get(manifest_url)
            if response.status_code == 200:
                manifest = response.json()
                return {
                    "repositories": manifest.get("repository", {}).get("url", "N/A"),
                    "tags": ", ".join(manifest.get("keywords", [])) if manifest.get("keywords") else "N/A",
                    "categories": ", ".join(manifest.get("categories", [])) if manifest.get("categories") else "N/A",
                }
        except Exception as e:
            print(f"Error al obtener el manifiesto desde {manifest_url}: {e}")
        return {"repositories": "N/A", "tags": "N/A", "categories": "N/A"}

    def fetch_extension_metadata(self, publisher_name, ext_name):
        url = "https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json;api-version=3.0-preview.1"
        }
        payload = {
            "filters": [
                {
                    "criteria": [
                        {"filterType": 7, "value": f"{publisher_name}.{ext_name}"}
                    ]
                }
            ],
            "flags": 914
        }

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            extensions = data.get("results", [])[0].get("extensions", [])
            if extensions:
                ext = extensions[0]

                # Obtener toda la metadata posible
                properties = ext.get("versions", [{}])[0].get("properties", [])
                repository_url = "N/A"
                for prop in properties:
                    if prop.get("key", "").lower() == "repositoryuri":
                        repository_url = prop.get("value", "N/A")
                        break

                # Obtener URL del manifiesto
                manifest_url = next(
                    (file["source"] for file in ext.get("versions", [{}])[0].get("files", [])
                     if file["assetType"] == "Microsoft.VisualStudio.Code.Manifest"),
                    "N/A"
                )

                # Extraer datos del manifiesto
                manifest_data = self.fetch_manifest_data(manifest_url) if manifest_url != "N/A" else {}

                # Obtener estadísticas
                statistics = ext.get("statistics", [])
                install_count = next((stat["value"] for stat in statistics if stat["statisticName"] == "install"), 0)
                average_rating = next((stat["value"] for stat in statistics if stat["statisticName"] == "averagerating"), 0)
                rating_count = next((stat["value"] for stat in statistics if stat["statisticName"] == "ratingcount"), 0)

                # Obtener métricas de código
                repo_name = repository_url.split('/')[-1]
                owner = repository_url.split('/')[-2]

                metadata = {
                    "publisher_name": ext.get("publisher", {}).get("publisherName", "N/A"),
                    "extension_name": ext.get("extensionName", "N/A"),
                    "display_name": ext.get("displayName", "N/A"),
                    "description": ext.get("shortDescription", "N/A"),
                    "last_updated": ext.get("lastUpdated", "N/A"),
                    "version": ext.get("versions", [{}])[0].get("version", "N/A"),
                    "tags": manifest_data.get("tags", "N/A"),
                    "categories": manifest_data.get("categories", "N/A"),
                    "install_count": install_count,
                    "average_rating": average_rating,
                    "rating_count": rating_count,
                    "repository": manifest_data.get("repositories", repository_url),
                    "icon_url": ext.get("versions", [{}])[0].get("files", [{}])[0].get("source", "N/A"),
                }
                return metadata
        return {}

    def run(self, max_results=50):
        extensions = self.fetch_extensions(max_results=max_results)

        if extensions:
            initial_json = os.path.join(self.data_dir, "1_extensions_initial.json")
            self.file_handler.save_to_json(extensions, initial_json)

            final_json = os.path.join(self.data_dir, "2_extensions_with_metadata.json")
            self.file_handler.append_metadata_to_json(initial_json, final_json, self.fetch_extension_metadata)

            repo_json = os.path.join(self.data_dir, "3_extensions_with_repository.json")
            self.file_handler.filter_extensions_with_github_repository(final_json, repo_json)

            github_json = os.path.join(self.data_dir, "4_github_metadata.json")
            self.github_fetcher.extract_github_metadata_to_json(repo_json, github_json)

            json_files = [initial_json, final_json, repo_json, github_json]

            for json_file in json_files:
                csv_file = json_file.replace(".json", ".csv")
                self.file_handler.json_to_csv(json_file, csv_file)
        else:
            print("No se encontraron extensiones.")