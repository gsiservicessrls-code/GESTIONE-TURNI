import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta

# Configurazione della pagina
st.set_page_config(page_title="Gestione Turni Personale", layout="wide")

# ==================== SISTEMA DI SICUREZZA (LOGIN) ====================
def verifica_password():
    """Ritorna True se l'utente è autenticato."""
    if "autenticato" not in st.session_state:
        st.session_state.autenticato = False

    if st.session_state.autenticato:
        return True

    st.title("🔒 Accesso Riservato - Gestione Turni")
    st.write("Inserisci le credenziali aziendali per accedere alla pianificazione online.")
    
    col1, _ = st.columns([2, 2])
    with col1:
        username = st.text_input("Nome Utente (Username)")
        password = st.text_input("Password", type="password")
        
        if st.button("Accedi"):
            # Credenziali di sicurezza personalizzabili
            if username == "amministrazione" and password == "Turniazienda2026!":
                st.session_state.autenticato = True
                st.rerun()
            else:
                st.error("❌ Username o Password errati. Riprova.")
    return False

# Esegui l'applicazione solo se l'utente ha effettuato l'accesso
if verifica_password():

    # ==================== CONFIGURAZIONE STRUTTURA DATI ====================
    dipendenti_ore = {
        "PERINO": 38, "GUARRAIA": 28, "GULLO": 30, "BENIGNO": 30,
        "NUCCIO": 0, "COCUZZA": 0, "GAITA": 0, "SERIO A.": 30,
        "FERRUGGIA": 24, "LION": 29, "DE JOMA": 0
    }

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

    lista_turni = list(turni_ore.keys())

    # ==================== INTERFACCIA UTENTE PRINCIPALE ====================
    st.title("📅 Pianificazione Professionale Turni Online")
    st.write("Le modifiche vengono mantenute in memoria. Scegli la settimana dal calendario.")

    # 1. MODIFICA: GESTIONE DELLE DATE (SELETTORE CALENDARIO)
    st.subheader("📆 Selezione Settimana di Riferimento")
    data_scelta = st.date_input("Seleziona il giorno di inizio (Lunedì):", datetime.now() - timedelta(days=datetime.now().weekday()))
    
    # Genera le intestazioni con le date esatte basate sulla scelta (es. Lunedì 16/03)
    giorni_colonne = []
    for i in range(7):
        giorno_corrente = data_scelta + timedelta(days=i)
        giorni_colonne.append(giorno_corrente.strftime("%A %d/%m"))

    # Chiave univoca per salvare in memoria la specifica settimana selezionata
    chiave_settimana = f"settimana_{data_scelta.strftime('%Y_%m_%d')}"

    # 2. MODIFICA: SALVATAGGIO AUTOMATICO E MEMORIA ONLINE
    if chiave_settimana not in st.session_state:
        # Crea una tabella vuota se la settimana non è mai stata aperta prima
        dati_iniziali = {g: ["RIPOSO" for _ in dipendenti_ore] for g in giorni_colonne}
        st.session_state[chiave_settimana] = pd.DataFrame(dati_iniziali, index=list(dipendenti_ore.keys()))

    df_lavoro = st.session_state[chiave_settimana].copy()

    # Sincronizzazione colonne nel caso cambino le date sul calendario
    if list(df_lavoro.columns) != giorni_colonne:
        dati_iniziali = {g: ["RIPOSO" for _ in dipendenti_ore] for g in giorni_colonne}
        df_lavoro = pd.DataFrame(dati_iniziali, index=list(dipendenti_ore.keys()))

    # Griglia interattiva di inserimento turni
    st.subheader("✍️ Compilazione della Griglia")
    for dipendente in df_lavoro.index:
        col_nome, *cols_giorni = st.columns([1.5, 1, 1, 1, 1, 1, 1, 1])
        col_nome.write(f"**{dipendente}**")
        for i, giorno in enumerate(giorni_colonne):
            valore_attuale = df_lavoro.at[dipendente, giorno]
            if valore_attuale not in lista_turni:
                valore_attuale = "RIPOSO"
            scelta = cols_giorni[i].selectbox(
                f"{giorno}-{dipendente}", lista_turni, index=lista_turni.index(valore_attuale), label_visibility="collapsed"
            )
            df_lavoro.at[dipendente, giorno] = scelta

    # Salva le selezioni dell'utente in tempo reale nella memoria persistente dell'app
    st.session_state[chiave_settimana] = df_lavoro

    # ==================== CALCOLO FORMULE ORIGINALI ====================
    ore_lavorate_totali = []
    differenze_totali = []

    for dipendente in df_lavoro.index:
        ore_contrattuali = dipendenti_ore[dipendente]
        somma_ore_lavorate = sum(turni_ore[df_lavoro.at[dipendente, giorno]] for giorno in giorni_colonne)
        differenza = somma_ore_lavorate - ore_contrattuali
        ore_lavorate_totali.append(somma_ore_lavorate)
        differenze_totali.append(differenza)

    # Assemblaggio del report finale per la visualizzazione e l'esportazione
    df_report = df_lavoro.copy()
    df_report.insert(0, "ORE CONTR.", [dipendenti_ore[d] for d in df_report.index])
    df_report["ORE LAV."] = ore_lavorate_totali
    df_report["DIFF."] = differenze_totali

    # RIGA COMPLESSIVA DEI TOTALI AZIENDALI (ORE DIPENTI)
    riga_totale = pd.Series(index=df_report.columns, dtype=object)
    riga_totale["ORE CONTR."] = sum(dipendenti_ore.values())
    riga_totale["ORE LAV."] = sum(ore_lavorate_totali)
    riga_totale["DIFF."] = sum(differenze_totali)
    for giorno in giorni_colonne:
        riga_totale[giorno] = ""

    df_report.loc["ORE DIPENTI"] = riga_totale

    st.subheader("📊 Calcoli Statistici e Totali del Personale")
    st.dataframe(df_report, use_container_width=True)

    # ==================== STRUMENTI DI ESPORTAZIONE EXCEL ====================
    st.subheader("💾 Scarica il Documento Ufficiale")

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_report.to_excel(writer, sheet_name="Turni Settimanali")
        writer.close()
    dati_excel = output.getvalue()

    st.download_button(
        label="🟢 Scarica i turni inseriti in Excel (.xlsx)",
        data=dati_excel,
        file_name=f"Pianificazione_Turni_{data_scelta.strftime('%Y_%m_%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
