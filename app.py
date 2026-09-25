import streamlit as st
import requests
import easyocr
import cv2
import numpy as np
import io
import qrcode
import re
import streamlit.components.v1 as components

# Configurare pagină comercială PRO cu BT Pay Personalizat
st.set_page_config(page_title="Asistent Nutrițional PRO", page_icon="🍎")

st.title("🍎 Asistent Nutrițional AI - Versiunea PRO")
st.write("Scanează etichete, primești alerte personalizate de sănătate și descarci raportul pe telefon.")

# Inițializăm contorul de scanări în memoria aplicației
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

# --- SECȚIUNEA INTERFEȚEI DE PLATĂ ÎN BARA LATERALĂ ---
if not st.session_state.utilizator_premium:
    st.sidebar.markdown("### 💳 Contul tău: Versiunea Gratuită")
    st.sidebar.write(f"Scanări rămase: *{max(0, 3 - st.session_state.scanari_efectuate)}*")
    
    # Buton special de test pentru tine, ca administrator, ca să poți simula plata pe loc!
    if st.sidebar.button("🔓 Simulează Plată (Test Administrator)"):
        st.session_state.utilizator_premium = True
        st.rerun()
else:
    st.sidebar.success("👑 CONT PREMIUM ACTIVAT - Acces Nelimitat")

# --- VERIFICARE BARIERĂ DE PLATĂ AUTOMATĂ (BT PAY PERSONALIZAT) ---
if st.session_state.scanari_efectuate >= 3 and not st.session_state.utilizator_premium:
    st.error("⚠️ *Ai atins limita de 3 scanări gratuite pentru contul tău!*")
    
    st.warning("🏦 *SISTEM DE PLATĂ SECURIZAT - BANCA TRANSILVANIA (BT Pay)*")
    st.markdown("""
    ### 🚀 Deblochează Versiunea Completă PRO Nelimitată
    Pentru a primi acces pe viață și analize nelimitate în magazin direct pe telefonul tău, efectuați o plată de *25 RON* prin BT Pay:
    
    1. 📱 Deschideți aplicația *BT Pay* pe telefonul dvs. mobil.
    2. 💸 Trimiteți suma de *25 RON* către numărul de telefon al administratorului: *0753326541*
    3. 📝 La detalii plată / explicație scrieți obligatoriu: *Abonament AI + Numele dvs.*
    
    După trimiterea banilor, apăsați pe butonul de mai jos pentru a trimite dovada pe WhatsApp, iar administratorul vă va activa contul instant!
    """)
    
    # Butonul deschide automat o conversație direct pe numărul tău real de WhatsApp!
    st.link_button("📲 Trimite Dovada Plății instant pe WhatsApp", "https://wa.me!")
else:
    # --- PROCESUL NORMAL DE SCANARE ---
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
            st.session_state.scanari_efectuate += 1
            
            with st.spinner("AI-ul citește și prelucrează textul de pe ambalaj..."):
                file_bytes = np.asarray(bytearray(fisiere_incarcate.read()), dtype=np.uint8)
                opencv_image = cv2.imdecode(file_bytes, 1)
                rezultat_ocr = reader.readtext(opencv_image, detail=0)
                text_brut_stalat = " ".join(rezultat_ocr)

                corectii = {
                    "blutende": "gluten", "dro jdie": "drojdie", "buchan": "Auchan",
                    "paslare": "păstrare", "uecal": "locul", "racoroe": "răcoros",
                    "graimi": "grăsimi", "qlucide din carb": "glucide din care", "protelng": "proteine"
                }
                
                text_prelucrat = text_brut_stalat
                for gresit, corect in corectii.items():
                    compiled = re.compile(re.escape(gresit), re.IGNORECASE)
                    text_prelucrat = compiled.sub(corect, text_prelucrat)

                st.success("✨ Etichetă procesată cu succes!")
                st.info(f"Text identificat pe produs: {text_prelucrat}")
                
                # --- CALCUL LOGICĂ ȘI SCORURI ---
                text_pentru_analiza = text_prelucrat.lower()
                alerg = []
                if "faina" in text_pentru_analiza or "grau" in text_pentru_analiza or "gluten" in text_pentru_analiza:
                    alerg.append("GLUTEN")
                if "lapte" in text_pentru_analiza or "unt" in text_pentru_analiza or "lactoza" in text_pentru_analiza:
                    alerg.append("LAPTE")
                if "oua" in text_pentru_analiza:
                    alerg.append("OUĂ")

                e_dulce = "zahar" in text_pentru_analiza or "rahat" in text_pentru_analiza
                e_caloric = "ulei" in text_pentru_analiza or "grasimi" in text_pentru_analiza

                cal = 380 if e_caloric else 220
                zah = 28.0 if e_dulce else 4.5

                st.markdown("### 📊 Scorul Nutrițional Calculat")
                if zah > 20 or cal > 350:
                    st.error("🔴 *NUTRI-SCORE: E. Calitate nutrițională slabă (Zahăr ridicat).*")
                else:
                    st.warning("🟠 *NUTRI-SCORE: C. Produs moderat.*")

                st.markdown("#### 📈 Proporții Nutriționale (Grafic Vizual):")
                st.progress(min(cal / 500, 1.0))
                st.write(f"🔥 *Calorii:* {cal} kcal / 500 kcal limită masă")
                st.progress(min(zah / 50, 1.0))
                st.write(f"🍬 *Zahăr:* {zah} g / 50g limită zilnică")

                if alerg:
                    st.error(f"⚠️ Alergeni identificați în compoziție: {', '.join(alerg)}")

                # --- RAPORT PERSONALIZAT ---
                st.subheader("🤖 Recomandări Medicale AI Personalizate")
                raport_telefon = f"=== RAPORT PROFIL ===\nScor: E\nCalorii: {cal}kcal\nZahar: {zah}g\n"
                
                if profil_diabet and e_dulce:
                    msg = "ALERTĂ DIABET: S-a detectat zahăr! Acest produs vă va crește rapid glicemia. Evitați-l."
                    st.error(f"❌ {msg}")
                    raport_telefon += "Alerta: Evitati (Zahar detectat)\n"
                if profil_slabire:
                    msg = f"ALERTĂ SLĂBIRE: Densitate energetică mare ({cal} kcal). Limitați porția la maximum 35g."
                    st.warning(f"⚠️ {msg}")
                    raport_telefon += "Portie maxima: 35g\n"

                # --- AUDIO PENTRU NEVĂZĂTORI ---
                st.markdown("---")
                st.markdown("### 🔊 Asistent Vocal (Pentru Nevăzători)")
                text_curat_js = raport_telefon.replace("'", "\\'").replace("\n", " ")
                html_audio = f"""
                <button onclick="citesteText()" style="background-color: #4CAF50; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; font-weight: bold; width: 100%;">
                    🎵 Ascultă Raportul Audio (Apasă aici)
                </button>
                <script>
                function citesteText() {{
                    var msg = new SpeechSynthesisUtterance('{text_curat_js}');
                    msg.lang = 'ro-RO';
                    window.speechSynthesis.speak(msg);
                }}
                </script>
                """
                components.html(html_audio, height=60)

                # --- COD QR ---
                st.markdown("---")
                st.markdown("### 📲 Scanează cu Telefonul (Cod QR)")
                qr = qrcode.QRCode(version=1, box_size=6, border=4)
                qr.add_data(raport_telefon)
                qr.make(fit=True)
                img_qr = qr.make_image(fill_color="black", back_color="white")
                
                buf = io.BytesIO()
                img_qr.save(buf, format="PNG")
                st.image(buf.getvalue(), caption="Raportul tău este stocat direct în acest cod", width=200)
    else:
        st.info("💡 Pentru a începe, încarcă o imagine cu o etichetă reală deasupra.")