import ollama
import markdown
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.pdfgen import canvas
from PIL import Image, ImageDraw
from jinja2 import Template
from app.core.config import settings
from app.db.models.document_templates import DocumentTemplate
from typing import Union, Optional, List
import uuid
import logging

logger = logging.getLogger(__name__)

def parse_markdown_to_reportlab(markdown_text: str) -> List:
    """Enhanced markdown parser with better formatting support"""
    
    # Add debugging
    logger.info(f"Processing markdown content length: {len(markdown_text)}")
    logger.debug(f"First 200 chars: {markdown_text[:200]}...")
    
    # Get default styles
    styles = getSampleStyleSheet()
    
    # Create custom styles for better formatting
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=12,
        textColor='black',
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=8,
        textColor='black',
        fontName='Helvetica-Bold'
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubheading',
        parent=styles['Heading3'],
        fontSize=12,
        spaceAfter=6,
        textColor='black',
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        textColor='black',
        fontName='Helvetica'
    )
    
    bullet_style = ParagraphStyle(
        'CustomBullet',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=4,
        leftIndent=20,
        bulletIndent=10,
        textColor='black',
        fontName='Helvetica'
    )
    
    story = []
    lines = markdown_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            story.append(Spacer(1, 6))
            continue
            
        # Enhanced processing with better detection
        if line.startswith('# '):
            # H1 - Main titles
            content = line[2:].strip()
            content = convert_inline_markdown(content)  # Handle inline formatting
            story.append(Paragraph(content, title_style))
            story.append(Spacer(1, 12))
            
        elif line.startswith('## '):
            # H2 - Sections  
            content = line[3:].strip()
            content = convert_inline_markdown(content)
            story.append(Paragraph(content, heading_style))
            story.append(Spacer(1, 8))
            
        elif line.startswith('### '):
            # H3 - Subsections
            content = line[4:].strip()
            content = convert_inline_markdown(content)
            story.append(Paragraph(content, subheading_style))
            story.append(Spacer(1, 6))
            
        elif line.startswith('- ') or line.startswith('* '):
            # Bullet points
            content = line[2:].strip()
            content = convert_inline_markdown(content)
            story.append(Paragraph(f"• {content}", bullet_style))
            
        elif re.match(r'^\d+\.\s', line):
            # Numbered lists
            content = re.sub(r'^\d+\.\s', '', line).strip()
            content = convert_inline_markdown(content)
            number = re.match(r'^(\d+)\.', line).group(1)
            story.append(Paragraph(f"{number}. {content}", bullet_style))
            
        else:
            # Regular paragraphs - ENHANCED to handle all inline markdown
            content = convert_inline_markdown(line)
            if content:
                story.append(Paragraph(content, normal_style))
                story.append(Spacer(1, 4))
    
    # Add fallback if no content parsed
    if not story:
        logger.warning("No markdown content parsed, using fallback")
        story = [Paragraph("Generated Business Plan", title_style)]
        story.append(Spacer(1, 12))
        # Strip markdown and use as plain text
        plain_text = strip_markdown_syntax(markdown_text)
        story.append(Paragraph(plain_text, normal_style))
    
    logger.info(f"Processed {len(story)} story elements for PDF")
    return story

def convert_inline_markdown(text: str) -> str:
    """Enhanced inline markdown formatting converter for ReportLab HTML-like tags"""
    
    if not text:
        return text
    
    # Handle nested formatting more carefully
    # Bold text: **text** or __text__ -> <b>text</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__(.*?)__', r'<b>\1</b>', text)
    
    # Italic text: *text* or _text_ -> <i>text</i> (but avoid already converted bold)
    text = re.sub(r'(?<!</b>)\*([^*]+?)\*(?!<)', r'<i>\1</i>', text)
    text = re.sub(r'(?<!</b>)_([^_]+?)_(?!<)', r'<i>\1</i>', text)
    
    # Code: `code` -> <font name="Courier">code</font>
    text = re.sub(r'`(.*?)`', r'<font name="Courier">\1</font>', text)
    
    # Handle special characters that might break ReportLab
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;').replace('>', '&gt;')
    
    # Restore our formatting tags
    text = text.replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>')
    text = text.replace('&lt;i&gt;', '<i>').replace('&lt;/i&gt;', '</i>')
    text = text.replace('&lt;font name="Courier"&gt;', '<font name="Courier">').replace('&lt;/font&gt;', '</font>')
    
    return text

def strip_markdown_syntax(text: str) -> str:
    """Fallback function to strip markdown syntax for plain text display"""
    
    if not text:
        return text
    
    # Remove common markdown syntax
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)  # Headers
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)           # Bold
    text = re.sub(r'__(.*?)__', r'\1', text)               # Bold (alternative)
    text = re.sub(r'\*(.*?)\*', r'\1', text)               # Italic
    text = re.sub(r'_(.*?)_', r'\1', text)                 # Italic (alternative)
    text = re.sub(r'`(.*?)`', r'\1', text)                 # Code
    text = re.sub(r'^[-*+]\s+', '• ', text, flags=re.MULTILINE)  # Bullets
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)   # Numbered lists
    
    # Clean up extra whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines
    text = text.strip()
    
    return text

def generate_multi_page_pdf(content: str, file_path: str) -> None:
    """Enhanced PDF generation with better markdown handling"""
    
    logger.info(f"Generating PDF with content length: {len(content)}")
    
    try:
        # Log sample of content for debugging
        sample = content[:500] if len(content) > 500 else content
        logger.debug(f"PDF content sample: {sample}")
        
        # Create document with margins
        doc = SimpleDocTemplate(
            file_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Parse markdown content into ReportLab elements
        story = parse_markdown_to_reportlab(content)
        
        if len(story) < 3:  # Very few elements parsed
            logger.warning("Very few elements parsed, content might not be markdown format")
            logger.warning(f"Story elements count: {len(story)}")
        
        if not story:
            # Enhanced fallback if no content parsed
            logger.error("No story elements created, using enhanced fallback")
            styles = getSampleStyleSheet()
            story = [Paragraph("Generated Document", styles['Title'])]
            story.append(Spacer(1, 12))
            
            # Try to strip markdown and create readable content
            plain_content = strip_markdown_syntax(content)
            if plain_content:
                # Split into paragraphs for better readability
                paragraphs = plain_content.split('\n\n')
                for para in paragraphs:
                    if para.strip():
                        story.append(Paragraph(para.strip(), styles['Normal']))
                        story.append(Spacer(1, 6))
            else:
                story.append(Paragraph(content[:1000], styles['Normal']))
        
        # Build the PDF - automatically handles multiple pages
        doc.build(story)
        logger.info(f"Multi-page PDF generated successfully: {file_path}")
        logger.info(f"Final story had {len(story)} elements")
        
    except Exception as e:
        logger.error(f"Enhanced PDF generation failed: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        # Use the existing fallback
        generate_simple_pdf_fallback(content, file_path)

def generate_simple_pdf_fallback(content: str, file_path: str) -> None:
    """Fallback PDF generation method if advanced formatting fails"""
    
    c = canvas.Canvas(file_path, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, height - 72, "Generated Document")
    
    # Content
    c.setFont("Helvetica", 10)
    lines = content.split('\n')
    y_position = height - 120
    line_height = 14
    
    for line in lines:
        if y_position < 72:  # Check if we need a new page
            c.showPage()
            c.setFont("Helvetica", 10)
            y_position = height - 72
        
        # Handle long lines by wrapping
        if len(line) > 80:
            words = line.split(' ')
            current_line = ''
            for word in words:
                if len(current_line + word) < 80:
                    current_line += word + ' '
                else:
                    if current_line:
                        c.drawString(72, y_position, current_line.strip())
                        y_position -= line_height
                        if y_position < 72:
                            c.showPage()
                            c.setFont("Helvetica", 10)
                            y_position = height - 72
                    current_line = word + ' '
            if current_line:
                c.drawString(72, y_position, current_line.strip())
                y_position -= line_height
        else:
            c.drawString(72, y_position, line)
            y_position -= line_height
    
    c.save()
    logger.info(f"Fallback PDF generated: {file_path}")

def generate_document(template: Optional[Union[DocumentTemplate, object]], params: dict, related_data: dict) -> str:
    """Enhanced document generator that handles optional templates for development speed"""
    
    # Handle missing or minimal template scenarios
    if template is None:
        logger.info("No template provided, using fallback generation")
        prompt_text = params.get('content', 'Default document content: {{content}}')
        file_format = params.get('file_format', 'pdf')
        template_id = 'fallback'
    else:
        # Check if template has required attributes
        if hasattr(template, 'prompt_text'):
            prompt_text = template.prompt_text
            file_format = getattr(template, 'file_format', 'pdf')
            template_id = getattr(template, 'id', 'unknown')
        else:
            # Handle simple namespace objects
            prompt_text = getattr(template, 'prompt_text', params.get('content', 'Default content'))
            file_format = getattr(template, 'file_format', 'pdf')
            template_id = 'minimal'
    
    try:
        # Try Ollama first if available
        all_params = {**params, **related_data}
        
        # Simple parameter substitution for fallback
        generated_text = prompt_text
        for key, value in all_params.items():
            generated_text = generated_text.replace(f'{{{{{key}}}}}', str(value))
        
        # Try advanced generation with Ollama (NO THINKING MODE)
        try:
            # logger.info(f"Using Ollama model: deepseek-r1:1.14b")
            # logger.info(f"Input prompt: {generated_text[:100]}...")
            if '{{' not in generated_text:  # Only if we have a complete prompt
                
                # Use chat method with think=False for clean responses
                response = ollama.chat(
                    model=settings.OLLAMA_MODEL,
                    messages=[{
                        'role': 'system', 
                        'content': 'You are a professional document generator. Create clear, well-structured documents based on the provided content. Provide direct responses without showing your reasoning process. Ensure you complete all sections of the document at all times no matter the content lenght and time taken to egenerate the content. Make sure you do not miss any sections or details.'
                    }, {
                        'role': 'user', 
                        'content': generated_text
                    }],
                    think=False  # Disable thinking traces for clean output
                )
                
                # Extract clean response without thinking
                generated_text = response['message']['content']
                logger.info(f"Clean Ollama response received: {(generated_text)} characters")
                
            else:
                logger.warning("Template has unfilled placeholders, skipping Ollama generation")
        except Exception as ollama_error:
            logger.warning(f"Ollama generation failed: {ollama_error}, using template substitution")
            # Continue with substituted text
            
    except Exception as e:
        logger.error(f"Error in text generation: {e}")
        # Ultimate fallback
        generated_text = f"Document generated with parameters: {params}"
    
    # Create unique filename
    unique_id = str(uuid.uuid4())[:8]
    file_path = f"{settings.DOC_STORAGE_PATH}/doc_{template_id}_{unique_id}.{file_format}"
    
    try:
        # Create file based on format
        if file_format == 'pdf':
            # Use new multi-page PDF generation with markdown support
            generate_multi_page_pdf(generated_text, file_path)
            
        elif file_format in ['image', 'png']:
            # Enhanced image generation with better text handling
            img = Image.new('RGB', (1200, 800), color=(255, 255, 255))
            d = ImageDraw.Draw(img)
            
            # Handle long text by wrapping
            wrapped_text = []
            lines = generated_text.split('\n')
            for line in lines:
                if len(line) > 100:
                    # Wrap long lines
                    words = line.split(' ')
                    current_line = ''
                    for word in words:
                        if len(current_line + word) < 100:
                            current_line += word + ' '
                        else:
                            wrapped_text.append(current_line.strip())
                            current_line = word + ' '
                    if current_line:
                        wrapped_text.append(current_line.strip())
                else:
                    wrapped_text.append(line)
            
            # Draw text with proper spacing
            y_offset = 20
            line_height = 20
            for line in wrapped_text[:35]:  # Limit lines to fit image
                d.text((20, y_offset), line, fill=(0, 0, 0))
                y_offset += line_height
                
            img.save(file_path)
    
        else:
            # Default to text file for unknown formats with full content
            file_path = file_path.replace(f'.{file_format}', '.txt')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(generated_text)
                
    except Exception as file_error:
        logger.error(f"Error creating file: {file_error}")
        # Create simple text file as ultimate fallback
        fallback_path = f"{settings.DOC_STORAGE_PATH}/doc_fallback_{unique_id}.txt"
        with open(fallback_path, 'w', encoding='utf-8') as f:
            f.write(f"Generated Text:\n{generated_text}")
        return fallback_path
    
    logger.info(f"Document generated successfully: {file_path}")
    return file_path 