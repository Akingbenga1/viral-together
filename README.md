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

---

# 🔔 Notification System

A comprehensive, event-driven notification platform that automatically sends notifications via email, Twitter/X, and real-time WebSocket connections.

## Overview

The notification system supports:
- **📧 Email notifications** (SMTP & transactional services)
- **🐦 Twitter/X integration** with MCP tool calling and Ollama content generation  
- **⚡ Real-time WebSocket notifications** for the UI
- **🎛️ User preferences** and opt-out functionality
- **🚀 Background processing** with auto-retry
- **📊 Complete API** with CRUD operations and filtering

## 🎯 Event Triggers

The system automatically creates notifications for these events:

1. **POST /promotions** - Notifies relevant influencers about new promotions
2. **POST /promotions/{id}/show-interest** - Notifies businesses when influencers show interest
3. **POST /collaborations/{id}/approve** - Notifies influencers when collaborations are approved
4. **POST /collaborations/approve-multiple** - Bulk approval notifications

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Database Migration
```bash
# Run the notification system migration
alembic upgrade head
```

### 3. Environment Configuration

Add these to your `.env` file:

```bash
# Basic Notification Settings
NOTIFICATIONS_ENABLED=true
EMAIL_NOTIFICATIONS_ENABLED=true
TWITTER_NOTIFICATIONS_ENABLED=true
WEBSOCKET_ENABLED=true

# Email Configuration (choose one)
EMAIL_BACKEND=smtp  # or 'sendgrid', 'mailgun'
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Twitter Configuration
TWITTER_API_KEY=your-api-key
TWITTER_API_SECRET=your-api-secret
TWITTER_ACCESS_TOKEN=your-access-token
TWITTER_ACCESS_TOKEN_SECRET=your-access-token-secret

# Ollama for Tweet Generation
OLLAMA_MODEL=deepseek-r1:1.5b
OLLAMA_BASE_URL=http://localhost:11434
```

## 📧 Email Configuration Options

### SMTP (Development/Testing)
```bash
EMAIL_BACKEND=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### SendGrid (Production)
```bash
EMAIL_BACKEND=sendgrid
SENDGRID_API_KEY=SG.your-sendgrid-api-key
```

### Mailgun (Production Alternative)
```bash
EMAIL_BACKEND=mailgun
MAILGUN_API_KEY=your-mailgun-api-key
MAILGUN_DOMAIN=your-domain.mailgun.org
```

## 🐦 Twitter Integration

The system uses MCP tool calling with Ollama for intelligent tweet generation:

- **Templates**: Fixed templates with dynamic variable substitution
- **AI Enhancement**: Ollama generates contextual, engaging content
- **Rate Limiting**: Respects Twitter API limits with backoff
- **Error Handling**: Auto-retry with exponential backoff

### Twitter API Setup
1. Create Twitter Developer account
2. Generate API keys and tokens
3. Add credentials to environment variables
4. Enable tweet posting in your app permissions

## 🔌 WebSocket Integration

Real-time notifications are available via WebSocket:

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/notifications/ws/USER_ID');

// Listen for notifications
ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    if (message.type === 'notification') {
        // Handle new notification
        console.log('New notification:', message.data);
    }
};

// Send ping to keep connection alive
ws.send(JSON.stringify({type: 'ping', data: {}}));
```

## 🛠️ Notification API Endpoints

### Core Notification Operations
```http
GET /notifications                              # List notifications with filtering
GET /notifications/{id}                        # Get specific notification
PUT /notifications/{id}/mark-read              # Mark as read
DELETE /notifications/{id}                     # Delete notification
GET /notifications/stats                       # Get statistics
GET /notifications/unread-count               # Get unread count
```

### Bulk Operations
```http
PUT /notifications/mark-all-read               # Mark all as read
PUT /notifications/bulk-mark-read              # Mark specific ones as read
DELETE /notifications/bulk-delete              # Delete multiple
```

### User Preferences
```http
GET /notifications/preferences                 # Get user preferences
POST /notifications/preferences/{event_type}   # Create/update preference
PUT /notifications/preferences/{event_type}    # Update preference
DELETE /notifications/preferences/{event_type} # Delete (revert to default)
```

### WebSocket
```http
WS /notifications/ws/{user_id}                 # Real-time connection
```

### Admin (System Monitoring)
```http
GET /notifications/admin/stats                 # System-wide statistics
```

## 🧪 Testing Notifications

### Test Event Triggers
```bash
# Trigger promotion_created notification
curl -X POST "http://localhost:8000/promotions" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "business_id": 1,
    "promotion_name": "Summer Fashion Campaign 2024",
    "description": "Promote our latest summer collection",
    "industry": "Fashion",
    "budget": 5000.00
  }'

# Trigger influencer_interest notification
curl -X POST "http://localhost:8000/promotions/1/show-interest" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "influencer_id": 1,
    "proposed_amount": 500.00,
    "collaboration_type": "instagram_post",
    "deliverables": "3 Instagram posts, 5 stories",
    "message": "I love your brand and would love to collaborate!"
  }'

# Trigger collaboration_approved notification
curl -X POST "http://localhost:8000/collaborations/1/approve" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"business_id": 1}'
```

### Test Notification Management
```bash
# Get all notifications with filters
curl -X GET "http://localhost:8000/notifications?event_type=promotion_created&read_status=false&limit=10" \
  -H "Authorization: Bearer your-token"

# Mark notification as read
curl -X PUT "http://localhost:8000/notifications/NOTIFICATION_ID/mark-read" \
  -H "Authorization: Bearer your-token"

# Get notification statistics
curl -X GET "http://localhost:8000/notifications/stats" \
  -H "Authorization: Bearer your-token"
```

### Test User Preferences
```bash
# Set notification preferences
curl -X POST "http://localhost:8000/notifications/preferences/promotion_created?email_enabled=true&in_app_enabled=true" \
  -H "Authorization: Bearer your-token"

# Get all preferences
curl -X GET "http://localhost:8000/notifications/preferences" \
  -H "Authorization: Bearer your-token"
```

## 📊 Notification Features

### ✅ Multi-Channel Delivery
- **📧 Email**: Beautiful HTML templates with professional styling
- **🐦 Twitter**: AI-generated tweets with hashtags and engagement optimization
- **⚡ WebSocket**: Real-time notifications for instant UI updates
- **📱 API**: Complete management interface with filtering and bulk operations

### ✅ User Control
- **🎛️ Preferences**: Users can opt-out of any notification type
- **🔍 Filtering**: Filter by event type, read status, date range
- **📄 Pagination**: Handle large notification lists efficiently
- **📊 Statistics**: View delivery status and engagement metrics

### ✅ Production Ready
- **🚀 Background Processing**: Non-blocking with auto-retry logic
- **🔒 Security**: JWT authentication, user-scoped data access
- **📈 Scalable**: Async operations, efficient database queries
- **🧪 Well-Tested**: Comprehensive test suite in `api-test/notifications.http`

## 🗂️ Comprehensive HTTP Tests

Use the provided test file for complete testing:

```bash
# Test file location
api-test/notifications.http
```

The test file includes:
- ✅ All CRUD operations  
- ✅ Bulk operations
- ✅ User preferences
- ✅ Event trigger tests
- ✅ Error scenarios
- ✅ WebSocket examples
- ✅ Filtering and pagination
- ✅ Stress tests

## 🚨 Troubleshooting

### Common Issues

**Notifications not sending:**
- Check `NOTIFICATIONS_ENABLED=true` in environment
- Verify service initialization in logs
- Check background task processing

**Email delivery failures:**
- Verify SMTP credentials
- Check EMAIL_BACKEND configuration
- Review email service logs

**Twitter posts failing:**
- Verify Twitter API credentials
- Check rate limiting
- Ensure Ollama is running

**WebSocket connection issues:**
- Check WEBSOCKET_ENABLED setting
- Verify user authentication
- Monitor connection logs

### Debug Mode
Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔐 Security Features

- ✅ All endpoints require authentication
- ✅ User can only access their own notifications
- ✅ Preferences are user-scoped
- ✅ Email templates sanitize user input
- ✅ WebSocket connections support authentication
- ✅ Twitter API credentials are securely stored

## 🚀 System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Endpoints │───▶│ Notification    │───▶│ Background      │
│                 │    │ Service         │    │ Tasks           │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Database      │    │ User            │    │ External        │
│   Models        │    │ Preferences     │    │ Services        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                              ┌────────────────────────┼────────────────────────┐
                              ▼                        ▼                        ▼
                    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
                    │ Email Service   │    │ Twitter Service │    │ WebSocket       │
                    │ (SMTP/SendGrid) │    │ (MCP + Ollama)  │    │ Service         │
                    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📈 Performance & Monitoring

### Performance Features
- ✅ Background task processing prevents blocking
- ✅ Database queries optimized with indexes
- ✅ WebSocket connections efficiently managed
- ✅ Email/Twitter failures include retry logic
- ✅ Bulk operations reduce API calls

### Monitoring Endpoints
```bash
# System-wide statistics
GET /notifications/admin/stats

# User-specific statistics  
GET /notifications/stats

# Real-time connection count
# Available via WebSocket service metrics
```

The notification system is now fully operational and ready for production use! 🎉

---

# MCP Social Media Integration - Option 1 Implementation

## 🎯 **Implementation Overview**

This implements **Option 1: Generic MCP Client** approach, maintaining your excellent existing architecture while adding flexible MCP tool integration.

## 🏗️ **Architecture**

```
Notification Event → Ollama Content Generation → MCP Tool Calling → Social Media Posting
```

### **Key Components:**

1. **SimpleMCPClient** (`app/services/mcp_client.py`)
   - Lightweight MCP client for tool calling
   - Loads configuration from `mcp_config.json`
   - Handles subprocess communication with MCP servers

2. **Enhanced TwitterService** (`app/services/twitter_service.py`)
   - Keeps existing Ollama content generation (unchanged)
   - Replaces simulation with real MCP calls
   - Maintains all error handling and logging

3. **MCP Configuration** (`mcp_config.json`)
   - Pre-configured with 6 social media platforms
   - Environment variable integration
   - Tool definitions for each platform

## 📦 **Configured Social Media Tools**

### **1. Twitter/X** (Real Implementation)
- **Server**: `@enescinar/twitter-mcp`
- **Tools**: `post_tweet`, `search_tweets`, `delete_tweet`, `get_tweet_metrics`
- **Status**: ✅ Ready to use

### **2. LinkedIn** (Ready for Implementation)
- **Tools**: `post_update`, `share_article`, `post_company_update`, `get_post_analytics`
- **Use Case**: Professional networking, business updates

### **3. Instagram** (Ready for Implementation)
- **Tools**: `post_image`, `post_story`, `post_reel`, `get_media_insights`
- **Use Case**: Visual content, stories, reels

### **4. Facebook** (Ready for Implementation)
- **Tools**: `post_to_page`, `create_event`, `post_photo`, `get_page_insights`
- **Use Case**: Page management, events, community engagement

### **5. TikTok** (Ready for Implementation)
- **Tools**: `upload_video`, `post_with_music`, `get_trending_hashtags`, `get_video_analytics`
- **Use Case**: Short-form video content, trending participation

### **6. YouTube** (Ready for Implementation)
- **Tools**: `upload_video`, `create_playlist`, `add_to_playlist`, `get_video_stats`
- **Use Case**: Long-form content, playlists, channel management

## 🚀 **Setup Instructions**

### **1. Install Twitter MCP Server**
```bash
npm install -g @enescinar/twitter-mcp
```

### **2. Set Environment Variables**
```bash
# Twitter API credentials
export TWITTER_API_KEY="your_api_key"
export TWITTER_API_SECRET="your_api_secret"
export TWITTER_ACCESS_TOKEN="your_access_token"
export TWITTER_ACCESS_TOKEN_SECRET="your_access_token_secret"

# Future: Other platform credentials
export LINKEDIN_CLIENT_ID="your_linkedin_client_id"
export INSTAGRAM_ACCESS_TOKEN="your_instagram_token"
# ... etc
```

### **3. Test Integration**
```bash
# Use the provided test file
# api-test/mcp_social_media.http
```

## 📊 **How It Works**

### **Notification Flow:**
1. **Event Trigger**: API endpoint called (e.g., `POST /promotions`)
2. **Content Generation**: Ollama creates enhanced tweet content (unchanged)
3. **MCP Tool Call**: SimpleMCPClient calls `twitter-tools/post_tweet`
4. **Real Posting**: MCP server posts to actual Twitter API
5. **Response Handling**: Tweet ID returned and logged

### **MCP Call Example:**
```python
result = await self.mcp_client.call_tool(
    server="twitter-tools",
    tool="post_tweet", 
    arguments={
        "content": "🎯 EXCITING OPPORTUNITY! StyleCorp Inc just launched...",
        "metadata": {"promotion_id": 123, "business_name": "StyleCorp Inc"}
    }
)
tweet_id = result.get("tweet_id")
```

## ✅ **Benefits of This Implementation**

### **Preserved Excellence:**
- ✅ **Direct Ollama calls**: Fast, reliable content generation
- ✅ **Comprehensive logging**: All existing monitoring intact
- ✅ **Error handling**: Retry logic and fallbacks work perfectly
- ✅ **Background tasks**: Async processing unchanged

### **Added Flexibility:**
- ✅ **6 Social platforms**: Ready for expansion
- ✅ **Easy tool addition**: Just update `mcp_config.json`
- ✅ **Independent scaling**: Add platforms without code changes
- ✅ **Real MCP ecosystem**: Access to 100+ MCP servers

## 🔧 **Extending to Other Platforms**

### **To Add a New Social Platform:**

1. **Add to `mcp_config.json`:**
```json
"new-platform-tools": {
  "command": "npx",
  "args": ["-y", "@social-mcp/new-platform"],
  "env": {"API_KEY": "${NEW_PLATFORM_API_KEY}"},
  "tools": ["post_content", "get_analytics"]
}
```

2. **Use in Services:**
```python
# No code changes needed! Just call:
await self.mcp_client.call_tool("new-platform-tools", "post_content", args)
```

## 📈 **Current Status**

- ✅ **Twitter**: Fully implemented and ready
- 🟡 **LinkedIn/Instagram/Facebook/TikTok/YouTube**: Configured, awaiting MCP servers
- ✅ **Architecture**: Production ready
- ✅ **Logging**: Comprehensive monitoring
- ✅ **Testing**: HTTP test suite provided

## 🎯 **Next Steps**

1. **Test Twitter integration** with real API keys
2. **Install additional MCP servers** as they become available
3. **Expand notification templates** for different platforms
4. **Add platform-specific content optimization**

---

**This implementation gives you the best of both worlds: your excellent existing architecture + flexible MCP tool ecosystem access.**
