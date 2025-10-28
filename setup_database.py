#!/usr/bin/env python3

import sqlite3
import hashlib
import uuid
from datetime import datetime

def hash_password(password: str) -> str:
    """Hash a password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def setup_database():
    """Create the necessary database tables and seed data"""
    
    # Connect to SQLite database
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()
    
    print("Creating tables...")
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            username VARCHAR(150) UNIQUE NOT NULL,
            hashed_password VARCHAR(200),
            mobile VARCHAR(20),
            description TEXT,
            email VARCHAR(255),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create task_status table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS task_status (
            task_id VARCHAR(255) PRIMARY KEY,
            user_id INTEGER NOT NULL,
            task_type VARCHAR(100) NOT NULL,
            status VARCHAR(50) NOT NULL,
            message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME,
            result TEXT,  -- JSON as TEXT in SQLite
            error_details TEXT,
            celery_task_id VARCHAR(255),
            task_data TEXT,  -- JSON as TEXT in SQLite
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Create indexes for task_status
    cursor.execute('CREATE INDEX IF NOT EXISTS ix_task_status_user_id ON task_status(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS ix_task_status_task_type ON task_status(task_type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS ix_task_status_status ON task_status(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS ix_task_status_celery_task_id ON task_status(celery_task_id)')
    
    # Create ai_agents table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid VARCHAR(36) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            agent_type VARCHAR(100) NOT NULL,
            capabilities TEXT NOT NULL,  -- JSON as TEXT in SQLite
            status VARCHAR(50) DEFAULT 'active',
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    print("Seeding test user...")
    
    # Insert test user: Akingbenga with password kazeem123456
    hashed_pass = hash_password("kazeem123456")
    cursor.execute('''
        INSERT OR REPLACE INTO users 
        (first_name, last_name, username, hashed_password, email)
        VALUES (?, ?, ?, ?, ?)
    ''', ("Akin", "Benga", "Akingbenga", hashed_pass, "akingbenga@test.com"))
    
    print("Seeding AI agents...")
    
    # AI Agents data
    ai_agents_data = [
        {
            'uuid': str(uuid.uuid4()),
            'name': 'Influencer Growth Agent',
            'agent_type': 'growth_advisor',
            'capabilities': '{"content_strategy": true, "audience_analysis": true, "platform_optimization": true, "engagement_tactics": true, "growth_metrics": true, "trend_identification": true}'
        },
        {
            'uuid': str(uuid.uuid4()),
            'name': 'Business Development Agent',
            'agent_type': 'business_advisor',
            'capabilities': '{"market_research": true, "partnership_opportunities": true, "brand_strategy": true, "revenue_optimization": true, "business_planning": true, "competitive_analysis": true}'
        },
        {
            'uuid': str(uuid.uuid4()),
            'name': 'Content Strategy Agent',
            'agent_type': 'content_advisor',
            'capabilities': '{"content_planning": true, "trend_analysis": true, "creative_direction": true, "publishing_schedule": true, "content_optimization": true, "storytelling": true}'
        },
        {
            'uuid': str(uuid.uuid4()),
            'name': 'Analytics & Insights Agent',
            'agent_type': 'analytics_advisor',
            'capabilities': '{"performance_analysis": true, "data_interpretation": true, "kpi_tracking": true, "optimization_recommendations": true, "reporting": true, "predictive_analytics": true}'
        },
        {
            'uuid': str(uuid.uuid4()),
            'name': 'Collaboration Manager Agent',
            'agent_type': 'collaboration_advisor',
            'capabilities': '{"partnership_matching": true, "campaign_coordination": true, "communication_facilitation": true, "project_management": true, "contract_negotiation": true, "relationship_building": true}'
        },
        {
            'uuid': str(uuid.uuid4()),
            'name': 'Rate Card Optimization Agent',
            'agent_type': 'pricing_advisor',
            'capabilities': '{"market_rate_analysis": true, "pricing_strategy": true, "value_proposition": true, "negotiation_support": true, "pricing_optimization": true, "revenue_maximization": true}'
        },
        {
            'uuid': str(uuid.uuid4()),
            'name': 'Social Media Platform Specialist',
            'agent_type': 'platform_advisor',
            'capabilities': '{"instagram_optimization": true, "tiktok_strategy": true, "youtube_management": true, "cross_platform_synergy": true, "platform_algorithms": true, "feature_optimization": true}'
        },
        {
            'uuid': str(uuid.uuid4()),
            'name': 'Brand Safety & Compliance Agent',
            'agent_type': 'compliance_advisor',
            'capabilities': '{"content_moderation": true, "brand_guidelines": true, "regulatory_compliance": true, "risk_assessment": true, "policy_enforcement": true, "legal_guidance": true}'
        },
        {
            'uuid': str(uuid.uuid4()),
            'name': 'Community Engagement Agent',
            'agent_type': 'engagement_advisor',
            'capabilities': '{"audience_interaction": true, "community_building": true, "feedback_management": true, "relationship_nurturing": true, "engagement_strategies": true, "community_moderation": true}'
        },
        {
            'uuid': str(uuid.uuid4()),
            'name': 'Performance Optimization Agent',
            'agent_type': 'optimization_advisor',
            'capabilities': '{"campaign_optimization": true, "roi_analysis": true, "a_b_testing": true, "performance_forecasting": true, "efficiency_improvement": true, "resource_optimization": true}'
        }
    ]
    
    # Insert AI agents
    for agent_data in ai_agents_data:
        cursor.execute('''
            INSERT OR REPLACE INTO ai_agents 
            (uuid, name, agent_type, capabilities, status, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (agent_data['uuid'], agent_data['name'], agent_data['agent_type'], 
              agent_data['capabilities'], 'active', 1, datetime.now(), datetime.now()))
    
    # Commit changes
    conn.commit()
    
    # Verify data
    print("Verifying setup...")
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    print(f"Users created: {user_count}")
    
    cursor.execute("SELECT COUNT(*) FROM ai_agents")
    agent_count = cursor.fetchone()[0]
    print(f"AI Agents created: {agent_count}")
    
    cursor.execute("SELECT username, email FROM users")
    users = cursor.fetchall()
    for user in users:
        print(f"User: {user[0]} ({user[1]})")
    
    cursor.execute("SELECT agent_type, name FROM ai_agents")
    agents = cursor.fetchall()
    for agent in agents:
        print(f"Agent: {agent[0]} - {agent[1]}")
    
    conn.close()
    print("Database setup completed successfully!")

if __name__ == "__main__":
    setup_database()