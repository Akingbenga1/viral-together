import ollama
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image, ImageDraw
from jinja2 import Template
from app.core.config import settings
from app.db.models.document_templates import DocumentTemplate

def generate_document(template: DocumentTemplate, params: dict, related_data: dict) -> str:
    try:
        # Try Ollama first
        prompt = template.prompt_text.format(**params, **related_data)
        response = ollama.generate(model='llama3', prompt=prompt)
        generated_text = response['response']
    except Exception as e:
        # Fallback to Jinja2
        jinja_template = Template(template.prompt_text)
        generated_text = jinja_template.render(**params, **related_data)
    
    # Create file based on format
    file_path = f"{settings.DOC_STORAGE_PATH}/doc_{template.id}.{template.file_format}"
    if template.file_format == 'pdf':
        c = canvas.Canvas(file_path, pagesize=letter)
        c.drawString(100, 750, "Generated Document")
        c.drawString(100, 700, generated_text)
        c.save()
    elif template.file_format == 'image' or template.file_format == 'png':
        img = Image.new('RGB', (800, 600), color=(73, 109, 137))
        d = ImageDraw.Draw(img)
        d.text((10,10), generated_text, fill=(255,255,0))
        img.save(file_path)
    
    return file_path 