from openai import OpenAI
import yaml
import openai
import PyPDF2
import fitz
# Provide your API key as a parameter when initializing the client

with open("config.yaml") as f:
   config_yaml = yaml.load(f, Loader=yaml.FullLoader)
openai.api_key = config_yaml['token']

completion = openai.chat.completions.create(
  model="gpt-3.5-turbo",
 max_tokens=2048,
conversation = [
    {"role": "system", "content": "You are a presentation assistant."},
    {"role": "user", "content": "Please explain the PDF presentation with keywords: [user-provided keywords]."},
    {"role": "assistant", "content": "..."},  # Assistant's responses
    # Add more user and assistant messages as needed
]
)

#print(completion.choices[0].message)
###

# Replace 'your_pdf_file.pdf' with the path to your PDF presentation file
pdf_file_path = 'CarsharingMitStreams.pdf'

# Open the PDF file
pdf_document = fitz.open(pdf_file_path)

# Initialize an empty string to store extracted text
extracted_text = ''

# Iterate through each page in the PDF
for page_num in range(len(pdf_document)):
    # Get the current page
    page = pdf_document[page_num]

    # Extract text from the page
    page_text = page.get_text()

    # Append the page text to the extracted_text variable
    extracted_text += page_text

# Print or use the extracted text as needed
print(extracted_text)
