import streamlit as st

def interfaccia_blocco_note():
    st.title("📝 Blocco Note e Appunti")
    st.subheader("Gestione comunicazioni e promemoria")

    # Inizializza lo stato della memoria per le note se non esiste
    if "note" not in st.session_state:
        st.session_state.note = []

    # --- SEZIONE 1: CREAZIONE NUOVA NOTA ---
    st.markdown("### ➕ Aggiungi una nuova nota")
    
    # Layout a due colonne per titolo e categoria
    col_titolo, col_cat = st.columns([2, 1])
    with col_titolo:
        titolo = st.text_input("Titolo della nota", placeholder="Es. Turno Domenica")
    with col_cat:
        categoria = st.selectbox("Categoria", ["Urgente", "Promemoria", "Generale"])
        
    contenuto = st.text_area("Contenuto della nota", placeholder="Scrivi qui i dettagli...")

    if st.button("Salva Nota", type="primary"):
        if titolo and contenuto:
            # Salva la nota come dizionario nella sessione
            nuova_nota = {
                "titolo": titolo,
                "categoria": categoria,
                "contenuto": contenuto
            }
            st.session_state.note.append(nuova_nota)
            st.success("Nota salvata con successo!")
            st.rerun()
        else:
            st.error("Per favore, inserisci sia il titolo che il contenuto.")

    st.divider()

    # --- SEZIONE 2: VISUALIZZAZIONE E GESTIONE NOTE ---
    st.markdown("### 📋 Le tue note")

    if not st.session_state.note:
        st.info("Non ci sono note salvate al momento.")
    else:
        # Mostra le note in una griglia o lista
        for id_nota, nota in enumerate(st.session_state.note):
            # Colore o etichetta in base alla categoria
            emoji = "🚨" if nota["categoria"] == "Urgente" else "📌" if nota["categoria"] == "Promemoria" else "✉️"
            
            # Crea un box espandibile per ogni nota
            with st.expander(f"{emoji} {nota['titolo']} ({nota['categoria']})"):
                st.write(nota["contenuto"])
                
                # Pulsante per eliminare la singola nota
                if st.button(f"Elimina nota", key=f"del_{id_nota}"):
                    st.session_state.note.pop(id_nota)
                    st.success("Nota eliminata.")
                    st.rerun()

# Per testare l'interfaccia da sola basta chiamare la funzione
if __name__ == "__main__":
    interfaccia_blocco_note()
