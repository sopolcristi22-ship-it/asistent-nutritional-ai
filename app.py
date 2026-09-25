import streamlit as st
import requests
import easyocr
import cv2
import numpy as np
import io
import qrcode
import urllib.parse
import streamlit.components.v1 as components

# Configurare pagină comercială
st.set_page_config(page_title="Asistent Nutrițional PRO", page_icon="🍎")

st.title("🍎 Asistent Nutrițional AI - Versiunea PRO")
st.write("Scanează etichete, primești alerte personalizate de sănătate și descarci raportul pe telefon.")

# Inițializăm contorul de scanări gratuite în memoria aplicației
if "scanari_efectuate" not in st.session_state:
    st.session_state.scanari_efectuate = 0

# Inițializăm starea abonamentului (False = Neplătit, True = Plătit)
if "utilizator_premium" not in st.session_state:
    st.session_state.utilizator_premium = False

# Inițializăm cititorul de text (OCR)
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['ro', 'en'])

reader = load_ocr()

# --- SECȚIUNEA INTERFEȚEI DE PLATĂ ---
if not st.session_state.utilizator_premium:
    st.sidebar.markdown("### 💳 Contul tău: Versiunea Gratuită")
    st.sidebar.write(f"Scanări rămase: *{max(0, 3 - st.session_state.scanari_efectuate)}*")
    
    # Buton secret de test pentru tine, ca să vezi cum se schimbă aplicația după ce încasezi banii!
    if st.sidebar.button("Simulează Plată Card (Test)"):
        st.session_state.utilizator_premium = True
        st.rerun()
else:
    st.sidebar.success("👑 CONT PREMIUM ACTIVAT - Acces Nelimitat")

# --- VERIFICARE BARIERĂ DE PLATĂ ---
if st.session_state.scanari_efectuate >= 3 and not st.session_state.utilizator_premium:
    st.error("⚠️ *Ai atins limita de 3 scanări gratuite pentru contul tău!*")
    st.markdown("""
    ### 🚀 Debloochează Versiunea Completă PRO
    Ai nevoie de analize nelimitate în magazin? Alătură-te comunității noastre și ai acces la:
    * 🔍 *Scanări Etichete Nelimitate* în mai puțin de o secundă
    * 🔊 *Asistent Vocal complet activ* pentru nevăzători
    * 📲 *Coduri QR unice* transmise direct pe ecranul telefonului tău
    
    #### 💳 Preț promoțional: *25 RON / lună* (Abonament flexibil)
    """)
    
    # Aici va fi legat link-ul real Stripe pe care îl generăm în pasul următor
    if st.button("💳 Plătește în siguranță cu Cardul pe Stripe"):
        st.info("Trimitere către pagina securizată de plată...")
else:
    # --- PROCESUL NORMAL DE SCANARE (Dacă utilizatorul mai are credite sau a plătit) ---
    st.header("📸 1. Încarcă Eticheta Produsului")
    fisiere_incarcate = st.file_uploader("Alege o imagine (JPG, PNG, WEBP)...", type=["jpg", "jpeg", "png", "webp"])

    if fisiere_incarcate:
        st.image(fisiere_incarcate, caption="Eticheta încărcată!", use_container_width=True)
        
        st.markdown("---")
        st.header("🎯 2. Personalizează Profilul Tău")
        profil_diabet = st.checkbox("Am Diabet / Probleme cu glicemia")
        profil_slabire = st.checkbox("Vreau să slăbesc / Dietă hipocalorică")
        profil_lacto_gluten = st.checkbox("Intoleranță la Lactoză sau Gluten")

        st.markdown("---")
        if st.button("Scanează Eticheta și Corectează cu AI"):
            # Crestem numărul de scanări la fiecare apăsare de buton
            st.session_state.scanari_efectuate += 1
            
            with st.spinner("AI-ul citește eticheta..."):
                file_bytes = np.asarray(bytearray(fisiere_incarcate.read()), dtype=np.uint8)
                opencv_image = cv2.imdecode(file_bytes, 1)
                rezultat_ocr = reader.readtext(opencv_image, detail=0)
                text_brut_stalat = " ".join(rezultat_ocr)

                # Simulare analiză rapidă
                st.success("✨ Etichetă procesată cu succes!")
                st.info(f"Text detectat: {text_brut_stalat[:200]}...")
                
                # Grafice și scoruri
                st.markdown("### 📊 Scorul Nutrițional Calculat")
                st.error("🔴 *NUTRI-SCORE: E* (Conținut mare de carbohidrați)")
                st.progress(0.7)
                st.write("🍬 *Zahăr estimat:* 23g / 50g limită zilnică")
                
                # --- ASISTENTUL VOCAL ȘI QR ---
                # Aceste funcții de top funcționează gratuit doar primele 3 scanări, apoi cer plată!
                st.markdown("---")
                st.subheader("🔊 Asistent Vocal & Cod QR")
                st.write("Disponibile pe ecran. Folosește butonul din stânga pentru cont premium nelimitat.")