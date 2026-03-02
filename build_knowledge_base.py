import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


def build():
    print("\n Building medical knowledge base...")
    print("─" * 40)

    folder = "./medical_knowledge/"
    all_text = ""

    for filename in os.listdir(folder):
        if filename.endswith(".txt"):
            filepath = os.path.join(folder, filename)
            with open(filepath, "r") as f:
                content = f.read()
                all_text += content + "\n\n"
            print(f"  ✅ Loaded: {filename}")

    print(f"\n Splitting into chunks...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50
    )
    chunks = splitter.create_documents([all_text])
    print(f"  Total chunks created: {len(chunks)}")

    print("\n Creating embeddings and saving to ChromaDB...")
    
    # Runs locally — no API needed
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name="medical_knowledge",
        persist_directory="./chroma_storage/knowledge_base"
    )

    print("\n✅ Knowledge base built successfully!")
    print("─" * 40)
    print("Run the server now: python manage.py runserver\n")


if __name__ == "__main__":
    build()