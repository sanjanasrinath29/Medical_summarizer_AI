import fitz  # PyMuPDF
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
from django.conf import settings


# ──────────────────────────────────────────────pip install langchain-text-splitters
# FUNCTION 1: Read text from uploaded PDF
# ──────────────────────────────────────────────
def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    full_text = ""

    for page_number, page in enumerate(doc):
        text = page.get_text()
        full_text += f"\n--- Page {page_number + 1} ---\n{text}"

    doc.close()

    if not full_text.strip():
        raise ValueError(
            "No text found in PDF. "
            "Make sure it is not a scanned image."
        )

    return full_text


# ──────────────────────────────────────────────
# FUNCTION 2: Store report in ChromaDB
# ──────────────────────────────────────────────
def build_report_vectorstore(text, report_id):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.create_documents([text])

    embeddings = HuggingFaceEmbeddings(
      model_name="all-MiniLM-L6-v2"
    )

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=f"report_{report_id}",
        persist_directory=f"./chroma_storage/{report_id}"
    )

    return vectorstore


# ──────────────────────────────────────────────
# FUNCTION 3: Generate summary using BOTH
#             report + knowledge base
# ──────────────────────────────────────────────
def generate_summary(text, report_id):
    embeddings = HuggingFaceEmbeddings(
       model_name="all-MiniLM-L6-v2"
    )

    # Load the report vectorstore we just built
    report_vs = Chroma(
        collection_name=f"report_{report_id}",
        embedding_function=embeddings,
        persist_directory=f"./chroma_storage/{report_id}"
    )

    # Load the medical knowledge base
    knowledge_vs = Chroma(
        collection_name="medical_knowledge",
        embedding_function=embeddings,
        persist_directory="./chroma_storage/knowledge_base"
    )

    # Get all test values from report
    report_docs = report_vs.similarity_search(
        "blood test values hemoglobin RBC WBC platelets "
        "glucose cholesterol thyroid kidney liver",
        k=10
    )

    # Get all reference ranges from knowledge base
    knowledge_docs = knowledge_vs.similarity_search(
        "normal range hemoglobin glucose cholesterol "
        "RBC WBC platelets thyroid kidney creatinine",
        k=20
    )

    report_context = "\n".join(
        [doc.page_content for doc in report_docs]
    )
    knowledge_context = "\n".join(
        [doc.page_content for doc in knowledge_docs]
    )

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0  # No creativity — pure comparison
    )

    prompt = f"""
You are a medical report reading assistant.

YOUR ONLY JOB:
1. Read patient values from PATIENT REPORT section below
2. Read normal ranges from MEDICAL REFERENCE section below
3. Compare each value against the reference range
4. Report if each value is Normal, Low, or High
5. Use one simple sentence to explain what it means

STRICT RULES:
- Use ONLY the two sections provided below
- Do NOT use your own training knowledge or memory
- Do NOT guess any values or ranges
- If a test is in the report but NOT in the reference, write:
  "Reference range not available in our database"
- Keep language very simple — patient should understand
- Be consistent — if a test is marked HIGH or LOW in results, it must appear in Needs Attention list
- UNIT AWARENESS: Some tests use two unit systems.
  WBC/TLC: if value is 4-11 it is 10^9/L (normal 4.0-11.0)
           if value is 4000-11000 it is cells/mcL (normal 4500-11000)
  PLATELETS: if value is 150-400 it is 10^9/L (normal 150-400)
             if value is 150000-400000 it is cells/mcL (normal 150000-400000)
  RBC: whether unit is 10^12/L or million cells/mcL
       the normal range numbers are the same (4.5-5.9 male, 4.1-5.1 female)
  Always check the unit in the report before comparing against reference range.
- Never put the same test in both Normal and Needs Attention lists
- HDL Cholesterol and HDL/LDL Ratio are two different tests — treat them separately

OUTPUT FORMAT (follow exactly, do not change):

📋 REPORT SUMMARY
Patient: [name if found, else write Not mentioned]
Date: [date if found, else write Not mentioned]
Report Type: [CBC / Lipid Profile / Thyroid etc]

📊 QUICK OVERVIEW

✅ Normal Tests:
[comma separated list of all normal test names only]

🔴 Needs Attention:

⚕️ Please Discuss With Your Doctor:
[For each abnormal test write exactly in this format:]

[Test Name]: [LOW or HIGH]
  Your Value: [value] [unit]
  Meaning: [one line from reference section only]

💊 MEDICATIONS IN REPORT:
[List any medicines found, or write None mentioned]

📅 FOLLOW UP:
[Any instructions from report, or write Not mentioned]

⚕️ NOTE: This is an AI generated summary for information
only. Always consult your doctor for medical advice.

─────────────────────────────────────────────
PATIENT REPORT:
{report_context}

─────────────────────────────────────────────
MEDICAL REFERENCE (use ONLY this for ranges):
{knowledge_context}
─────────────────────────────────────────────

Important: Compare ONLY. Do not add anything from memory.
"""

    response = llm.invoke(prompt)
    return response.content


# ──────────────────────────────────────────────
# FUNCTION 4: Answer user questions
#             using report + knowledge base
# ──────────────────────────────────────────────
def answer_question(report_id, question):
    embeddings = HuggingFaceEmbeddings(
       model_name="all-MiniLM-L6-v2"
    )

    report_vs = Chroma(
        collection_name=f"report_{report_id}",
        embedding_function=embeddings,
        persist_directory=f"./chroma_storage/{report_id}"
    )

    knowledge_vs = Chroma(
        collection_name="medical_knowledge",
        embedding_function=embeddings,
        persist_directory="./chroma_storage/knowledge_base"
    )

    # Find relevant parts from report
    report_docs = report_vs.similarity_search(question, k=4)

    # Find relevant parts from knowledge base
    # ChromaDB automatically finds nutrition data
    # when question is about food
    knowledge_docs = knowledge_vs.similarity_search(question, k=6)

    report_context = "\n".join(
        [doc.page_content for doc in report_docs]
    )
    knowledge_context = "\n".join(
        [doc.page_content for doc in knowledge_docs]
    )

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0
    )

    prompt = f"""
You are a medical report assistant.
Answer the user question using ONLY the two sources below.

STRICT RULES:
- Use ONLY PATIENT REPORT and KNOWLEDGE BASE sections below
- Do NOT use your own training knowledge or memory
- If answer is not in either source write exactly:
  "I don't have enough information in my knowledge base
   to answer this. Please consult your doctor."
- Keep language simple and friendly
- Never be alarming or scary

USER QUESTION: {question}

─────────────────────────────────────────────
PATIENT REPORT:
{report_context}

─────────────────────────────────────────────
KNOWLEDGE BASE:
{knowledge_context}
─────────────────────────────────────────────

Answer using only the sources above:
"""

    response = llm.invoke(prompt)
    return response.content
