import logging
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from sentence_transformers import SentenceTransformer
from transformers import pipeline
import faiss
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
import os
import numpy as np

# Configuração do Flask
app = Flask(__name__)
CORS(app)  # Adicione esta linha para habilitar o CORS

# Configuração do Modelo de Embeddings
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
index_path = "faiss_index"

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
        raise ValueError("Nenhum documento fornecido para adicionar ao índice.")
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

# Configuração do pipeline de resumo
summary_pipeline = pipeline("summarization")

# Função para criar o resumo
def generate_summary(data):
    """Cria um resumo sintetizado a partir das informações fornecidas."""
    # Calcular os anos de experiência
    experience_years = sum(
        int(exp['end_year']) - int(exp['start_year']) for exp in data.get('experience', []) if exp.get('start_year') and exp.get('end_year')
    )
    # Combinar habilidades
    skills = data.get('skills', '')

    # Classificar a experiência
    classification = classify_experience(experience_years)

    # Criar o texto de entrada para o modelo de resumo
    input_text = f"Experiência: {experience_years} anos. Habilidades: {skills}."

    # Gerar o resumo usando o modelo de IA
    summary = summary_pipeline(input_text, max_length=50, min_length=25, do_sample=False)[0]['summary_text']

    return summary, classification

# Função para criar o PDF
    elements = []

    elements.append(Paragraph(f" {user_data.get('name', 'Nome não informado')}", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"<b>Email:</b> {user_data.get('contact', 'Contato não informado')}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("<b>Resumo:</b>", styles["Heading2"]))
    elements.append(Paragraph(summary, styles["Normal"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("<b>Classificação:</b>", styles["Heading2"]))
    elements.append(Paragraph(classification, styles["Normal"]))
    elements.append(Spacer(1, 12))

    doc.build(elements)
    return pdf_path

# Endpoint para processamento do currículo
@app.route("/process-cv", methods=["POST"])
def process_cv():
    try:
        # Dados do usuário
        user_data = request.json
        logging.info("Recebendo dados do usuário...")

        # Gerar resumo e classificação
        summary, classification = generate_summary(user_data)
        logging.info(f"Resumo gerado: {summary}")
        logging.info(f"Classificação gerada: {classification}")

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
