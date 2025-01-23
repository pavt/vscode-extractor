from extension_metadata_extractor import ExtensionMetadataExtractor
from dotenv import load_dotenv
import os

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

if __name__ == "__main__":
    github_token = os.getenv("GITHUB_TOKEN")  # Obtener el token de GitHub desde las variables de entorno
    extractor = ExtensionMetadataExtractor(github_token)
    extractor.run(max_results=10)  # Puedes cambiar a 100 si lo deseas