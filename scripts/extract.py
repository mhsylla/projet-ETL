# scripts/extract.py

from pathlib import Path
import pandas as pd


RAW_DATA_PATH = Path("data/raw")


def load_dataset(folder: str) -> dict:
    """
    Charge tous les fichiers CSV présents dans un dossier.

    Parameters
    ----------
    folder : str
        Nom du dossier contenant les fichiers CSV.

    Returns
    -------
    dict
        {nom_fichier: DataFrame}
    """

    dataset_path = RAW_DATA_PATH / folder    

    if not dataset_path.exists():
        raise FileNotFoundError(f"{dataset_path} n'existe pas.")

    dataframes = {}

    for file in dataset_path.glob("*.csv"):
        dataframes[file.stem] = pd.read_csv(file)

    return dataframes


def extract():
    """
    Extrait les données des deux datasets.
    """

    compets = load_dataset("compets")
    matches = load_dataset("matches")

    return {
        "compets": compets,
        "matches": matches,
    }


if __name__ == "__main__":

    datasets = extract()
    print(datasets)

    print("\n====== DATASET 1 ======")

    for name, df in datasets["compets"].items():
        print(f"{name} : {df.shape}")

    print("\n====== DATASET 2 ======")

    for name, df in datasets["matches"].items():
        print(f"{name} : {df.shape}")