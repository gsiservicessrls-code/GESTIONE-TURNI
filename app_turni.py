import streamlit as st
import pandas as pd
import io
import os
from datetime import datetime, timedelta

# Configurazione della pagina
st.set_page_config(page_title="Gestione Turni Personale", layout="wide")

# ==============================================================================
# 🎨 ORDINE DEI NOMINATIVI E ORE CONTRATTUALI
# ==============================================================================
dipendenti_ore = {
    "🟡 PERINO": 38, 
    "🔵 SERIO A.": 30,
    "🟠 GULLO": 30, 
    "🟢 GUARRAIA": 28, 
    "🟣 FERRUGGIA": 24, 
    "⚪ BENIGNO": 0,    
    "🟡 COCUZZA": 0, 
    "🟤 DE JOMA": 0,
    "⚫ GAITA": 0, 
    "🔵 NUCCIO": 0, 
    "🟢 LION": 0        
}

# Elenco dei 31 turni e relativi valori orari
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

# ==============================================================================
# 🎨 FUNZIONE CONDIZIONALE CON LA NUOVA SEQUENZA DI COLORI
# ==============================================================================
def colora_tipologia_turno(valore):
    """Restituisce lo stile CSS con i colori esatti richiesti dall'utente."""
    if not isinstance(valore, str):
        return ""
    
    v = valore.upper().strip()
    
    # 1. Priorità alle voci SIELTE (Celeste)
    if "SIELTE" in v:
        return "background-color: #cceeff; color: #004466; font-weight: bold;"  # Celeste
    
    # 2. Voci PALAZZO (Verde)
    elif "PALAZZO" in v or v == "PAL+TOMM 14:30/22:00":
        return "background-color: #ccffcc; color: #006600; font-weight: bold;"  # Verde
    
    # 3. Voci TOMM rimanenti (Marrone Chiaro)
    elif "TOMM" in v or "TOM" in v:
        return "background-color: #f5e1c8; color: #5c3a21; font-weight: bold;"  # Marrone chiaro
        
    # 4. Stati generici (Riposi in Grigio, Assenze in Rosso)
    elif v in ["RIPOSO", "SENZA TURNO"]:
        return "background-color: #f2f4f7; color: #5a626a;"  # Grigio
    elif v in ["FERIE", "MALATTIA", "PERMESSO RETR."]:
        return "background-color: #fce8e6; color: #c5221f;"  # Rosso/Rosa chiaro
        
    return ""

# ==============================================================================
# ⚙️ LOGICA E DATI DELL'APPLICAZIONE
# ==============================================================================
st.title("📅 Pianificazione Settimanale dei Turni")
st.write("Seleziona i turni dal menu. I calcoli si aggiornano in tempo reale. Usa il tasto **Salva** in fondo per memorizzare i dati.")

# Selettore della data dal calendario
st.subheader("🗓️ Seleziona la Settimana e la Vista")
data_scelta = st.date_input("Scegli un giorno sul calendario:", datetime.strptime("31/08/2026", "%d/%m/%Y").date())

# Calcolo automatico del Lunedì della settimana selezionata
data_inizio = data_scelta - timedelta(days=data_scelta.weekday())  
FILE_SALVATAGGIO = f"salvataggio_turni_{data_inizio.strftime('%Y_%m_%d')}.csv"

giorni_nomi = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
giorni_formattati = [f"{giorno} {(data_inizio + timedelta(days=i)).strftime('%d/%m')}" for i, giorno in enumerate(giorni_nomi)]
lista_turni = list(turni_ore.keys())

giorno_selezionato_stringa = giorni_formattati[data_scelta.weekday()]
st.info(f"📆 Settimana attiva da **Lunedì {data_inizio.strftime('%d/%m/%Y')}** a **Domenica {(data_inizio + timedelta(days=6)).strftime('%d/%m/%Y')}** | Giorno corrente sul calendario: **{giorno_selezionato_stringa}**")

# Inizializzazione session_state legata in modo univoco alla settimana scelta
chiave_sessione = f"tabella_turni_{data_inizio.strftime('%Y_%m_%d')}"

if chiave_sessione not in st.session_state:
    dati_iniziali = {giorno: ["RIPOSO" for _ in dipendenti_ore] for giorno in giorni_formattati}
    df_struttura_attuale = pd.DataFrame(dati_iniziali, index=list(dipendenti_ore.keys()))
    
    if os.path.exists(FILE_SALVATAGGIO):
        try:
            df_caricato = pd.read_csv(FILE_SALVATAGGIO, index_col=0)
            for dipendente in df_struttura_attuale.index:
                for giorno in df_struttura_attuale.columns:
                    if dipendente in df_caricato.index and giorno in df_caricato.columns:
                        df_struttura_attuale.at[dipendente, giorno] = df_caricato.at[dipendente, giorno]
            st.session_state[chiave_sessione] = df_struttura_attuale
            st.toast("🔄 Ultimi dati salvati caricati con successo!", icon="ℹ️")
        except Exception as e:
            st.error(f"⚠️ Errore nel recupero del file salvato. Dettaglio: {e}")
            st.session_state[chiave_sessione] = df_struttura_attuale
    else:
        st.session_state[chiave_sessione] = df_struttura_attuale

df_inserimento = st.session_state[chiave_sessione].copy()

# Selettore di modalità vista
modo_vista = st.radio("Scegli come inserire/visualizzare i dati nella griglia:", ["Visualizza Intera Settimana", "Visualizza Giorno Singolo"], horizontal=True)

if modo_vista == "Visualizza Giorno Singolo":
    st.subheader(f"✍️ Inserimento Turni di: {giorno_selezionato_stringa}")
    cols_header = st.columns([1.5, 6])
    cols_header.write("**Dipendenti**")
    cols_header.write(f"**Turno {giorno_selezionato_stringa}**")
    
    for dipendente in df_inserimento.index:
        col_nome, col_scelta = st.columns([1.5, 6])
        col_nome.write(f"**{dipendente}**")
        
        valore_attuale = df_inserimento.at[dipendente, giorno_selezionato_stringa]
        if valore_attuale not in lista_turni:
            valore_attuale = "RIPOSO"
            
        scelta = col_scelta.selectbox(
            f"singolo_{dipendente}_{giorno_selezionato_stringa}", 
            lista_turni, 
            index=lista_turni.index(valore_attuale), 
            label_visibility="collapsed",
            key=f"singolo_{data_inizio.strftime('%Y%m%d')}_{dipendente}_{giorno_selezionato_stringa}"
        )
        df_inserimento.at[dipendente, giorno_selezionato_stringa] = scelta
else:
    st.subheader("✍️ Inserimento Turni Settimanale")
    cols_header = st.columns([1.5, 1, 1, 1, 1, 1, 1, 1])
    cols_header.write("**Dipendenti**")
    for i, gf in enumerate(giorni_formattati):
        cols_header[i+1].write(f"**{gf}**")

    for dipendente in df_inserimento.index:
        col_nome, *cols_giorni = st.columns([1.5, 1, 1, 1, 1, 1, 1, 1])
        col_nome.write(f"**{dipendente}**")
        for i, giorno in enumerate(giorni_formattati):
            valore_attuale = df_inserimento.at[dipendente, giorno]
            if valore_attuale not in lista_turni:
                valore_attuale = "RIPOSO"
            
            scelta = cols_giorni[i].selectbox(
                f"{giorno}-{dipendente}", 
                lista_turni, 
                index=lista_turni.index(valore_attuale), 
                label_visibility="collapsed",
                key=f"settimanale_{data_inizio.strftime('%Y%m%d')}_{dipendente}_{giorno}"
            )
            df_inserimento.at[dipendente, giorno] = scelta

st.session_state[chiave_sessione] = df_inserimento

# Sezione pulsante di salvataggio permanente
st.write("")
col_salva, _ = st.columns(2)
if col_salva.button("💾 SALVA MODIFICHE PERMANENTI", use_container_width=True):
    df_inserimento.to_csv(FILE_SALVATAGGIO)
    st.success(f"🎉 Turni salvati con successo per la settimana del {data_inizio.strftime('%d/%m/%Y')}!")

# Calcolo dei totali orari
ore_lavorate_totali = []
differenze_totali = []

for dipendente in df_inserimento.index:
    ore_contrattuali = dipendenti_ore[dipendente]
    somma_ore_lavorate = sum(turni_ore[df_inserimento.at[dipendente, giorno]] for giorno in giorni_formattati)
    differenza = somma_ore_lavorate - ore_contrattuali
    ore_lavorate_totali.append(somma_ore_lavorate)
    differenze_totali.append(differenza)

df_report = df_inserimento.copy()
df_report.insert(0, "ORE CONTR.", [dipendenti_ore[d] for d in df_report.index])
df_report["ORE LAV."] = ore_lavorate_totali
df_report["DIFF."] = differenze_totali

riga_totale = pd.Series(index=df_report.columns, dtype=object)
riga_totale["ORE CONTR."] = sum(dipendenti_ore.values())
riga_totale["ORE LAV."] = sum(ore_lavorate_totali)
riga_totale["DIFF."] = sum(differenze_totali)
for giorno in giorni_formattati:
    riga_totale[giorno] = ""

df_report.loc["ORE DIPENDENTI"] = riga_totale

# Applicazione del tabellone colorato con la sequenza personalizzata
st.subheader("📊 Riepilogo Calcoli e Totali del Personale (Colori Personalizzati)")
df_style = df_report.style.applymap(colora_tipologia_turno, subset=giorni_formattati)
st.dataframe(df_style, use_container_width=True)

# Esportazione Excel
st.subheader("💾 Esporta i Dati Compilati")
output = io.BytesIO()
with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
    df_report.to_excel(writer, sheet_name="Turni Settimanali")
dati_excel = output.getvalue()

st.download_button(
    label="🟢 Scarica i turni inseriti in Excel (.xlsx)",
    data=dati_excel,
    file_name=f"Turni_Settimana_{data_inizio.strftime('%Y_%m_%d')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
