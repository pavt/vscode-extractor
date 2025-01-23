import csv
import json
from tqdm import tqdm

class FileHandler:
    def append_metadata_to_json(self, input_json, output_json, fetch_extension_metadata):
        with open(input_json, "r", encoding="utf-8") as json_file:
            extensions = json.load(json_file)

        updated_extensions = []
        for ext in tqdm(extensions, desc="Procesando extensiones", unit="ext"):
            print(f"Obteniendo metadata para: {ext['publisher_name']}.{ext['ext_name']}")
            metadata = fetch_extension_metadata(ext["publisher_name"], ext["ext_name"])
            if metadata:
                ext.update(metadata)
                updated_extensions.append(ext)
            else:
                print(f"Error al obtener metadata para: {ext['publisher_name']}.{ext['ext_name']}")

        self.save_to_json(updated_extensions, output_json)
    
    def filter_extensions_with_github_repository(self, input_json, output_json):
        with open(input_json, 'r', encoding='utf-8') as json_file:
            extensions = json.load(json_file)

        extensions_with_github_repo = [ext for ext in extensions if ext.get('repository') and 'github.com' in ext['repository']]

        if extensions_with_github_repo:
            self.save_to_json(extensions_with_github_repo, output_json)
        else:
            print("No se encontraron extensiones con repositorio de GitHub.")

    def json_to_csv(self, input_json, output_csv):
        with open(input_json, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)

        if not data:
            print(f"No hay datos en {input_json} para convertir a CSV.")
            return

        headers = data[0].keys()

        with open(output_csv, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=headers)
            writer.writeheader()
            for row in data:
                writer.writerow(row)

        print(f"CSV guardado en: {output_csv}")

    def save_to_json(self, data, file_path):
        if not data:
            print("No hay datos para guardar en el JSON.")
            return
        with open(file_path, "w", encoding="utf-8") as output_file:
            json.dump(data, output_file, ensure_ascii=False, indent=4)
        print(f"JSON guardado en: {file_path}")