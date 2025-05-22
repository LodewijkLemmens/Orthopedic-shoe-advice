import streamlit as st
import os

# Basispad naar je data
DATA_DIR = "data"

def list_folders(path):
    """Geeft een lijst van mappen terug in een directory."""
    return sorted([f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))])

def file_exists(path, ext):
    """Controleert of een bestand met bepaalde extensie bestaat in een map."""
    return any(fname.endswith(ext) for fname in os.listdir(path))

def load_file(path):
    """Laadt een bestand als tekst (voor demo-doeleinden)."""
    with open(path, 'r', encoding='latin1') as f:
        return f.read()

st.title("Pedar Data Analyse Dashboard")

# 1. Kies patiënt
patients = list_folders(DATA_DIR)
selected_patient = st.selectbox("Selecteer patiënt", patients)

if selected_patient:
    patient_path = os.path.join(DATA_DIR, selected_patient)
    dates = list_folders(patient_path)
    selected_date = st.selectbox("Selecteer meetdatum", dates)

    if selected_date:
        date_path = os.path.join(patient_path, selected_date)
        measurements = list_folders(date_path)
        selected_measurement = st.selectbox("Selecteer meting", measurements)

        if selected_measurement:
            measurement_path = os.path.join(date_path, selected_measurement)

            # Toon beschikbare bestanden
            asc_path = os.path.join(measurement_path, "data.asc")
            fgt_path = os.path.join(measurement_path, "data.fgt")

            if os.path.exists(asc_path):
                st.subheader("Inhoud van ASC-bestand")
                st.text(load_file(asc_path))
            else:
                st.warning("Geen .asc-bestand gevonden.")

            if os.path.exists(fgt_path):
                st.subheader("Inhoud van FGT-bestand")
                st.text(load_file(fgt_path))
            else:
                st.warning("Geen .fgt-bestand gevonden.")
