from flask import Flask, render_template, request, redirect, url_for, Response
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import yaml
import openai
import fitz
from io import BytesIO
import traceback

app = Flask(__name__)

# Load API key from config.yaml
with open("config.yaml") as f:
    config_yaml = yaml.load(f, Loader=yaml.FullLoader)
openai.api_key = config_yaml['token']

# Helper function to save the uploaded PDF file
def save_pdf_file(pdf_file):
    if pdf_file:
        pdf_file_path = f"uploads/{pdf_file.filename}"
        pdf_file.save(pdf_file_path)
        return pdf_file_path
    return None

# Helper function to extract text from the PDF
def extract_text_from_pdf(pdf_file_path):
    extracted_text = ''
    try:
        pdf_document = fitz.open(pdf_file_path)
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            page_text = page.get_text()
            extracted_text += page_text
    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
    return extracted_text

# Helper function to interact with ChatGPT and generate presentation content
def generate_presentation_content(extracted_text, keywords, question):
    additional_instructions = request.form.get('additional_instructions', '')
    try:
        # Formulate the prompt for GPT
        prompt = (
            f"Ich benötige einen Fließtext, der die wesentlichen Inhalte einer detaillierten und gründlichen Präsentation zusammenfasst. "
            f"Der Fließtext soll die Hauptpunkte der Präsentation mit klaren Formulierungen zusammenfassen und einen Schwerpunkt auf die folgenden Schlüsselwörter legen: {keywords}. "
            f"Zusätzliche Anweisungen: {additional_instructions} "
            f"Der Text der Präsentation lautet: {extracted_text}\n\n"
            "Bitte beginnen Sie mit einer kurzen Einführung, die einen Überblick über die Hauptthemen der Präsentation bietet, gefolgt von einer kompakten Zusammenfassung der einzelnen Abschnitte. "
            "Schließen Sie den Fließtext mit den wichtigsten Erkenntnissen und Schlussfolgerungen ab."
        )

        if question:
            prompt += f" {question}"

        # Log the inputs
        #print(f"Prompt: {prompt}")

        # Send API requests to GPT-4 using the chat completions endpoint
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )

        # Log the response
        if 'choices' not in completion or not completion['choices']:
            print("No choices in the completion response.")
            return None

        presentation_content = completion['choices'][0]['message'
        ]['content'].strip()
        if not presentation_content:
            print("Received empty content from GPT.")
            return None

        print(f"Generated Content: {presentation_content[:500]}...")  # Log the first 500 characters of the content
        return presentation_content

    except Exception as e:
        print(f"Error generating presentation content: {str(e)}")
        traceback.print_exc()
        return None


# Helper function to generate a PDF document
def generate_pdf(presentation_content):
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        styles = getSampleStyleSheet()

        Story = []
        style = styles["Normal"]
        for line in presentation_content.split('\n'):
            p = Paragraph(line, style)
            Story.append(p)

        doc.build(Story)
        buffer.seek(0)
        return buffer
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        return None

# Route for the presentation generation page
@app.route('/')
def home():
    return render_template('generate_presentation.html')

# Route to handle PDF upload and presentation generation
@app.route('/generate_presentation', methods=['POST'])
def generate_presentation():
    pdf_file_path = None
    try:
        # Handle PDF file upload
        pdf_file = request.files['pdf_file']
        pdf_file_path = save_pdf_file(pdf_file)
    except Exception as e:
        print(f"Error handling PDF file upload: {str(e)}")
        traceback.print_exc()
        return "Error handling PDF file upload."

    try:
        # Extract text from the uploaded PDF
        extracted_text = extract_text_from_pdf(pdf_file_path)
    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
        traceback.print_exc()
        return "Error extracting text from PDF."

    try:
        # Extract user inputs (keywords and question)
        keywords = request.form.get('keywords')
        question = request.form.get('question')
    except Exception as e:
        print(f"Error extracting form data: {str(e)}")
        traceback.print_exc()
        return "Error extracting form data."

    try:
        # Generate presentation content with ChatGPT
        presentation_content = generate_presentation_content(extracted_text, keywords, question)
        if not presentation_content:
            raise ValueError("No content generated by ChatGPT.")
    except Exception as e:
        print(f"Error generating presentation content: {str(e)}")
        traceback.print_exc()
        return "Error generating presentation content."

    try:
        # Generate a PDF document with the presentation content
        pdf_buffer = generate_pdf(presentation_content)
        if not pdf_buffer:
            raise ValueError("PDF buffer is empty.")
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        traceback.print_exc()
        return "Error generating PDF."

    try:
        # Send the PDF document as a response for download
        return Response(pdf_buffer, mimetype='application/pdf',
                        headers={'Content-Disposition': 'attachment; filename=fließText.pdf'})
    except Exception as e:
        print(f"Error sending PDF response: {str(e)}")
        traceback.print_exc()
        return "Error sending PDF response."



if __name__ == '__main__':
        app.run(debug=True)
