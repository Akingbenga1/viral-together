# Viral Together

A platform for connecting influencers and businesses for collaboration opportunities.

## Features

### 🚀 **Async Document Generation**
- **Background Processing**: Document generation using AI happens asynchronously 
- **Real-time Status Tracking**: Check generation progress with dedicated status endpoints
- **No HTTP Timeouts**: API responds immediately while processing continues in background
- **File Downloads**: Direct download links for completed documents
- **Multiple Formats**: Support for PDF, PNG, TXT, and HTML generation
- **AI-Powered**: Uses Ollama with DeepSeek-R1 for intelligent document creation

### 📄 **Document Templates**
- **Admin Upload**: Admins can upload template files (.txt, .docx, .pdf, .html, .json)
- **Auto-Sourcing**: Automatically fetch templates from GitHub repos and APIs
- **Template Validation**: Optional validation for faster development
- **Multiple Sources**: GitHub, legal platforms, and custom template APIs

### 📊 **Business Intelligence Documents**
- **Business Plan Generation**: Influencers can now generate comprehensive business plans based on their profile, industry, and target markets
- **Specific Collaboration Requests**: Businesses can generate personalized collaboration proposals for specific influencers using detailed campaign requirements
- **General Collaboration Requests**: Businesses can create broad outreach documents for multiple influencers with targeting criteria and application processes
- **Enhanced PDF Formatting**: All documents now support advanced markdown-to-PDF conversion with proper multi-page layouts, headers, and styling

### 👥 **User Management**
- User authentication and authorization
- Role-based access control (admin, influencer, business, etc.)
- Profile management

### 🤝 **Collaboration Features**
- Influencer and business matching
- Promotion management
- Rate card system
- Subscription plans

## API Endpoints

### Document Generation (Async)
```http
POST /documents/generate                              # Start async document generation
POST /documents/generate-business-plan                # Generate business plan for influencers
POST /documents/generate-collaboration-request-specific   # Generate personalized collaboration request for specific influencer
POST /documents/generate-collaboration-request-general    # Generate general collaboration request for multiple influencers
GET /documents/{id}/status                           # Check generation status  
GET /documents/{id}/download                         # Download completed document
GET /documents/                                      # List documents with filtering
```

### Document Templates
```http
POST /document-templates/upload    # Admin upload templates
POST /document-templates/auto-source  # Auto-source from online
GET /document-templates/           # List templates
GET /document-templates/{id}       # Get specific template
DELETE /document-templates/{id}    # Delete template (admin)
```

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Database
```bash
# Run migrations
alembic upgrade head
```

### 3. Configure Environment
```bash
# Copy environment file
cp .env.example .env

# Set your environment variables:
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/db
SECRET_KEY=your-secret-key
OLLAMA_HOST=http://localhost:11434
```

### 4. Run the Application
```bash
# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Test Document Generation
```bash
# Generate a business plan for influencer (returns immediately)
curl -X POST "http://localhost:8000/documents/generate-business-plan" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "influencer_id": 1,
    "industry": "Fashion & Lifestyle",
    "product": "Sustainable Clothing Line",
    "countries": ["United States", "Canada"],
    "file_format": "pdf"
  }'

# Generate specific collaboration request (business → influencer)
curl -X POST "http://localhost:8000/documents/generate-collaboration-request-specific" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "business_id": 1,
    "influencer_id": 1,
    "campaign_title": "Summer Collection 2024",
    "campaign_description": "Promote our new summer fashion line",
    "deliverables": ["3 Instagram posts", "1 TikTok video"],
    "compensation_amount": 2500.00,
    "campaign_duration": "2 weeks",
    "content_requirements": "Authentic lifestyle shots",
    "deadline": "2024-07-15",
    "file_format": "pdf"
  }'

# Check generation status
curl -X GET "http://localhost:8000/documents/1/status" \
  -H "Authorization: Bearer your-token"

# Download completed document
curl -X GET "http://localhost:8000/documents/1/download" \
  -H "Authorization: Bearer your-token" \
  -o document.pdf
```

## Development Features

### Optional Template Validation
Speed up development by skipping template validation:

```http
POST /documents/generate?skip_template_validation=true
```

### Development Mode Benefits
- ✅ Generate documents without templates
- ✅ Graceful fallbacks for missing templates  
- ✅ Parameter-based content generation
- ✅ Flexible file format support

## Architecture

### Background Task Processing
- **FastAPI BackgroundTasks**: Handles async document generation
- **Database Status Tracking**: Real-time job status updates
- **Error Recovery**: Proper error handling and status reporting
- **Concurrent Processing**: Multiple documents can generate simultaneously

### AI Integration  
- **Ollama Integration**: Local AI model processing
- **DeepSeek-R1 Model**: Advanced reasoning for document generation
- **Clean Output**: `think=False` parameter removes reasoning traces
- **Fallback Processing**: Template substitution when AI unavailable

### Database Design
- **Async Sessions**: Full async/await support
- **Status Tracking**: pending → processing → completed/failed
- **Nullable Templates**: Support for template-optional development
- **Error Logging**: Detailed error message storage

## Testing

Use the provided HTTP test files:
- `api-test/documents.http` - Async document generation tests
- `api-test/document_templates.http` - Template management tests

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **AI**: Ollama, DeepSeek-R1
- **Authentication**: JWT tokens
- **Document Generation**: ReportLab (PDF), Pillow (Images)
- **Background Tasks**: FastAPI BackgroundTasks
- **Database Migrations**: Alembic

## License

MIT License
