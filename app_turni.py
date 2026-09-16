import streamlit as st
import pandas as pd
import io, os
from datetime import datetime, timedelta

st.set_page_config(page_title="Gestione Turni", layout="wide")
FILE_SALVATAGGIO = "salvataggio_turni.csv"

dipendenti_ore = {
    "🟡 PERINO": 38, "🔵 SERIO A.": 30, "🟠 GULLO": 30, "🟢 GUARRAIA": 28, "🟣 FERRUGGIA": 24, 
    "⚪ BENIGNO": 0, "🟡 COCUZZA": 0, "🟤 DE JOMA": 0, "⚫ GAITA": 0, "🔵 NUCCIO": 0, "🟢 LION": 0        
}

turni_ore = {
    "SENZA TURNO": 0.0, "RIPOSO": 0.0, "PERMESSO RETR.": 0.0, "FERIE": 0.0, "MALATTIA": 0.0,
    "TOMM 17:30/23:30": 6.0, "TOMM 23:30/06:30": 7.0, "PALAZZO 16:00/23:00": 7.0, "PALAZZO 23:00/06:00": 7.0,
    "PALAZZO 16:30/23:30": 7.0, "SIELTE 20:00/02:00": 6.0, "SIELTE 02:00/08:30": 6.5,
    "SIELTE 20:00/01:00": 5.0, "SIELTE 01:00/06:00": 5.0, "TOM+PAL 06:30/14:30": 8.0,
    "TOM+PAL 14:30/22:30": 8.0, "TOMM 22:30/06:30": 8.0, "PALAZZO 22:30/06:30": 8.0,
    "SIELTE 06:30/14:30": 8.0, "SIELTE 14:30/22:30": 8.0, "SIELTE 22:30/06:30": 8.0,
    "SIELTE 06:30/15:30": 9.0, "SIELTE 15:30/24:30": 9.0, "SIELTE 24:00/08:30": 8.5
}

def filtra_turni_dipendente(d, g_nome):
    is_wk, t_all = g_nome in ["Sabato", "Domenica"], list(turni_ore.keys())
    b = ["RIPOSO", "SENZA TURNO", "FERIE", "MALATTIA", "PERMESSO RETR."]
    if "PERINO" in d: return b + [t for t in t_all if "SIELTE" in t or t in (["TOM+PAL 06:30/14:30", "TOM+PAL 14:30/22:30"] if is_wk else ["PALAZZO 16:30/23:30", "TOMM 17:30/23:30"])]
    if "FERRUGGIA" in d or "SERIO A." in d: return b + [t for t in t_all if "SIELTE" in t]
    if "BENIGNO" in d: return b + [t for t in t_all if any(x in t for x in ["22:30/", "23:00/", "23:30/", "24:00/", "01:00/", "02:00/"])]
    if "GULLO" in d: return t_all if is_wk else b + [t for t in t_all if any(x in t for x in ["16:00/", "16:30/", "17:30/", "20:00/"])]
    if "COCUZZA" in d:
        if is_wk: return b + [t for t in t_all if t in ["PALAZZO 22:30/06:30", "TOM+PAL 14:30/22:30"]]
        return b + [t for t in t_all if "PALAZZO" in t or "TOM+PAL" in t]
    if "GUARRAIA" in d: return b + [t for t in t_all if "06:30/" in t] if is_wk else b + [t for t in t_all if any(x in t for x in ["22:30/", "23:00/", "23:30/", "24:00/", "01:00/", "02:00/"])]
    return t_all

def colora_tipologia_turno(valore):
    if pd.isna(valore) or not isinstance(valore, str): return ""
    v = valore.upper().strip()
    if v == "MALATTIA": return "background-color: #fce8e6; color: #c5221f; font-weight: bold;"
    if v in ["RIPOSO", "SENZA TURNO", "FERIE", "PERMESSO RETR."]: return "background-color: #fef7e0; color: #b06000; font-weight: bold;"
    if "SIELTE" in v: return "background-color: #cceeff; color: #004466; font-weight: bold;"
    if "PALAZZO" in v or "PAL+" in v or "TOM+" in v: return "background-color: #ccffcc; color: #006600; font-weight: bold;"
    if "TOMM" in v or "TOM" in v: return "background-color: #f5e1c8; color: #5c3a21; font-weight: bold;"
    return ""

def aggiungi_emoji_menu(t):
    v = t.upper().strip()
    if v == "MALATTIA": return f"🔴 {t}"
    if v in ["RIPOSO", "SENZA TURNO", "FERIE", "PERMESSO RETR."]: return f"🟡 {t}"
    return f"🔵 {t}" if "SIELTE" in v else f"🟢 {t}" if ("PALAZZO" in v or "PAL+" in v or "TOM+" in v) else f"🟤 {t}"

st.title("📅 Pianificazione Settimanale dei Turni")
data_scelta = st.date_input("Scegli un giorno:", datetime.strptime("21/09/2026", "%d/%m/%Y").date())
data_inizio = data_scelta - timedelta(days=data_scelta.weekday())  

giorni_nomi = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
giorni_formattati = [f"{g} {(data_inizio + timedelta(days=i)).strftime('%d/%m')}" for i, g in enumerate(giorni_nomi)]
lista_turni, lista_maiuscoli = list(turni_ore.keys()), [t.upper().strip() for t in turni_ore.keys()]

st.info(f"📆 Settimana attiva: da **Lunedì {data_inizio.strftime('%d/%m/%Y')}** a **Domenica {(data_inizio + timedelta(days=6)).strftime('%d/%m/%Y')}**")
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
    file_caricato = st.file_uploader("Carica un file:", type=["xlsx", "csv"], key="uploader_turni")
    if file_caricato is not None and st.button("🔄 Applica dati caricati", use_container_width=True):
        try:
            df_imp = pd.read_excel(file_caricato, index_col=0) if file_caricato.name.endswith(".xlsx") else pd.read_csv(file_caricato, index_col=0)
            df_imp.index = df_imp.index.astype(str).str.strip().str.upper()
            contatore = 0
            for dg in st.session_state[chiave_sessione].index:
                df_file = next((f for f in df_imp.index if f in dg.upper().strip() or dg.upper().strip() in f), None)
                if df_file is not None and df_imp.shape >= 7:
                    for i, gg in enumerate(giorni_formattati):
                        valore_file = str(df_imp.iloc[df_imp.index.get_loc(df_file), i]).strip().upper()
                        if valore_file in lista_maiuscoli:
                            tc = lista_turni[lista_maiuscoli.index(valore_file)]
                            st.session_state[chiave_sessione].at[dg, gg] = tc
                            st.session_state[f"wk_{data_inizio.strftime('%Y%m%d')}_{dg}_{gg}"] = tc
                            contatore += 1
            st.success(f"🎉 Caricati {contatore} turni!"); st.rerun()
        except Exception as e: st.error(f"❌ Errore: {e}")

df_inserimento = st.session_state[chiave_sessione].copy()

with st.expander("✍️ Apri il Pannello Inserimento Turni Personale", expanded=True):
    cols_header = st.columns([1.6, 1, 1, 1, 1, 1, 1, 1])
    cols_header[0].write("**Dipendenti**") # CORRETTO: Aggiunto l'indice per la colonna dei dipendenti
    for i, gf in enumerate(giorni_formattati): cols_header[i+1].write(f"**{gf}**")
    for dipendente in df_inserimento.index:
        col_nome, *cols_giorni = st.columns([1.6, 1, 1, 1, 1, 1, 1, 1])
        col_nome.write(f"**{dipendente}**")
        for i, giorno in enumerate(giorni_formattati):
            kw = f"wk_{data_inizio.strftime('%Y%m%d')}_{dipendente}_{giorno}"
            val = df_inserimento.at[dipendente, giorno]
            p_turni = filtra_turni_dipendente(dipendente, giorni_nomi[i])
            if val not in p_turni: val = "RIPOSO"
            df_inserimento.at[dipendente, giorno] = cols_giorni[i].selectbox(f"{giorno}-{dipendente}", p_turni, index=p_turni.index(val), format_func=aggiungi_emoji_menu, label_visibility="collapsed", key=kw)

st.session_state[chiave_sessione] = df_inserimento
errori_rilevati = [f"⚠️ {gi.split()}: {tu} è duplicato." for gi in giorni_formattati for tu in lista_turni if tu not in ["RIPOSO", "SENZA TURNO", "FERIE", "MALATTIA", "PERMESSO RETR."] and df_inserimento[gi].tolist().count(tu) > 1]

if errori_rilevati:
    st.error("### 🛑 Conflitti di assegnazione:")
    for errore in errori_rilevati: st.write(errore)

st.write("")
if st.columns(2)[0].button("💾 SALVA MODIFICHE PERMANENTI", use_container_width=True, disabled=len(errori_rilevati) > 0):
    df_inserimento.to_csv(FILE_SALVATAGGIO); st.success("🎉 Turni salvati!")

st.write("---")
st.header("📊 Resoconto Ore Settimanali")
ore_l = [sum(turni_ore.get(df_inserimento.at[d, g], 0.0) for g in giorni_formattati) for d in df_inserimento.index]
df_ore = pd.DataFrame({"Ore Contrattuali": [dipendenti_ore[d] for d in df_inserimento.index], "Ore Svolte": ore_l, "Delta (Ore)": [ol - dipendenti_ore[d] for d, ol in zip(df_inserimento.index, ore_l)]}, index=df_inserimento.index)
st.metric(label="Totalizzatore Ore Lavorate dalla Squadra", value=f"{sum(ore_l):.1f} ore")
st.dataframe(df_ore.style.format("{:.1f}").map(lambda v: "background-color: #fce8e6; color: #c5221f; font-weight: bold;" if v < 0 else "background-color: #e6f4ea; color: #137333; font-weight: bold;" if v > 0 else "color: #5f6368;", subset=["Delta (Ore)"]), use_container_width=True)

st.write("---")
col_csv, col_excel = st.columns(2)
csv_buf = io.StringIO(); df_inserimento.to_csv(csv_buf)
col_csv.download_button(label="📄 Scarica in CSV", data=csv_buf.getvalue(), file_name=f"turni_{data_inizio.strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)

try:
    ex_buf = io.BytesIO()
    with pd.ExcelWriter(ex_buf, engine="openpyxl") as w:
        df_inserimento.to_excel(w, sheet_name="Turni")
        df_ore.to_excel(w, sheet_name="Ore")
    col_excel.download_button(label="🟢 Scarica in Excel", data=ex_buf.getvalue(), file_name=f"report_{data_inizio.strftime('%Y%m%d')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
except: pass
