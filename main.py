from scripts.extract import extract
from scripts.transform import transform
from scripts.load import load
from scripts.build_ml_dataset import build_ml_dataset

def main():
    print("===================================")
    print(" DÉMARRAGE DU PIPELINE ETL")
    print("===================================")
    
    print("\n[1/3] Phase d'Extraction...")
    raw_data = extract()
    
    print("\n[2/3] Phase de Transformation...")
    transformed_data = transform(raw_data)
    
    print("\n[3/3] Phase de Chargement...")
    load(transformed_data)
    
    print("\n[4/4] Phase de Feature Engineering (Machine Learning)...")
    build_ml_dataset()
    
    print("\n===================================")
    print(" PIPELINE TERMINÉ AVEC SUCCÈS")
    print("===================================")

if __name__ == "__main__":
    main()
