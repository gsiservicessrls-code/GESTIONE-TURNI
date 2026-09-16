import streamlit as st
import pandas as pd
import io, os
from datetime import datetime, timedelta

st.set_page_config(page_title="Gestione Turni Personale", layout="wide")
FILE_SALVATAGGIO = "salvataggio_turni.csv"

dipendenti_ore = {
    "🟡 PERINO": 38, "🔵 SERIO A.": 30, "🟠 GULLO": 30, "🟢 GUARRAIA": 28, "🟣 FERRUGGIA": 24, 
    "⚪ BENIGNO": 0, "🟡 COCUZZA": 0, "🟤 DE JOMA": 0, "⚫ GAITA": 0, "🔵 NUCCIO": 0, "🟢 LION": 0        
}

# Elenco completo con la correzione del turno SIELTE 24:00/08:30
turni_ore = {
    "SENZA TURNO": 0.0, "RIPOSO": 0.0, "PERMESSO RETR.": 0.0, "FERIE": 0.0, "MALATTIA": 0.0,
    "TOMM 17:30/23:30": 6.0, "TOMM 23:30/06:30": 7.0,
    "PALAZZO 16:00/23:00": 7.0, "PALAZZO 23:00/06:00": 7.0,
    "SIELTE 20:00/02:00": 6.0, "SIELTE 02:00/08:30": 6.5,
    "SIELTE 20:00/01:00": 5.0, "SIELTE 01:00/06:00": 5.0,
    "TOM+PAL 06:30/14:30": 8.0, "TOM+PAL 14:30/22:30": 8.0,
    "TOMM 22:30/06:30": 8.0, "PALAZZO 22:30/06:30": 8.0,
    "SIELTE 06:30/14:30": 8.0, "SIELTE 14:30/22:30": 8.0, "SIELTE 22:30/06:30": 8.0,
    "SIELTE 06:30/15:30": 9.0, "SIELTE 15:30/24:30": 9.0, "SIELTE 24:00/08:30": 8.5
}

def colora_tipologia_turno(valore):
    if pd.isna(valore) or not isinstance(valore, str): return ""
    v = valore.upper().strip()
    if v == "MALATTIA": return "background-color: #fce8e6; color: #c5221f; font-weight: bold;"
    if v in ["RIPOSO", "SENZA TURNO", "FERIE", "PERMESSO RETR."]: return "background-color: #fef7e0; color: #b06000; font-weight: bold;"
    if "SIELTE" in v: return "background-color: #cceeff; color: #004466; font-weight: bold;"
    if "PALAZZO" in v or "PAL+" in v or "TOM+" in v: return "background-color: #ccffcc; color: #006600; font-weight: bold;"
    if "TOMM" in v or "TOM" in v: return "background-color: #f5e1c8; color: #5c3a21; font-weight: bold;"
    return ""

def aggiungi_emoji_menu(turno):
    v = turno.upper().strip()
    if v == "MALATTIA": return f"🔴 {turno}"
    if v in ["RIPOSO", "SENZA TURNO", "FERIE", "PERMESSO RETR."]: return f"🟡 {turno}"
    if "SIELTE" in v: return f"🔵 {turno}"
    if "PALAZZO" in v or "PAL+" in v or "TOM+" in v: return f"🟢 {turno}"
    if "TOMM" in v or "TOM" in v: return f"🟤 {turno}"
    return turno

def colora_delta(valore):
    if valore < 0: return "background-color: #fce8e6; color: #c5221f; font-weight: bold;"
    if valore > 0: return "background-color: #e6f4ea; color: #137333; font-weight: bold;"
    return "color: #5f6368;"

st.title("📅 Pianificazione Settimanale dei Turni")
st.subheader("🗓️ Seleziona la Settimana")
data_scelta = st.date_input("Scegli un giorno sul calendario:", datetime.strptime("31/08/2026", "%d/%m/%Y").date())
data_inizio = data_scelta - timedelta(days=data_scelta.weekday())  

giorni_nomi = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
giorni_formattati = [f"{g} {(data_inizio + timedelta(days=i)).strftime('%d/%m')}" for i, g in enumerate(giorni_nomi)]
lista_turni = list(turni_ore.keys())
lista_maiuscoli = [t.upper().strip() for t in lista_turni]

st.info(f"📆 Settimana attiva da **Lunedì {data_inizio.strftime('%d/%m/%Y')}** a **Domenica {(data_inizio + timedelta(days=6)).strftime('%d/%m/%Y')}**")
chiave_sessione = f"tabella_turni_{data_inizio.strftime('%Y_%m_%d')}"

if chiave_sessione not in st.session_state:
    df_struttura = pd.DataFrame({g: ["RIPOSO" for _ in dipendenti_ore] for g in giorni_formattati}, index=list(dipendenti_ore.keys()))
    if os.path.exists(FILE_SALVATAGGIO):
        try:
            df_caricato = pd.read_csv(FILE_SALVATAGGIO, index_col=0)
            for dip in df_struttura.index:
                for gio in df_struttura.columns:
                    if dip in df_caricato.index and gio in df_caricato.columns: df_struttura.at[dip, gio] = df_caricato.at[dip, gio]
        except: pass
    st.session_state[chiave_sessione] = df_struttura

with st.expander("📥 Importa Turni da File Esterno (Excel / CSV)", expanded=False):
    file_caricato = st.file_uploader("Scegli un file:", type=["xlsx", "csv"], key="uploader_turni")
    if file_caricato is not None:
        try:
            df_imp = pd.read_excel(file_caricato, index_col=0) if file_caricato.name.endswith(".xlsx") else pd.read_csv(file_caricato, index_col=0)
            df_imp.index = df_imp.index.astype(str).str.strip().str.upper()
            if st.button("🔄 Applica dati caricati alla settimana attiva", use_container_width=True):
                contatore = 0
                for dip_griglia in st.session_state[chiave_sessione].index:
                    dip_puro = dip_griglia.upper().strip()
                    dip_file = next((f for f in df_imp.index if f in dip_puro or dip_puro in f), None)
                    if dip_file is not None and df_imp.shape >= 7:
                        for i, g_griglia in enumerate(giorni_formattati):
                            valore_file = str(df_imp.iloc[df_imp.index.get_loc(dip_file), i]).strip().upper()
                            if valore_file in lista_maiuscoli:
                                turno_corretto = lista_turni[lista_maiuscoli.index(valore_file)]
                                st.session_state[chiave_sessione].at[dip_griglia, g_griglia] = turno_corretto
                                chiave_widget = f"wk_{data_inizio.strftime('%Y%m%d')}_{dip_griglia}_{g_griglia}"
                                st.session_state[chiave_widget] = turno_corretto
                                contatore += 1
                if contatore > 0:
                    st.success(f"🎉 Caricati {contatore} turni con successo!")
                    st.rerun()
                else: st.warning("⚠️ Nessun dato corrispondente trovato.")
        except Exception as e: st.error(f"❌ Errore: {e}")

df_inserimento = st.session_state[chiave_sessione].copy()

with st.expander("✍️ Apri il Pannello Inserimento Turni Personale", expanded=True):
    cols_header = st.columns([1.6, 1, 1, 1, 1, 1, 1, 1])
    cols_header.write("**Dipendenti**")
    for i, gf in enumerate(giorni_formattati): cols_header[i+1].write(f"**{gf}**")
    for dipendente in df_inserimento.index:
        col_nome, *cols_giorni = st.columns([1.6, 1, 1, 1, 1, 1, 1, 1])
        col_nome.write(f"**{dipendente}**")
        for i, giorno in enumerate(giorni_formattati):
            chiave_widget = f"wk_{data_inizio.strftime('%Y%m%d')}_{dipendente}_{giorno}"
            valore_attuale = df_inserimento.at[dipendente, giorno]
            scelta = cols_giorni[i].selectbox(
                f"{giorno}-{dipendente}", lista_turni, 
                index=lista_turni.index(valore_attuale if valore_attuale in lista_turni else "RIPOSO"), 
                format_func=aggiungi_emoji_menu, label_visibility="collapsed", 
                key=chiave_widget
            )
            df_inserimento.at[dipendente, giorno] = scelta

st.session_state[chiave_sessione] = df_inserimento
errori_rilevati = []
voci_escluse = ["RIPOSO", "SENZA TURNO", "FERIE", "MALATTIA", "PERMESSO RETR."]

for giorno in giorni_formattati:
    turni_giorno = df_inserimento[giorno].tolist()
    for turno in lista_turni:
        if turno not in voci_escluse and turni_giorno.count(turno) > 1:
            nomi_coinvolti = df_inserimento[df_inserimento[giorno] == turno].index.tolist()
            nomi_puliti = ", ".join([n.split()[-1] for n in nomi_coinvolti])
            errori_rilevati.append(f"⚠️ Il turno {turno} è duplicato tra: {nomi_puliti}.")

blocco_salvataggio = len(errori_rilevati) > 0
if errori_rilevati:
    st.error("### 🛑 Rilevati conflitti di assegnazione contemporanea:")
    for errore in errori_rilevati: st.write(errore)

st.write("")
col_salva, _ = st.columns(2)
if col_salva.button("💾 SALVA MODIFICHE PERMANENTI", use_container_width=True, disabled=blocco_salvataggio):
    df_inserimento.to_csv(FILE_SALVATAGGIO)
    st.success("🎉 Turni salvati nel file permanente!")
elif blocco_salvataggio: st.warning("🔒 Correggi la griglia per sbloccare il salvataggio.")

st.write("---")
st.header("📊 Resoconto Ore Settimanali")
ore_lavorate_settimana = [sum(turni_ore.get(df_inserimento.at[dip, g], 0.0) for g in giorni_formattati) for dip in df_inserimento.index]
df_ore = pd.DataFrame({"Ore Contrattuali": [dipendenti_ore[d] for d in df_inserimento.index], "Ore Svolte": ore_lavorate_settimana}, index=df_inserimento.index)
df_ore["Delta (Ore)"] = df_ore["Ore Svolte"] - df_ore["Ore Contrattuali"]

st.metric(label="Totalizzatore Ore Lavorate dalla Squadra", value=f"{df_ore['Ore Svolte'].sum():.1f} ore")
st.dataframe(df_ore.style.format("{:.1f}").map(colora_delta, subset=["Delta (Ore)"]), use_container_width=True)

st.write("---")
st.header("👀 Tabella Orari Applicata (Anteprima)")
st.dataframe(df_inserimento.style.map(colora_tipologia_turno), use_container_width=True)

st.write("")
st.subheader("📥 Esporta la Pianificazione")
col_csv, col_excel = st.columns(2)
csv_buffer = io.StringIO()
df_inserimento.to_csv(csv_buffer)
col_csv.download_button(label="📄 Scarica Turni in CSV", data=csv_buffer.getvalue(), file_name=f"turni_{data_inizio.strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)

try:
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        df_inserimento.to_excel(writer, sheet_name="Turni Settimanali")
        df_ore.to_excel(writer, sheet_name="Resoconto Ore")
    col_excel.download_button(label="🟢 Scarica Report Completo in Excel", data=excel_buffer.getvalue(), file_name=f"report_{data_inizio.strftime('%Y%m%d')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
except: col_excel.info("💡 Installa `openpyxl` per scaricare in formato Excel.")
