import streamlit as st
import pandas as pd
import io
import os
from datetime import datetime, timedelta

# Configurazione della pagina (Wide mode forza lo schermo intero orizzontale)
st.set_page_config(page_title="Gestione Turni Personale", layout="wide")

# File locale unico centralizzato per evitare frammentazioni dei dati
FILE_SALVATAGGIO = "salvataggio_turni.csv"

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
# 🎨 FUNZIONI GRAFICHE E DI COLORE
# ==============================================================================
def colora_tipologia_turno(valore):
    if pd.isna(valore) or not isinstance(valore, str): return ""
    v = valore.upper().strip()
    if v == "": return ""
    
    if v == "MALATTIA":
        return "background-color: #fce8e6; color: #c5221f; font-weight: bold;"
    elif v in ["RIPOSO", "SENZA TURNO", "FERIE", "PERMESSO RETR."]:
        return "background-color: #fef7e0; color: #b06000; font-weight: bold;"
    elif "SIELTE" in v:
        return "background-color: #cceeff; color: #004466; font-weight: bold;"
    elif "PALAZZO" in v or v == "PAL+TOMM 14:30/22:00":
        return "background-color: #ccffcc; color: #006600; font-weight: bold;"
    elif "TOMM" in v or "TOM" in v:
        return "background-color: #f5e1c8; color: #5c3a21; font-weight: bold;"
    return ""

def aggiungi_emoji_menu(turno):
    v = turno.upper().strip()
    if v == "MALATTIA": return f"🔴 {turno}"
    elif v in ["RIPOSO", "SENZA TURNO", "FERIE", "PERMESSO RETR."]: return f"🟡 {turno}"
    elif "SIELTE" in v: return f"🔵 {turno}"
    elif "PALAZZO" in v or v == "PAL+TOMM 14:30/22:00": return f"🟢 {turno}"
    elif "TOMM" in v or "TOM" in v: return f"🟤 {turno}"
    return turno

# ==============================================================================
# ⚙️ LOGICA CALCOLO DATA E CARICAMENTO FILE
# ==============================================================================
st.title("📅 Pianificazione Settimanale dei Turni")

st.subheader("🗓️ Seleziona la Settimana")
data_scelta = st.date_input("Scegli un giorno sul calendario:", datetime.strptime("31/08/2026", "%d/%m/%Y").date())
data_inizio = data_scelta - timedelta(days=data_scelta.weekday())  

giorni_nomi = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
giorni_formattati = [f"{giorno} {(data_inizio + timedelta(days=i)).strftime('%d/%m')}" for i, giorno in enumerate(giorni_nomi)]
lista_turni = list(turni_ore.keys())

st.info(f"📆 Settimana attiva da **Lunedì {data_inizio.strftime('%d/%m/%Y')}** a **Domenica {(data_inizio + timedelta(days=6)).strftime('%d/%m/%Y')}**")

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
        except:
            st.session_state[chiave_sessione] = df_struttura_attuale
    else:
        st.session_state[chiave_sessione] = df_struttura_attuale

df_inserimento = st.session_state[chiave_sessione].copy()

# ==============================================================================
# ✍️ GRIGLIA UNICA DI INSERIMENTO SETTIMANALE
# ==============================================================================
with st.expander("✍️ Apri il Pannello Inserimento Turni Personale", expanded=True):
    # Genera l'intestazione orizzontale bloccata delle colonne
    cols_header = st.columns([1.6, 1, 1, 1, 1, 1, 1, 1])
    cols_header[0].write("**Dipendenti**")
    for i, gf in enumerate(giorni_formattati): 
        cols_header[i+1].write(f"**{gf}**")

    # Inserimento righe per ciascun dipendente affiancate sulla stessa linea
    for dipendente in df_inserimento.index:
        col_nome, *cols_giorni = st.columns([1.6, 1, 1, 1, 1, 1, 1, 1])
        col_nome.write(f"**{dipendente}**")
        for i, giorno in enumerate(giorni_formattati):
            valore_attuale = df_inserimento.at[dipendente, giorno]
            
            scelta = cols_giorni[i].selectbox(
                f"{giorno}-{dipendente}", lista_turni, 
                index=lista_turni.index(valore_attuale if valore_attuale in lista_turni else "RIPOSO"), 
                format_func=aggiungi_emoji_menu, label_visibility="collapsed", 
                key=f"wk_{data_inizio.strftime('%Y%m%d')}_{dipendente}_{giorno}"
            )
            df_inserimento.at[dipendente, giorno] = scelta

st.session_state[chiave_sessione] = df_inserimento

# ==============================================================================
# 🚨 CONTROLLO UNICITÀ CONTEMPORANEA DEI TURNI
# ==============================================================================
errori_rilevati = []
voci_escluse = ["RIPOSO", "SENZA TURNO", "FERIE", "MALATTIA", "PERMESSO RETR."]

for giorno in giorni_formattati:
    turni_giorno = df_inserimento[giorno].tolist()
    for turno in lista_turni:
        if turno not in voci_escluse:
            conteggio = turni_giorno.count(turno)
            if conteggio > 1:
                st.session_state["conflitto_rilevato"] = True
                nomi_coinvolti = df_inserimento[df_inserimento[giorno] == turno].index.tolist()
                nomi_puliti = ", ".join([n.split()[-1] for n in nomi_coinvolti])
                errori_rilevati.append(f"⚠️ **{giorno.split()[0]}**: Il turno **{turno}** è duplicato tra: {nomi_puliti}.")

blocco_salvataggio = False
if errori_rilevati:
    blocco_salvataggio = True
    st.error("### 🛑 Rilevati conflitti di assegnazione contemporanea:")
    for errore in errori_rilevati:
        st.write(errore)

# ==============================================================================
# 💾 PULSANTE DI SALVATAGGIO CENTRALIZZATO
# ==============================================================================
st.write("")
col_salva, _ = st.columns(2)
if col_salva.button("💾 SALVA MODIFICHE PERMANENTI", use_container_width=True, disabled=blocco_salvataggio):
    df_inserimento.to_csv(FILE_SALVATAGGIO)
    st.success(f"🎉 Turni salvati correttamente nel file unico permanente!")
elif blocco_salvataggio:
    st.warning("🔒 Assegnazioni duplicate rilevate. Correggi la griglia per sbloccare il salvataggio.")

# ==============================================================================
# 📊 CALCOLO DEI TOTALI E TABELLONE FINALE COLORATO
# ==============================================================================
ore_lavorate_totali = []
differenze_totali = []

for dipendente in df_inserimento.index:
    ore_contrattuali = dipendenti_ore[dipendente]
    somma_ore_lavorate = sum(turni_ore[df_inserimento.at[dipendente, giorno]] for giorno in giorni_formattati)
    ore_lavorate_totali.append(somma_ore_lavorate)
    differenze_totali.append(somma_ore_lavorate - ore_contrattuali)

df_report = df_inserimento.copy()
df_report.insert(0, "ORE CONTR.", [dipendenti_ore[d] for d in df_report.index])
df_report["ORE LAV."] = ore_lavorate_totali
df_report["DIFF."] = differenze_totali

riga_totale = pd.Series(index=df_report.columns, dtype=object)
riga_totale["ORE CONTR."] = sum(dipendenti_ore.values())
riga_totale["ORE LAV."] = sum(ore_lavorate_totali)
riga_totale["DIFF."] = sum(differenze_totali)
for giorno in giorni_formattati: riga_totale[giorno] = ""

df_report.loc["ORE DIPENDENTI"] = riga_totale

st.subheader("📊 Riepilogo Calcoli e Totali del Personale (Tabellone Unificato)")
df_style = df_report.style.map(colora_tipologia_turno, subset=giorni_formattati)
st.dataframe(df_style, use_container_width=True)

# Generazione file Excel per il download
st.subheader("💾 Esporta i Dati Compilati")
output = io.BytesIO()
with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
    df_report.to_excel(writer, sheet_name="Turni Settimanali")

st.download_button(
    label="🟢 Scarica i turni inseriti in Excel (.xlsx)", data=output.getvalue(),
    file_name=f"Turni_Settimana_{data_inizio.strftime('%Y_%m_%d')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
