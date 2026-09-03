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

# Elenco dei 31 turni con BADGE EMOJI e relativi valori orari
turni_ore = {
    "⚪ RIPOSO": 0, 
    "⚪ SENZA TURNO": 0, 
    "⚪ PERMESSO RETR.": 0, 
    "⚪ FERIE": 0, 
    "⚪ MALATTIA": 0,
    "🟡 TOMM 06:30/14:30": 8.0, 
    "🟡 TOMM 14:30/22:30": 8.0, 
    "🟡 TOMM  22:30/06:30": 8.0,
    "🟡 TOMM 17:30/23:30": 6.0, 
    "🟡 TOMM 23:30/06:30": 7.0, 
    "🔵 TOM + PAL 06:30/14:30": 8.0,
    "🔵 TOM+PAL 14:30/22:30": 8.0, 
    "🟢 SIELTE 06/14": 8.0, 
    "🟢 SIELTE 14/22": 8.0, 
    "🟢 SIELTE 22/06": 8.0,
    "🟢 SIELTE 20/02": 6.0, 
    "🟢 SIELTE 02/08:30": 6.5, 
    "🟢 SIELTE 20/01": 5.0, 
    "🟢 SIELTE 01/06": 5.0,
    "🟢 SIELTE 06/15": 9.0, 
    "🟢 SIELTE 15/24": 9.0, 
    "🟢 SIELTE 24/08:30": 8.5, 
    "🟢 SIELTE 20/06": 10.0,
    "🟢 SIELTE 06/18": 12.0, 
    "🟢 SIELTE 18/06": 12.0, 
    "🟣 PALAZZO 06/14": 8.0, 
    "🟣 PALAZZO 14/22": 8.0,
    "🟣 PALAZZO 22/06": 8.0, 
    "🟣 PALAZZO 16/23": 7.0, 
    "🟣 PALAZZO 23/06": 7.0, 
    "🟣 PALAZZO 06/18": 12.0,
    "🔵 PAL+TOMM 14:30/22:00": 12.0
}

# ==============================================================================
# 🎨 FUNZIONE PER COLORARE LE CELLE DELLA TABELLA DI RIEPILOGO
# ==============================================================================
def colora_turni(valore):
    """Assegna un colore di sfondo CSS in base al badge emoji del turno."""
    if not isinstance(valore, str):
        return ""
    
    if valore.startswith("⚪"):
        return "background-color: #f0f2f6; color: #555555;"  
    elif valore.startswith("🟡"):
        return "background-color: #fff2cc; color: #b27a00;"  
    elif valore.startswith("🟢"):
        return "background-color: #e2f0d9; color: #385723;"  
    elif valore.startswith("🟣"):
        return "background-color: #e8daef; color: #6c3483;"  
    elif valore.startswith("🔵"):
        return "background-color: #ddebf7; color: #1f4e78;"  
    return ""

# ==============================================================================
# ⚙️ LOGICA E DATI DELL'APPLICAZIONE
# ==============================================================================
st.title("📅 Pianificazione e Ricerca Turni Personale")

# 1. SELEZIONE DELLA DATA E CALCOLO SETTIMANA
st.subheader("🗓️ Seleziona il Giorno o la Settimana")
data_scelta = st.date_input("Scegli un giorno sul calendario:", datetime.strptime("31/08/2026", "%d/%m/%Y").date())

# Forza il calcolo partendo sempre dal Lunedì della settimana selezionata
data_inizio = data_scelta - timedelta(days=data_scelta.weekday())  
FILE_SALVATAGGIO = f"salvataggio_turni_{data_inizio.strftime('%Y_%m_%d')}.csv"

giorni_nomi = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
giorni_formattati = [f"{giorno} {(data_inizio + timedelta(days=i)).strftime('%d/%m')}" for i, giorno in enumerate(giorni_nomi)]
lista_turni = list(turni_ore.keys())

giorno_selezionato_stringa = giorni_formattati[data_scelta.weekday()]
st.info(f"📆 Settimana: **da Lunedì {data_inizio.strftime('%d/%m/%Y')} a Domenica {(data_inizio + timedelta(days=6)).strftime('%d/%m/%Y')}** | Giorno selezionato: **{giorno_selezionato_stringa}**")

# Inizializzazione della sessione specifica per la data corrente
chiave_sessione = f"tabella_turni_{data_inizio.strftime('%Y_%m_%d')}"

if chiave_sessione not in st.session_state:
    dati_iniziali = {giorno: ["⚪ RIPOSO" for _ in dipendenti_ore] for giorno in giorni_formattati}
    df_struttura_attuale = pd.DataFrame(dati_iniziali, index=list(dipendenti_ore.keys()))
    
    if os.path.exists(FILE_SALVATAGGIO):
        try:
            df_caricato = pd.read_csv(FILE_SALVATAGGIO, index_col=0)
            for dipendente in df_struttura_attuale.index:
                for giorno in df_struttura_attuale.columns:
                    if dipendente in df_caricato.index and giorno in df_caricato.columns:
                        valore_file = df_caricato.at[dipendente, giorno]
                        # Controllo compatibilità vecchi file senza emoji badge
                        if valore_file in lista_turni:
                            df_struttura_attuale.at[dipendente, giorno] = valore_file
                        elif f"⚪ {valore_file}" in lista_turni:
                            df_struttura_attuale.at[dipendente, giorno] = f"⚪ {valore_file}"
                        elif f"🟡 {valore_file}" in lista_turni:
                            df_struttura_attuale.at[dipendente, giorno] = f"🟡 {valore_file}"
                        elif f"🟢 {valore_file}" in lista_turni:
                            df_struttura_attuale.at[dipendente, giorno] = f"🟢 {valore_file}"
                        elif f"🟣 {valore_file}" in lista_turni:
                            df_struttura_attuale.at[dipendente, giorno] = f"🟣 {valore_file}"
                        elif f"🔵 {valore_file}" in lista_turni:
                            df_struttura_attuale.at[dipendente, giorno] = f"🔵 {valore_file}"
            st.session_state[chiave_sessione] = df_struttura_attuale
        except Exception as e:
            st.session_state[chiave_sessione] = df_struttura_attuale
    else:
        st.session_state[chiave_sessione] = df_struttura_attuale

# --- BLOCCO FUNZIONE: COPIA DA SETTIMANA PRECEDENTE ---
data_settimana_scorsa = data_inizio - timedelta(weeks=1)
FILE_PRECEDENTE = f"salvataggio_turni_{data_settimana_scorsa.strftime('%Y_%m_%d')}.csv"

if os.path.exists(FILE_PRECEDENTE):
    if st.button("📋 Copia la pianificazione della settimana precedente su questa nuova settimana"):
        try:
            df_vecchio = pd.read_csv(FILE_PRECEDENTE, index_col=0)
            giorni_vecchi = df_vecchio.columns.tolist()
            
            for dipendente in st.session_state[chiave_sessione].index:
                for i in range(7):
                    giorno_nuovo = giorni_formattati[i]
                    giorno_vecchio = giorni_vecchi[i]
                    if dipendente in df_vecchio.index:
                        st.session_state[chiave_sessione].at[dipendente, giorno_nuovo] = df_vecchio.at[dipendente, giorno_vecchio]
            st.success("🔄 Turni duplicati con successo! Verifica i dati e ricordati di salvare in basso.")
            st.rerun()
        except Exception as e:
            st.error(f"Errore durante la copia dei vecchi dati: {e}")

df_inserimento = st.session_state[chiave_sessione].copy()

# 2. SEZIONE INTERFACCIA: SCELTA MODALITÀ DI VISTA
modo_vista = st.radio("Scegli come visualizzare/inserire i dati:", ["Visualizza Intera Settimana", "Visualizza Giorno Singolo"], horizontal=True)

if modo_vista == "Visualizza Giorno Singolo":
    st.subheader(f"🔍 Turni di: {giorno_selezionato_stringa}")
    for dipendente in df_inserimento.index:
        col_n, col_s = st.columns([1.5, 6])
        col_n.write(f"**{dipendente}**")
        valore_attuale = df_inserimento.at[dipendente, giorno_selezionato_stringa]
        if valore_attuale not in lista_turni:
            valore_attuale = "⚪ RIPOSO"
        scelta = col_s.selectbox(
            f"Singolo-{dipendente}", lista_turni, index=lista_turni.index(valore_attuale), label_visibility="collapsed",
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
                valore_attuale = "⚪ RIPOSO"
            scelta = cols_giorni[i].selectbox(
                f"{giorno}-{dipendente}", lista_turni, index=lista_turni.index(valore_attuale), label_visibility="collapsed",
                key=f"settimanale_{data_inizio.strftime('%Y%m%d')}_{dipendente}_{giorno}"
            )
            df_inserimento.at[dipendente, giorno] = scelta

st.session_state[chiave_sessione] = df_inserimento

# Pulsante unico per il salvataggio dei dati su file locale CSV
st.write("")
col_salva, _ = st.columns(2)
if col_salva.button("💾 SALVA MODIFICHE PERMANENTI", use_container_width=True):
    df_inserimento.to_csv(FILE_SALVATAGGIO)
    st.success(f"🎉 Dati aggiornati e salvati con successo per la settimana del {data_inizio.strftime('%d/%m/%Y')}!")

# 3. CONTEGGIO ORE E TABELLA REPORT FINALE
ore_lavorate_totali = []
differenze_totali = []

for dipendente in df_inserimento.index:
    ore_contrattuali = dipendenti_ore[dipendente]
    somma_ore_lavorate = sum(turni_ore[df_inserimento.at[dipendente, giorno]] for giorno in giorni_formattati)
    difference = somma_ore_lavorate - ore_contrattuali
    ore_lavorate_totali.append(somma_ore_lavorate)
    differenze_totali.append(difference)

df_report = df_inserimento.copy()
df_report.insert(0, "ORE CONTR.", [dipendenti_ore[d] for d in df_report.index])
df_report["ORE LAV."] = ore_lavorate_totali
df_report["DIFF."] = differenze_totali
