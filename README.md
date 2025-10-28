# 🧓 Aplicație de Îngrijire a Vârstnicilor

Aceasta este o aplicație mobilă dezvoltată cu **KivyMD** și **Python**, destinată gestionării informațiilor medicale pentru persoane vârstnice. Aplicația oferă un sistem de autentificare pe roluri (admin, doctor, îngrijitor, vârstnic) și facilitează comunicarea și organizarea între aceste categorii de utilizatori.

---

## 🛠️ Funcționalități principale

- **Autentificare și înregistrare pe roluri**: doctori, îngrijitori, vârstnici și admini.
- **Aprobarea cererilor de cont pentru doctori** (efectuată de către admin).
- **Creare de conturi de îngrijitor și vârstnic** de către doctor.
- **Adăugarea și vizualizarea medicației** pentru vârstnici.
- **Încărcare de documente medicale** (ex: fișe PDF, rețete, analize).
- **Programarea controalelor medicale** și exerciții recomandate.
- **Vizualizarea fișierelor și informațiilor de sănătate** pentru fiecare rol.
- **Suport pentru descărcarea fișierelor pe Android și Windows.**

---

## 📱 Platformă

- Testată și compatibilă cu **Android** (via Buildozer) și **Windows** (versiune desktop Python).
- Gestionarea permisiunilor de fișiere pentru Android este implementată.

---

## ▶️ Cum rulezi aplicația

### 🔹 Pe Windows

1. Instalează dependențele:

   ```bash
   pip install -r requirements.txt
   ```

2. Rulează aplicația:
   ```bash
   python main.py
   ```

### 🔹 Pe Android

1. Asigură-te că ai `buildozer` configurat (pe Linux).
2. Compilează aplicația:
   ```bash
   buildozer -v android debug
   buildozer android deploy run
   ```

---

## 💾 Bază de date

- Aplicația utilizează o bază de date **MySQL**.
- Datele sunt stocate în tabele separate pentru utilizatori, medicații, documente, exerciții și controale medicale.
- Setările pentru conexiune se găsesc în fișierul `database.py`, în dicționarul `DB_CONFIG`.

---

## 🎨 Iconițe

Toate iconițele folosite în aplicație sunt obținute de pe [Icons8](https://icons8.com/icons).  
Mulțumim pentru resursele gratuite oferite!

---

## 🔒 Securitate

- Parolele sunt criptate cu **bcrypt** înainte de a fi stocate în baza de date.
- Verificarea autentificării se face în mod securizat.
- Accesul la funcționalități este controlat pe baza rolului utilizatorului.
