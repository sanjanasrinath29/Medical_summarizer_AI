# 🏥 Medical Report Summarizer — AI Powered RAG Application

An intelligent medical report analysis system built with Django and 
RAG (Retrieval Augmented Generation) that reads your blood test report, 
compares every value against standard medical reference ranges, and 
explains results in simple language.

---

## 💡 What It Does

- Upload any medical PDF report (blood test, lipid profile, thyroid, etc.)
- Automatically extracts all test values from the report
- Compares each value against a curated medical knowledge base
- Tells you which values are Normal, Low, or High in simple language
- Chat with your report — ask questions like:
  - *"What does my low Hb mean?"*
  - *"What foods help improve my hemoglobin?"*
  - *"Which values need immediate attention?"*
- All answers come strictly from the knowledge base — no hallucination

---

## 🧠 How RAG Works in This Project
```
User uploads PDF
      ↓
PyMuPDF extracts text
      ↓
Text split into chunks → stored in ChromaDB (vector database)
      ↓
User asks question
      ↓
ChromaDB finds relevant chunks from:
  1. Patient's report
  2. Medical knowledge base (reference ranges + nutrition advice)
      ↓
Both sent to Gemini with strict prompt
      ↓
Gemini compares and responds using ONLY provided context
      ↓
No hallucination — fully grounded response
```

The LLM (Gemini) is strictly prompted to answer **only** from the 
two retrieved sources. It cannot use its own training knowledge. 
This ensures every response is traceable and verifiable.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django, Django REST Framework |
| AI / LLM | Google Gemini API (gemini-2.5-flash-lite) |
| RAG Framework | LangChain |
| Vector Database | ChromaDB (local) |
| Embeddings | HuggingFace Sentence Transformers (all-MiniLM-L6-v2) |
| PDF Parsing | PyMuPDF (fitz) |
| Frontend | HTML, CSS, JavaScript |
| Database | SQLite |

---

## 📁 Project Structure
```
medical_summarizer/
│
├── config/                     # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── reports/                    # Main Django app
│   ├── templates/
│   │   └── index.html          # Frontend UI
│   ├── models.py               # MedicalReport, ChatMessage models
│   ├── views.py                # API endpoints
│   ├── urls.py                 # URL routing
│   └── rag_engine.py           # Core RAG pipeline
│
├── medical_knowledge/          # Knowledge base text files
│   ├── blood_tests.txt         # CBC reference ranges
│   ├── glucose_diabetes.txt    # Diabetes markers
│   ├── lipid_profile.txt       # Cholesterol ranges
│   ├── thyroid.txt             # Thyroid tests
│   ├── kidney_liver.txt        # Kidney and liver tests
│   ├── vitamins_minerals.txt   # Vitamin and mineral ranges
│   ├── liver_function.txt      # Complete LFT ranges
│   └── nutrition_advice.txt    # Food recommendations per condition
│
├── build_knowledge_base.py     # One-time script to build ChromaDB
├── manage.py
├── requirements.txt
└── .env                        # API keys (not pushed to GitHub)
```

---

## ⚙️ Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/medical-report-summarizer.git
cd medical-report-summarizer
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Get Free Gemini API Key

1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Sign in with Google account
3. Click **Get API Key** → **Create API Key**
4. Copy the key

### 5. Create .env File

Create a `.env` file in the project root:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

### 6. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Build Knowledge Base (Run Only Once)
```bash
python build_knowledge_base.py
```

This downloads the HuggingFace embedding model (~90MB) 
and builds the ChromaDB knowledge base from the 
medical_knowledge/ text files.

Only needs to be run once. Run again only if you 
update the knowledge base files.

### 8. Start the Server
```bash
python manage.py runserver
```

Open browser → `http://127.0.0.1:8000`

---

## 🚀 How to Use

**Step 1** — Upload your medical PDF report

**Step 2** — Wait 20-30 seconds while the app:
- Extracts text from PDF
- Builds vector store for your report
- Compares values against knowledge base
- Generates structured summary

**Step 3** — Read your summary:
```
📋 REPORT SUMMARY
Patient: Your Name
Report Type: Complete Blood Count

📊 QUICK OVERVIEW
✅ Normal: WBC, Platelets, HbA1c...
🔴 Needs Attention:

⚕️ Please Discuss With Your Doctor:
Haemoglobin (Hb): LOW
  Your Value: 8.3 g/dL
  Meaning: Hemoglobin is low. May indicate anemia.
```

**Step 4** — Ask questions in the chat:
- *"What foods help improve my Hb?"*
- *"Is my cholesterol dangerous?"*
- *"What does low MCV mean?"*

---

## 📚 Knowledge Base Coverage

The medical knowledge base covers:

| Category | Tests Covered |
|---|---|
| Complete Blood Count | Hb, RBC, WBC, Platelets, PCV, MCV, MCH, MCHC |
| Diabetes | Fasting Glucose, HbA1c, Post Meal Glucose |
| Lipid Profile | Total Cholesterol, LDL, HDL, Triglycerides, VLDL |
| Thyroid | TSH, T3, T4, Free T3, Free T4 |
| Kidney Function | Creatinine, Urea, Uric Acid, eGFR |
| Liver Function | SGPT, SGOT, Bilirubin, ALP, GGT, Albumin |
| Vitamins & Minerals | Vitamin D, B12, Folate, Iron, Ferritin, Calcium |
| Electrolytes | Sodium, Potassium, Magnesium |
| Nutrition Advice | Food recommendations for each condition |

---

## 🔒 Privacy

- Patient report text is stored locally in ChromaDB
- HuggingFace embeddings run **locally on your machine**
- Medical data is **never sent to external embedding APIs**
- Only the final comparison prompt is sent to Gemini API

---

## ⚠️ Disclaimer

This application is for **informational purposes only.**
It is not a substitute for professional medical advice,
diagnosis, or treatment. Always consult a qualified
doctor for medical concerns.

---

## 🙋 Common Issues

**`No text found in PDF`**
Your PDF might be a scanned image. 
Try with a text-based PDF report.

**`Knowledge base not found`**
Run `python build_knowledge_base.py` first.

**`Gemini API quota exceeded`**
Free tier has daily limits. 
Wait a few hours or create a new API key at aistudio.google.com

**`Port already in use`**
```bash
python manage.py runserver 8080
```
Then open `http://127.0.0.1:8080`

---

## 👩‍💻 Author

**Sanjana Srinath** & **Mithali S Channal**
- LinkedIn: https://www.linkedin.com/in/sanjana-srinath-s2901/  and https://www.linkedin.com/in/mithali-s-channal2002
- Email: sanjanasrinath1@gmail.com and mithalischannal143@gmail.com
