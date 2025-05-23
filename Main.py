import streamlit as st
import os
import re
import numpy as np
import matplotlib.pyplot as plt
import traceback

root_path = r"C:\Users\l.lemmens\Documents\SynologyDrive\SynologyDrive\VCW-AZURE-NB167\C\novel\novfile\ascii\asciiout\pedar"

if 'current_path' not in st.session_state:
    st.session_state.current_path = root_path

def go_up():
    if st.session_state.current_path != root_path:
        st.session_state.current_path = os.path.dirname(st.session_state.current_path)

st.title("Mapbrowser in Streamlit")

if st.button("⬆️ Ga 1 map omhoog"):
    go_up()

st.write(f"**Huidige map:** {st.session_state.current_path}")

try:
    items = os.listdir(st.session_state.current_path)
except PermissionError:
    st.error("Geen toegang tot deze map")
    items = []

folders = [item for item in items if os.path.isdir(os.path.join(st.session_state.current_path, item))]
files = [item for item in items if os.path.isfile(os.path.join(st.session_state.current_path, item)) and item.lower().endswith('.asc')]

st.subheader("Mappen")
for folder in folders:
    if st.button(f"📁 {folder}"):
        st.session_state.current_path = os.path.join(st.session_state.current_path, folder)
        # Na wijzigen van current_path verschijnt automatisch nieuwe content bij volgende run

st.subheader("Bestanden")
metingen_dict = {}

# Regex om getal aan het einde van bestandsnaam (zonder extensie) te vinden
pattern = re.compile(r"(\d+)(?=\.[^.]+$)")

for file in files:
    match = pattern.search(file)
    if match:
        nummer = match.group(1)
        meting_naam = f"Meting {nummer}"
    else:
        # Bestanden zonder nummer of niet passend patroon kunnen 'Onbekend' krijgen
        meting_naam = f"Onbekend: {file}"
    metingen_dict[meting_naam] = os.path.join(st.session_state.current_path, file)

# Dropdown om meting te kiezen
gekozen_meting = st.selectbox("Kies een meting:", sorted(metingen_dict.keys()))

if gekozen_meting:
    gekozen_bestand = metingen_dict[gekozen_meting]
    st.write(f"Je hebt gekozen: {gekozen_bestand}")

    # Toon de inhoud van het gekozen bestand
    try:
        with open(gekozen_bestand, "r") as f:
            content = f.read()
            st.text_area("Inhoud van bestand:", content, height=300)
    except Exception as e:
        st.write(f"Kan bestand niet openen: {e}")

    def run_code_voor_meting(meting_naam, asc_file):
        try:
            fgt_file = asc_file.replace('.asc', '.fgt')  # aanname: fgt bestand zit in dezelfde map met zelfde naam


            aantal_sensors = 99  # Aantal sensoren per voet

            # Defineer de maskers
            masks = {
                'Hallux': [83, 84, 90, 91, 96],
                'Dig25': [85, 86, 87, 88, 89, 92, 93, 94, 95, 97, 98, 99],
                'MTH1': [55, 56, 62, 63, 69, 70, 76, 77],
                'MTH25': [57, 58, 59, 60, 61, 64, 65, 66, 67, 68, 71, 72, 73, 74, 75, 78, 79, 80, 81, 82],
                'Midfoot': [27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54],
                'Heel': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]
            }

            if os.path.exists(asc_file) and os.path.exists(fgt_file):
                # Laad de data in
                raw_data = np.loadtxt(asc_file, skiprows=10)

                # Step detection en berekening van Mean Peak Pressure (MPP) per sensor
                steps = np.loadtxt(fgt_file, skiprows=9)
                filtered_steps = []
                non_detected_timestamps = []

                for i in range(len(steps)):
                    if sum(steps[i, 1:7]) > 0:
                        filtered_steps.append(steps[i, :])
                    else:
                        non_detected_timestamps.append(steps[i, 0])

                filtered_steps_array = np.array(filtered_steps)
                links_step_detection = filtered_steps_array[:, 1]
                rechts_step_detection = filtered_steps_array[:, 4]
                time_stamps = filtered_steps_array[:, 0]

                IC_L, TO_L, IC_R, TO_R = [], [], [], []
                step_detection_threshold_l = 120
                step_detection_threshold_r = 120
                if sum(x > 120 for x in links_step_detection) / len(links_step_detection) * 100 > 98:
                    step_detection_threshold_l = np.mean(links_step_detection) - 100
                if sum(x > 120 for x in rechts_step_detection) / len(rechts_step_detection) * 100 > 98:
                    step_detection_threshold_r = np.mean(rechts_step_detection) - 100

                # Detectie van initial contact (IC) en toe off (TO) voor linker en rechter voet
                for x in range(5, len(links_step_detection) - 5):
                    if links_step_detection[x] > step_detection_threshold_l and (np.median(links_step_detection[x-3:x]) < step_detection_threshold_l) and (np.median(links_step_detection[x+1:x+5]) > step_detection_threshold_l):
                        if len(IC_L) == 0 or (time_stamps[x] - 0.3) > max(IC_L):
                            IC_L.append(time_stamps[x])
                    if links_step_detection[x] < step_detection_threshold_l and (np.median(links_step_detection[x-3:x]) > step_detection_threshold_l) and (np.median(links_step_detection[x+1:x+5]) < step_detection_threshold_l) and len(IC_L) > 0:
                        if len(TO_L) == 0 or (time_stamps[x] - 0.3) > max(TO_L):
                            TO_L.append(time_stamps[x-1])
                
                for x in range(5, len(rechts_step_detection) - 5):
                    if rechts_step_detection[x] > step_detection_threshold_r and (np.median(rechts_step_detection[x-3:x]) < step_detection_threshold_r) and (np.median(rechts_step_detection[x+1:x+5]) > step_detection_threshold_r):
                        if len(IC_R) == 0 or (time_stamps[x] - 0.3) > max(IC_R):
                            IC_R.append(time_stamps[x])
                    if rechts_step_detection[x] < step_detection_threshold_r and (np.median(rechts_step_detection[x-3:x]) > step_detection_threshold_r) and (np.median(rechts_step_detection[x+1:x+5]) < step_detection_threshold_r) and len(IC_R) > 0:
                        if len(TO_R) == 0 or (time_stamps[x] - 0.3) > max(TO_R):
                            TO_R.append(time_stamps[x-1])
            

                # Bereken MPP per sensor over het aantal stappen
                MPP_L = np.zeros(aantal_sensors)
                MPP_R = np.zeros(aantal_sensors)
                for sensor_index in range(aantal_sensors):
                    sensor_data_L = []
                    sensor_data_R = []
                    for i in range(len(IC_L)):
                        IC_L_idx = np.where(raw_data[:, 0] == IC_L[i])[0]
                        TO_L_idx = np.where(raw_data[:, 0] == TO_L[i])[0]
                        if len(IC_L_idx) > 0 and len(TO_L_idx) > 0:
                            sensor_data_L.append(np.max(raw_data[IC_L_idx[0]:TO_L_idx[0], sensor_index]))
                        IC_R_idx = np.where(raw_data[:, 0] == IC_R[i])[0]
                        TO_R_idx = np.where(raw_data[:, 0] == TO_R[i])[0]
                        if len(IC_R_idx) > 0 and len(TO_R_idx) > 0:
                            sensor_data_R.append(np.max(raw_data[IC_R_idx[0]:TO_R_idx[0], sensor_index + aantal_sensors]))
                    MPP_L[sensor_index] = np.mean(sensor_data_L) if sensor_data_L else 0
                    MPP_R[sensor_index] = np.mean(sensor_data_R) if sensor_data_R else 0

                # Sensorposities (op basis van opgegeven coördinaten)
                sensor_positions1 = [
                    (224, 1116), (183, 1133), (149, 1142), (108, 1133), (70, 1116),
                    (254, 1043), (216, 1043), (181, 1043), (147, 1043), (117, 1043), (74, 1043), (36, 1043),
                    (265, 954), (224, 954), (192, 954), (149, 954), (113, 954), (81, 954), (34, 954),
                    (269, 874), (224, 874), (190, 874), (153, 874), (117, 874), (76, 874), (31, 874),
                    (267, 795), (231, 795), (196, 795), (153, 795), (113, 795), (76, 795), (31, 795),
                    (275, 710), (233, 710), (198, 710), (158, 710), (121, 710), (79, 710), (44, 710),
                    (278, 628), (233, 628), (194, 628), (160, 628), (121, 628), (81, 628), (42, 628),
                    (295, 555), (252, 555), (213, 555), (168, 555), (132, 555), (74, 555), (46, 555),
                    (327, 487), (275, 487), (228, 487), (181, 487), (136, 487), (87, 487), (38, 487),
                    (333, 423), (293, 423), (235, 423), (192, 423), (145, 423), (87, 423), (36, 423),
                    (342, 358), (301, 358), (248, 358), (205, 358), (143, 358), (96, 358), (44, 358),
                    (353, 301), (303, 301), (254, 301), (207, 301), (153, 301), (104, 301), (53, 301),
                    (353, 232), (308, 232), (258, 232), (222, 232), (173, 232), (126, 232), (79, 232),
                    (333, 168), (293, 168), (252, 168), (207, 168), (160, 168), (113, 168),
                    (301, 106), (256, 89), (216, 87), (164, 104)
                ]
                sensor_positions = [(x*1.5, y) for (x, y) in sensor_positions1]
                sensor_positions1 = [(x*1.5, y) for (x, y) in sensor_positions1]

        # Plot resultaten toevoegen
            fig, ax = plt.subplots(figsize=(6, 6))
            ax.set_xlim(0, 1250)
            ax.set_ylim(0, 1000)
            ax.invert_yaxis()
            ax.axis('off')
            ax.set_aspect('equal')
            ax.set_title(f'Mean Peak Pressure (MPP) per sensor')

            # Linker voet met waarden
            for idx, pos in enumerate(sensor_positions):
                color = 'red' if MPP_L[idx] > 200 else 'black'
                ax.text(pos[0], pos[1], str(int(MPP_L[idx])), ha='center', va='center', fontsize=8, color=color)

            # Rechter voet (gespiegeld met verschillende waarden)
            for idx, pos in enumerate(sensor_positions1):
                mirrored_pos = (1200 - pos[0], pos[1])
                color = 'red' if MPP_R[idx] > 200 else 'black'
                ax.text(mirrored_pos[0], mirrored_pos[1], str(int(MPP_R[idx])), ha='center', va='center', fontsize=8, color=color)

            # Embed de grafiek in tkinter GUI
            #for widget in self.plot_frame.winfo_children():
                #widget.destroy()



            # Controleer op hoge drukken binnen de maskers en toon het resultaat
            high_pressure_masks_L = []
            high_pressure_masks_R = []
            threshold = 200
            for mask_name, sensor_indices in masks.items():
                if any(MPP_L[idx - 1] > threshold for idx in sensor_indices):
                    high_pressure_masks_L.append(mask_name)
                if any(MPP_R[idx - 1] > threshold for idx in sensor_indices):
                    high_pressure_masks_R.append(mask_name)

            # Voeg advies toe per voet onder de hoge druk maskers
            def generate_advice(mask_names):
                advice = []
                if "Hallux" in mask_names:
                    advice.append("Replacement of top cover of insole + local removal of material in insole (Hallux)")
                    advice.append("Local cushioning in insole (Hallux)")
                if "Dig25" in mask_names:
                    advice.append("Replacement of top cover of insole (Dig2-5)")
                if "MTH1" in mask_names:
                    advice.append("Replacement of top cover of insole + local cushioning in insole (MTH1)")
                    advice.append("Replacement of top cover of insole + local removal of material in insole (MTH1)")
                if "MTH25" in mask_names:
                    advice.append("Replacement of top cover of insole + addition of a trans-metatarsal bar to insole (MTH25)") 
                    advice.append("Replacement of top cover of insole + local cushioning in insole (MTH25)")
                if "Midfoot" in mask_names:
                    advice.append("Replacement of top cover of insole (Midfoot)")
                    advice.append("Replacement of top cover of insole + repositioning of a metatarsal pad or bar in insole (Midfoot)")
                if "Heel" in mask_names:
                    advice.append("Replacement of top cover of insole + addition of a pad to insole (Heel)")
                    advice.append("Replacement of top cover of insole (Heel)")
                return advice

            # Genereer advies voor beide voeten
            advice_L = list(set(generate_advice(high_pressure_masks_L)))
            advice_R = list(set(generate_advice(high_pressure_masks_R)))

            def generate_high_pressure_text(side, masks, advice):
                text = f"Hoge druk {side} in: "
                if masks:
                    text += ', '.join(masks)
                    if advice:
                        text += "\nAdvies:\n"
                        text += '\n'.join([f"{i + 1}. {item}" for i, item in enumerate(advice)])
                    else:
                        text += "\nGeen specifieke adviezen."
                else:
                    text += "Geen"
                return text
            # Toon resultaten in Streamlit
            st.pyplot(fig)

            st.markdown("### Analyse linker voet")
            st.text(generate_high_pressure_text("links", high_pressure_masks_L, advice_L))

            st.markdown("### Analyse rechter voet")
            st.text(generate_high_pressure_text("rechts", high_pressure_masks_R, advice_R))

            # Teksten genereren
            high_pressure_text_L = generate_high_pressure_text("links", high_pressure_masks_L, advice_L)
            high_pressure_text_R = generate_high_pressure_text("rechts", high_pressure_masks_R, advice_R)
        except Exception as error:
            st.error("Er ging iets mis tijdens het verwerken van de meting.")
            st.text(traceback.format_exc())

    if st.button("Start analyse"):
        run_code_voor_meting(gekozen_meting, gekozen_bestand)