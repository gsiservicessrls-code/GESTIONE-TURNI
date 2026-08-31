import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta

# Configurazione della pagina
st.set_page_config(page_title="Gestione Turni Personale", layout="wide")

# ==============================================================================
# 🎨 NUOVO ORDINE DEI NOMINATIVI E ORE CONTRATTUALI (Punto 2)
# ==============================================================================
dipendenti_ore = {
    "🟡 PERINO": 38, 
    "🔵 SERIO A.": 30,
    "🟠 GULLO": 30, 
    "🟢 GUARRAIA": 28, 
    "🟣 FERRUGGIA": 24, 
    "喂 BENIGNO": 0,    # Impostato a 0 ore come richiesto
    "🟡 COCUZZA": 0, 
    "🟤 DE JOMA": 0,
    "⚫ GAITA": 0, 
    "🔵 NUCCIO": 0, 
    "🟢 LION": 0        # Impostato a 0 ore come richiesto
}

# ==============================================================================
# ⚙️ LOGICA E DATI DELL'APPLICAZIONE
# ==============================================================================
st.title("📅 Pianificazione Settimanale dei Turni")
st.write("Seleziona i turni dal menu. I calcoli e i totali si aggiornano in tempo reale.")

# Elenco completo di tutti i 31 turni e relativi valori orari
turni_ore = {
    "RIPOSO": 0, "SENZA TURNO": 0, "PERMESSO RETR.": 0, "FERIE": 0, "MALATTIA": 0,
    "TOMM 06:30/14:30": 8.0, "TOMM 14:30/22:30": 8.0, "TOMM  22:30/06:30": 8.0,
    "TOMM 17:30/23:30": 6.0, "TOMM 23:30/06:30": 7.0, "TOM + PAL 06:30/14:30": 8.0,
    "TOM+PAL 14:30/22:30": 8.0, "SIELTE 06/14": 8.0, "SIELTE 14/22": 8.0, "SIELTE 22/06": 8.0,
    "SIELTE 20/02": 6.0, "SIELTE 02/08:30": 6.5, "SIELTE 20/01": 5.0, "SIELTE 01/06": 5.0,
    "SIELTE 06/15": 9.0, "SIELTE 15/24": 9.0, "SIELTE 24/08:30": 8.5, "SIELTE 20/06": 10.0,
    "SIELTE 06/18": 12.0, "SIELTE 18/06": 12.0, "PALAZZO 06/14": 8.0, "PALAZZO 14/22": 8.0,
    "PALAZZO 22/06": 8.0, "PALAZZO 16/23": 7.0, "PALAZZO 23/06": 7.0, "PALAZZO 06/18": 12.0,
    "PAL+TOMM 14:30/22:00": 12.0
}

# GENERAZIONE DATE DINFAMICHE (Punto 1)
data_inizio = datetime.strptime("31/08/2026", "%d/%m/%Y")
giorni_nomi = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
giorni_formattati = []
colonne_report = []

for i, giorno in enumerate(giorni_nomi):
    data_corrente = data_inizio + timedelta(days=i)
    data_str = data_corrente.strftime("%d/%m")
    giorni_formattati.append(f"{giorno} {data_str}")
    colonne_report.append(f"{giorno} {data_str}")

lista_turni = list(turni_ore.keys())

# Inizializzazione della tabella
if "tabella_turni" not in st.session_state:
    dati_iniziali = {giorno: ["RIPOSO" for _ in dipendenti_ore] for giorno in giorni_formattati}
    st.session_state.tabella_turni = pd.DataFrame(dati_iniziali, index=list(dipendenti_ore.keys()))

df_inserimento = st.session_state.tabella_turni.copy()

# Generazione della griglia interattiva con date sopra le caselle
st.subheader("✍️ Inserimento Turni Personale")

# Riga di intestazione con i giorni e le date
cols_header = st.columns([1.5, 1, 1, 1, 1, 1, 1, 1])
cols_header[0].write("**Dipendenti**")
for i, gf in enumerate(giorni_formattati):
    cols_header[i+1].write(f"**{gf}**")

# Righe dei menu a tendina per dipendente
for dipendente in df_inserimento.index:
    col_nome, *cols_giorni = st.columns([1.5, 1, 1, 1, 1, 1, 1, 1])
    col_nome.write(f"**{dipendente}**")
    for i, giorno in enumerate(giorni_formattati):
        valore_attuale = df_inserimento.at[dipendente, giorno]
        if valore_attuale not in lista_turni:
            valore_attuale = "RIPOSO"
        scelta = cols_giorni[i].selectbox(
            f"{giorno}-{dipendente}", lista_turni, index=lista_turni.index(valore_attuale), label_visibility="collapsed"
        )
        df_inserimento.at[dipendente, giorno] = scelta

st.session_state.tabella_turni = df_inserimento

# Calcolo dei totali
ore_lavorate_totali = []
differenze_totali = []

for dipendente in df_inserimento.index:
    ore_contrattuali = dipendenti_ore[dipendente]
    somma_ore_lavorate = sum(turni_ore[df_inserimento.at[dipendente, giorno]] for giorno in giorni_formattati)
    differenza = somma_ore_lavorate - ore_contrattuali
    ore_lavorate_totali.append(somma_ore_lavorate)
    differenze_totali.append(differenza)

# Creazione del report riassuntivo finale con le nuove intestazioni data
df_report = df_inserimento.copy()
df_report.insert(0, "ORE CONTR.", [dipendenti_ore[d] for d in df_report.index])
df_report["ORE LAV."] = ore_lavorate_totali
df_report["DIFF."] = differenze_totali

# Calcolo automatico della riga finale ORE DIPENTI
riga_totale = pd.Series(index=df_report.columns, dtype=object)
riga_totale["ORE CONTR."] = sum(dipendenti_ore.values())
riga_totale["ORE LAV."] = sum(ore_lavorate_totali)
riga_totale["DIFF."] = sum(differenze_totali)
for giorno in giorni_formattati:
    riga_totale[giorno] = ""

df_report.loc["ORE DIPENTI"] = riga_totale

st.subheader("📊 Riepilogo Calcoli e Totali del Personale")
st.dataframe(df_report, use_container_width=True)

# Generazione del file Excel per il download
st.subheader("💾 Esporta i Dati Compilati")

output = io.BytesIO()
with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
    df_report.to_excel(writer, sheet_name="Turni Settimanali")
    writer.close()
dati_excel = output.getvalue()

st.download_button(
    label="🟢 Scarica i turni inseriti in Excel (.xlsx)",
    data=dati_excel,
    file_name="Turni_Settimanali_Calcolati.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
