import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta

# Configurazione della pagina
st.set_page_config(page_title="Gestione Turni Personale", layout="wide")

# ==============================================================================
# 🎨 CONFIGURAZIONE COLORI PERSONALIZZATI PER OGNI DIPENDENTE
# ==============================================================================
colori_dipendenti = {
    "PERINO": "#fff2cc",       # Giallo tenue
    "GUARRAIA": "#e2efda",     # Verde chiaro
    "GULLO": "#fce4d6",        # Arancione/Pesca chiaro
    "SERIO A.": "#d9e1f2",     # Azzurro pastello
    "FERRUGGIA": "#e1d5e7",    # Lilla/Viola chiaro
    "COCUZZA": "#fff2cc",      # Giallo tenue
    "BENIGNO": "#f2f2f2",      # Grigio chiarissimo
    "NUCCIO": "#e6f7ff",       # Celeste chiaro
    "GAITA": "#fff7e6",        # Crema/Arancio chiarissimo
    "LION": "#f6ffed",         # Verde menta
    "DE JOMA": "#fff0f6"       # Rosa pallido
}

# Funzione interna per applicare i colori di sfondo alle righe dei dipendenti
def colora_righe(row):
    dipendente = row.name
    colore = colori_dipendenti.get(dipendente, "#ffffff")
    # Applica il colore a tutte le celle della riga (tranne la riga finale dei totali complessivi)
    if dipendente == "ORE DIPENTI":
        return ["background-color: #f2f2f2; font-weight: bold;"] * len(row)
    return [f"background-color: {colore};"] * len(row)

# ==============================================================================
# ⚙️ LOGICA E DATI DELL'APPLICAZIONE
# ==============================================================================
st.title("📅 Pianificazione Settimanale dei Turni")
st.write("Modifica i turni direttamente cliccando sulle celle della tabella. I totali si aggiornano all'istante.")

# Elenco dei dipendenti e ore contrattuali
dipendenti_ore = {
    "PERINO": 38, "GUARRAIA": 28, "GULLO": 30, "BENIGNO": 30,
    "NUCCIO": 0, "COCUZZA": 0, "GAITA": 0, "SERIO A.": 30,
    "FERRUGGIA": 24, "LION": 29, "DE JOMA": 0
}

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

giorni = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
lista_turni = list(turni_ore.keys())

# Inizializzazione dello stato della tabella
if "tabella_turni" not in st.session_state:
    dati_iniziali = {giorno: ["RIPOSO" for _ in dipendenti_ore] for giorno in giorni}
    st.session_state.tabella_turni = pd.DataFrame(dati_iniziali, index=list(dipendenti_ore.keys()))

# Configurazione delle colonne per il menu a tendina dentro la tabella interattiva
configurazione_colonne = {
    giorno: st.column_config.SelectboxColumn(
        giorno,
        options=lista_turni,
        required=True,
        width="medium"
    )
    for giorno in giorni
}

# ✍️ GRIGLIA INTERATTIVA DI INSERIMENTO COLORATA
st.subheader("✍️ Inserimento Turni Personale")

# Applichiamo lo stile dei colori alla griglia modificabile
df_colorato_inserimento = st.session_state.tabella_turni.style.apply(colora_righe, axis=1)

df_modificato = st.data_editor(
    df_colorato_inserimento,
    column_config=configurazione_colonne,
    use_container_width=True,
    key="editor_turni"
)

# Salviamo le modifiche effettuate dall'utente nello stato dell'app
st.session_state.tabella_turni = pd.DataFrame(df_modificato)

# ==============================================================================
# 📊 CALCOLO DEI TOTALI E DEI REPORT
# ==============================================================================
ore_lavorate_totali = []
differenze_totali = []

for dipendente in st.session_state.tabella_turni.index:
    ore_contrattuali = dipendenti_ore[dipendente]
    somma_ore_lavorate = sum(turni_ore[st.session_state.tabella_turni.at[dipendente, giorno]] for giorno in giorni)
    differenza = somma_ore_lavorate - ore_contrattuali
    ore_lavorate_totali.append(somma_ore_lavorate)
    differenze_totali.append(differenza)

# Creazione del report riassuntivo finale
df_report = st.session_state.tabella_turni.copy()
df_report.insert(0, "ORE CONTR.", [dipendenti_ore[d] for d in df_report.index])
df_report["ORE LAV."] = ore_lavorate_totali
df_report["DIFF."] = differenze_totali

# Calcolo automatico della riga finale ORE DIPENTI (Totale complessivo della ditta)
riga_totale = pd.Series(index=df_report.columns, dtype=object)
riga_totale["ORE CONTR."] = sum(dipendenti_ore.values())
riga_totale["ORE LAV."] = sum(ore_lavorate_totali)
riga_totale["DIFF."] = sum(differenze_totali)
for giorno in giorni:
    riga_totale[giorno] = ""

df_report.loc["ORE DIPENTI"] = riga_totale

# Mostra il report finale con la stessa formattazione colore coerente
st.subheader("📊 Riepilogo Calcoli e Totali del Personale")
st.dataframe(df_report.style.apply(colora_righe, axis=1), use_container_width=True)

# ==============================================================================
# 💾 ESPORTAZIONE EXCEL
# ==============================================================================
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
