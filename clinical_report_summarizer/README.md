# UHG GenAI Projects Documentation

This repository contains two advanced GenAI projects developed for United Health Group (UHG):

1. **Clinical Report Summarization using LLMs**
2. **Medical Knowledge Retrieval Assistant for Doctors**

## Table of Contents

- [Project 1: Clinical Report Summarization](#project-1-clinical-report-summarization)
  - [Overview](#overview-1)
  - [Architecture](#architecture-1)
  - [Technology Stack](#technology-stack-1)
  - [Key Features](#key-features-1)
  - [Workflow](#workflow-1)
  - [Security & Compliance](#security--compliance-1)
  - [Monitoring & Performance](#monitoring--performance-1)
  - [Deployment](#deployment-1)
- [Project 2: Medical Knowledge Retrieval Assistant]

(#project-2-medical-knowledge-retrieval-assistant)
  - [Overview](#overview-2)
  - [Architecture](#architecture-2)
  - [Technology Stack](#technology-stack-2)
  - [Key Features](#key-features-2)
  - [Workflow](#workflow-2)
  - [Security & Compliance](#security--compliance-2)
  - [Monitoring & Performance](#monitoring--performance-2)
  - [Deployment](#deployment-2)
- [Getting Started](#getting-started)
- [Development Guidelines](#development-guidelines)
- [Contributing](#contributing)

## Project 1: Clinical Report Summarization

### Overview-1

The Clinical Report Summarization system transforms lengthy, complex clinical documents into concise, actionable summaries. The system processes discharge notes, radiology reports, and lab results to extract key insights, helping healthcare professionals quickly grasp essential patient information.

### Architecture-1

The system employs a microservices architecture with the following components:

- **API Layer**: FastAPI-based RESTful services with Keycloak integration for authentication
- **Processing Layer**: LLM-powered summarization engine using GPT-4 and LangChain
- **Streaming Layer**: Kafka (Amazon MSK) and Celery for asynchronous processing
- **Storage Layer**: Amazon S3 for raw documents and PostgreSQL (Amazon RDS) for structured data
- **Monitoring Layer**: Grafana and AWS CloudWatch for system observability

![Clinical Report Summarization Architecture](placeholder_for_architecture_diagram_1)

### Technology Stack-1

- **Backend**: Python 3.12, FastAPI
- **AI/ML**: GPT-4, LangChain
- **Data Processing**: Kafka (Amazon MSK), Celery
- **Storage**: PostgreSQL (Amazon RDS), Amazon S3
- **Security**: Keycloak
- **Monitoring**: Grafana, AWS CloudWatch
- **Infrastructure**: Docker, Kubernetes (EKS), Terraform
- **Frontend**: React.js
- **Methodology**: Agile

### Key Features-1

- **Intelligent Summarization**: Uses GPT-4 to extract and highlight critical information
- **Multi-document Support**: Processes diverse clinical document types
- **Real-time Processing**: Streams and processes documents as they arrive
- **Role-based Access Control**: Ensures data security and compliance
- **Scalable Architecture**: Handles varying workloads efficiently
- **High Availability**: 99.9% uptime guarantee
- **Audit Logging**: Comprehensive tracking of system usage

### Workflow-1

1. **Document Ingestion**:
   - Clinical documents are uploaded via API or file transfer
   - Documents are stored in Amazon S3 with appropriate metadata
   - Document metadata is recorded in PostgreSQL

2. **Processing Queue**:
   - Kafka receives document processing requests
   - Celery workers pick up tasks based on priority and load

3. **Document Analysis**:
   - Text extraction from various document formats
   - Preprocessing to standardize content
   - Entity recognition for medical terms

4. **Summarization**:
   - GPT-4 generates summaries based on document type and content
   - LangChain orchestrates the prompt engineering and response handling
   - Clinical validation rules ensure accuracy

5. **Results Storage**:
   - Summaries stored in PostgreSQL with links to source documents
   - Index creation for efficient retrieval

6. **Access & Delivery**:
   - API endpoints for retrieving summaries
   - Role-based permission checks via Keycloak
   - Frontend display with highlighting of key information

### Security & Compliance-1

- **Data Encryption**: At rest and in transit
- **Access Control**: Keycloak-powered authentication and authorization
- **HIPAA Compliance**: Adheres to healthcare data regulations
- **Audit Trails**: Comprehensive logging of all data access
- **Secure Infrastructure**: AWS security best practices implemented

### Monitoring & Performance-1

- **Real-time Metrics**: Grafana dashboards showing system health
- **Performance Tracking**: Response times, processing throughput
- **Error Handling**: Automated alerting for system issues
- **Resource Utilization**: CPU, memory, and storage monitoring
- **Uptime Tracking**: 99.9% availability monitoring

### Deployment-1

- **Infrastructure as Code**: Terraform scripts for AWS resource provisioning
- **Containerization**: Docker images for consistent environments
- **Orchestration**: Kubernetes (EKS) for container management
- **CI/CD**: Automated testing and deployment pipeline
- **Environment Isolation**: Dev, QA, and Production environments

## Project 2: Medical Knowledge Retrieval Assistant

### Overview-2

The Medical Knowledge Retrieval Assistant helps doctors quickly find relevant information from standard operating procedures (SOPs) and medical guidelines. Using advanced AI techniques including Retrieval-Augmented Generation (RAG), the system provides context-aware answers to clinical questions in multiple languages.

### Architecture-2

The system uses a cloud-native architecture with the following components:

- **API Layer**: FastAPI-based microservices with Firebase Auth integration
- **Retrieval Layer**: FAISS vector database with Vertex AI embeddings
- **Processing Layer**: GPT-4 and LangChain for RAG implementation
- **Storage Layer**: Google Cloud Storage for documents, Cloud SQL for metadata
- **Authentication Layer**: Firebase Auth with GCP IAM integration
- **Frontend Layer**: React-based micro-frontend architecture

![Medical Knowledge Retrieval Assistant Architecture](placeholder_for_architecture_diagram_2)

### Technology Stack-2

- **Backend**: Python 3.12, FastAPI
- **AI/ML**: GPT-4, LangChain, FAISS, Vertex AI
- **Storage**: Google Cloud Storage, Google Cloud SQL (PostgreSQL)
- **Functions**: Google Cloud Functions
- **Security**: Firebase Auth, GCP IAM
- **Frontend**: React with micro-frontend architecture
- **Methodology**: Agile

### Key Features-2

- **Semantic Search**: Finds contextually relevant information beyond keyword matching
- **Retrieval-Augmented Generation**: Combines retrieval with generative AI for accurate answers
- **Multi-language Support**: Processes and answers queries in multiple languages
- **Role-based Access**: Department and role-specific access controls
- **Automated Document Indexing**: Keeps information current through automation
- **Contextual Understanding**: Recognizes medical terminology and concepts
- **User-friendly Interface**: Intuitive micro-frontend design

### Workflow-2

1. **Document Ingestion**:
   - Medical documents uploaded to Google Cloud Storage
   - Cloud Functions trigger automatic processing
   - Text extraction and preprocessing

2. **Knowledge Indexing**:
   - Document chunking for efficient retrieval
   - Vector embedding generation using Vertex AI
   - FAISS index creation and maintenance
   - Metadata storage in Cloud SQL

3. **Query Processing**:
   - User submits question through frontend
   - Query preprocessing and embedding generation
   - Semantic search using FAISS index
   - Relevant document retrieval

4. **Answer Generation**:
   - Context compilation from retrieved documents
   - GPT-4 generates answers using LangChain RAG framework
   - Answer validation and formatting
   - Response delivery to frontend

5. **Continuous Learning**:
   - User feedback collection
   - Index optimization based on usage patterns
   - Regular retraining of embedding models

### Security & Compliance-2

- **Authentication**: Firebase Auth for user identity management
- **Authorization**: GCP IAM for fine-grained access control
- **Data Protection**: Encryption at rest and in transit
- **Access Logging**: Comprehensive audit trails
- **Compliance**: HIPAA-compliant infrastructure

### Monitoring & Performance-2

- **API Metrics**: Request volume, latency, error rates
- **Resource Utilization**: CPU, memory, storage monitoring
- **Cost Optimization**: Usage analysis for cost efficiency
- **Error Tracking**: Automated logging and alerting
- **User Analytics**: Usage patterns and common queries

### Deployment-2

- **Cloud-native**: Google Cloud Platform services
- **Scalability**: Cloud Run for automatic scaling
- **Isolation**: Separate development and production environments
- **Versioning**: API versioning for backward compatibility
- **Blue-Green Deployments**: Zero-downtime updates

## Getting Started

### Prerequisites

- AWS account with appropriate permissions (Project 1)
- Google Cloud Platform account with appropriate permissions (Project 2)
- Docker installed locally
- Python 3.12
- Node.js and npm

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/UHG/genai-projects.git
   cd genai-projects
   ```

2. Set up environment variables
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Build and run containers
   ```bash
   docker-compose up -d
   ```

4. Access the applications:
   - Clinical Report Summarization: http://localhost:3000
   - Medical Knowledge Retrieval: http://localhost:3001

## Development Guidelines

### Code Style

- Python: Follow PEP 8 guidelines
- JavaScript: Use ESLint with Airbnb preset
- Documentation: Use Google style docstrings

### Testing

- Unit tests: pytest for Python, Jest for JavaScript
- Integration tests: Postman collections
- Load testing: Locust scripts

### Branching Strategy

- `main`: Production-ready code
- `develop`: Integration branch
- `feature/*`: Feature development
- `hotfix/*`: Production fixes

## Contributing

1. Create a new feature branch from `develop`
2. Implement your changes with appropriate tests
3. Submit a pull request to `develop`
4. Ensure CI/CD pipeline passes
5. Request code review from team members