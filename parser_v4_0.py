import os
import json
from datetime import datetime

from pubmed_parser_v1_0 import parse_pubmed
from amazon_parser_v1_0 import parse_amazon
from drugscom_parser_v1_0 import parse_drugscom
from uppsala_parser_v1_0 import parse_uppsala
from semanticscholar_parser_v1_1 import parse_semanticscholar


def master_parser(drug_name, sources):
    results = []
    if 'pubmed' in sources:
        results.extend(parse_pubmed(drug_name))
    if 'amazon' in sources:
        results.extend(parse_amazon(drug_name))
    if 'drugscom' in sources:
        results.extend(parse_drugscom(drug_name))
    if 'uppsala' in sources:
        results.extend(parse_uppsala(drug_name))
    if 'semanticscholar' in sources:
        results.extend(parse_semanticscholar(drug_name))

    query_date = datetime.now().strftime("%d_%m_%Y")
    safe_drug_name = drug_name.replace(" ", "_")
    filename = f"{safe_drug_name}_{query_date}.json"
    output_dir = "drug_data"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    return output_path

def main():
    drug_name = input("Введите название лекарственного препарата: ").strip()
    if not drug_name:
        print("Название препарата не может быть пустым.")
        return
    sources = ['semanticscholar']
    result_file = master_parser(drug_name, sources)
    print(f"Данные сохранены в файл {result_file}")

if __name__ == "__main__":
    main()
