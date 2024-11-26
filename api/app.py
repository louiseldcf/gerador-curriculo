from flask import Flask, request, jsonify, send_file
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

app = Flask(__name__)

# Configurando o modelo Hugging Face
model_name = "distilgpt2"  # Substitua por outro modelo, se necessário
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)
text_generator = pipeline("text-generation", model=model, tokenizer=tokenizer)

@app.route("/generate-cv", methods=["POST"])
def generate_cv():
    try:
        user_data = request.json
        
        prompt = f"""
        Você é um especialista em criação de currículos. Use as informações abaixo para criar um currículo claro e impressionante.

        Informações do Usuário:
        {user_data}

        Estrutura esperada:
        Nome:
        Contato:
        Resumo Profissional:
        Experiências Profissionais:
        - [Cargo] em [Empresa], [Ano-Início] - [Ano-Fim]: [Descrição]
        Educação:
        - [Grau] em [Curso] pela [Instituição], [Ano]
        Habilidades:
        - [Habilidade 1]
        - [Habilidade 2]
        - ...
        """
        
        # Gerar texto usando Hugging Face
        result = text_generator(prompt, max_new_tokens=500, num_return_sequences=1)
        structured_output = result[0]['generated_text']

        # Gerar PDF
        pdf_path = create_pdf(structured_output)

        # Retornar o PDF gerado
        return send_file(pdf_path, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def create_pdf(data):
    pdf_path = "curriculo_gerado.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    
    # Adicionar texto ao PDF
    c.setFont("Helvetica", 12)
    y = height - 50

    for line in data.split('\n'):
        if y < 50:  # Nova página se necessário
            c.showPage()
            c.setFont("Helvetica", 12)
            y = height - 50
        c.drawString(50, y, line)
        y -= 20

    c.save()
    return pdf_path


if __name__ == "__main__":
    app.run(debug=True)
