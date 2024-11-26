import logging
import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from transformers import RagTokenizer, RagSequenceForGeneration
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
import torch

# Configuração do Flask
app = Flask(__name__)
CORS(app)

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logging.info("Inicializando o modelo RAG...")

# Configuração do Tokenizer e Modelo RAG
tokenizer = RagTokenizer.from_pretrained("facebook/rag-sequence-nq")
rag_model = RagSequenceForGeneration.from_pretrained("facebook/rag-sequence-nq")

def generate_summary_with_rag(user_data):
    """Gera um resumo baseado nos dados do usuário."""
    # Criar um contexto simples a partir dos dados do usuário
    experiences = [
        f"{exp['position']} na {exp['company']} de {exp['start_year']} a {exp['end_year']}."
        for exp in user_data.get("experience", [])
    ]
    skills = user_data.get("skills", "Habilidades não informadas")
    context = (
        f"Nome: {user_data.get('name', 'Nome não informado')}. "
        f"Contato: {user_data.get('contact', 'Contato não informado')}. "
        f"Experiências: {', '.join(experiences)}. "
        f"Habilidades: {skills}."
    )

    # Pergunta simples para gerar o resumo
    question = "Baseando-se nos dados fornecidos, crie um resumo profissional claro e conciso."

    # Tokenizar a pergunta e o contexto
    question_inputs = tokenizer(question, return_tensors="pt", padding=True, truncation=True)
    context_inputs = tokenizer(context, return_tensors="pt", padding=True, truncation=True)

    # Ajustar inputs para o modelo
    inputs = {
        "input_ids": question_inputs["input_ids"],
        "attention_mask": question_inputs["attention_mask"],
        "context_input_ids": context_inputs["input_ids"],
        "context_attention_mask": context_inputs["attention_mask"],
    }

    # Geração de texto usando o modelo RAG
    outputs = rag_model.generate(
        input_ids=inputs["input_ids"],
        attention_mask=inputs["attention_mask"],
        context_input_ids=inputs["context_input_ids"],
        context_attention_mask=inputs["context_attention_mask"],
        max_new_tokens=50
    )
    summary = tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
    return summary

def create_pdf(user_data, summary, classification):
    """Cria um PDF com os dados do usuário e o resumo gerado."""
    pdf_path = "curriculo_gerado.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"<b>Nome:</b> {user_data.get('name', 'Nome não informado')}", styles["Title"]))
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

@app.route("/process-cv", methods=["POST"])
def process_cv():
    try:
        # Dados do usuário
        user_data = request.json
        logging.info("Recebendo dados do usuário...")

        # Gerar resumo com RAG
        summary = generate_summary_with_rag(user_data)
        logging.info(f"Resumo gerado: {summary}")

        # Calcular classificação baseada nos anos de experiência
        experience_years = sum(
            int(exp["end_year"]) - int(exp["start_year"])
            for exp in user_data.get("experience", [])
            if exp.get("start_year") and exp.get("end_year")
        )
        classification = (
            "Júnior" if experience_years < 2 else "Pleno" if experience_years < 5 else "Sênior"
        )
        logging.info(f"Classificação gerada: {classification}")

        # Gerar PDF
        pdf_path = create_pdf(user_data, summary, classification)
        return send_file(pdf_path, as_attachment=True)

    except Exception as e:
        logging.exception("Erro ao processar currículo")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    logging.info("Servidor iniciado...")
    app.run(debug=True)
