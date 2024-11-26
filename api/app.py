import logging
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from sentence_transformers import SentenceTransformer
from transformers import pipeline, RagTokenizer, RagRetriever, RagSequenceForGeneration
import faiss
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
import os
import numpy as np

# Configuração do Flask
app = Flask(__name__)
CORS(app)  # Ativar CORS para permitir comunicação com o frontend

# Configuração do Modelo de Resumo
summary_pipeline = pipeline("summarization", model="t5-base")

# Configuração do Modelo de Embeddings
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
index_path = "faiss_index"

# Configuração do Modelo RAG
tokenizer = RagTokenizer.from_pretrained("facebook/rag-sequence-nq")
retriever = RagRetriever.from_pretrained("facebook/rag-sequence-nq", index_name="exact", use_dummy_dataset=True)
rag_model = RagSequenceForGeneration.from_pretrained("facebook/rag-sequence-nq", retriever=retriever)

# Função para carregar ou criar o índice FAISS


def load_faiss_index():
    if os.path.exists(index_path):
        logging.info("Carregando índice FAISS existente...")
        index = faiss.read_index(index_path)
    else:
        logging.info("Criando novo índice FAISS...")
        dimension = embedding_model.get_sentence_embedding_dimension()
        index = faiss.IndexFlatL2(dimension)
    return index


# Carregar o índice FAISS
faiss_index = load_faiss_index()

# Função para adicionar documentos ao índice FAISS


def add_to_index(documents):
    if not documents:
        raise ValueError(
            "Nenhum documento fornecido para adicionar ao índice.")
    embeddings = [embedding_model.encode(doc) for doc in documents]
    faiss_index.add(np.array(embeddings))
    faiss.write_index(faiss_index, index_path)
    logging.info(f"{len(documents)} documentos adicionados ao índice FAISS.")


# Adicionar documentos iniciais ao índice FAISS
if faiss_index.ntotal == 0:
    logging.info("Índice FAISS está vazio. Adicionando documentos iniciais...")
    initial_documents = [
        "Experiência em Python e desenvolvimento web usando Django e Flask.",
        "Habilidades em engenharia de software, com foco em arquitetura de sistemas.",
        "Experiência em análise de dados e visualização usando Python e ferramentas como Pandas e Matplotlib.",
        "Habilidades em liderança de equipe, comunicação efetiva e gestão ágil de projetos.",
        "Experiência com bancos de dados relacionais e NoSQL, como PostgreSQL e MongoDB.",
        "Habilidades em DevOps e ferramentas como Docker, Kubernetes e Jenkins.",
    ]
    add_to_index(initial_documents)

# Função para classificar a experiência


def classify_experience(years):
    if years < 2:
        return "Júnior"
    elif 2 <= years < 5:
        return "Pleno"
    else:
        return "Sênior"

# Função para formatar a experiência do usuário


def format_experience(experiences):
    return ', '.join([
        f"{exp['position']} na {exp['company']} de {exp['start_year']} a {exp['end_year']}"
        for exp in experiences
    ])

# Função para criar o resumo


def generate_summary(data):
    input_text = (
        f"Nome: {data.get('name', 'Nome não informado')}. "
        f"Contato: {data.get('contact', 'Contato não informado')}. "
        f"Experiência: {format_experience(data.get('experience', []))}. "
        f"Habilidades: {data.get('skills', '')}."
    )
    try:
        summary = summary_pipeline(
            input_text, max_length=100, min_length=50, do_sample=False)[0]['summary_text']
    except Exception as e:
        logging.error(f"Erro ao gerar resumo: {e}")
        summary = "Resumo não pôde ser gerado. Verifique os dados fornecidos."
    return summary

# Função para criar o PDF


def create_pdf(user_data, summary, classification):
    """Cria um PDF com os dados do usuário, o resumo e a classificação."""
    pdf_path = "curriculo_gerado.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(
        f"<b>Nome:</b> {user_data.get('name', 'Nome não informado')}", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(
        f"<b>Email:</b> {user_data.get('contact', 'Contato não informado')}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("<b>Resumo:</b>", styles["Heading2"]))
    elements.append(Paragraph(summary, styles["Normal"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("<b>Classificação:</b>", styles["Heading2"]))
    elements.append(Paragraph(classification, styles["Normal"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("<b>Experiências:</b>", styles["Heading2"]))
    for exp in user_data.get('experience', []):
        experience_text = f"{exp['position']} - {exp['company']}: {exp['start_year']} ~ {exp['end_year']}"
        elements.append(Paragraph(experience_text, styles["Normal"]))
        elements.append(Spacer(1, 12))

    doc.build(elements)
    return pdf_path

# Função para gerar respostas usando RAG


def generate_rag_response(question):
    inputs = tokenizer(question, return_tensors="pt")
    generated = rag_model.generate(**inputs)
    response = tokenizer.batch_decode(generated, skip_special_tokens=True)[0]
    return response

# Endpoint para processamento do currículo


@app.route("/process-cv", methods=["POST"])
def process_cv():
    try:

        # Gerar PDF
        pdf_path = create_pdf(user_data, summary, classification)
        return send_file(pdf_path, as_attachment=True)

    except Exception as e:
        logging.exception("Erro ao processar currículo")
        return jsonify({"error": str(e)}), 500


# Inicializar a aplicação
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True)
