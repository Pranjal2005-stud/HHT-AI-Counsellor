from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uuid
import json
import os
import random
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
import tempfile

from state import ConversationState, ConversationStage
from state_controller import StateController
from engine import update_score, should_repeat

app = FastAPI(title="HHT AI Counsellor API", version="1.0.0")

# Vercel handler
handler = app

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store sessions
sessions = {}
controller = StateController()

@app.post("/start")
def start_conversation():
    session_id = str(uuid.uuid4())
    state = ConversationState()
    sessions[session_id] = state
    
    return {
        "session_id": session_id
    }

@app.post("/personal-info")
def submit_personal_info(request: dict):
    if request.get("session_id") in sessions:
        state = sessions[request["session_id"]]
        state.user_name = request.get("name")
        state.user_location = request.get("location")
        state.user_education = request.get("education")
    
    return {
        "message": "Thanks for the information!",
        "question": "Which tech domain interests you?"
    }

@app.post("/answer")
def submit_answer(request: dict):
    if request.get("session_id") not in sessions:
        return {"message": "Session not found"}
    
    state = sessions[request["session_id"]]
    
    # Valid domains
    valid_domains = ['backend', 'frontend', 'data analytics', 'machine learning', 'devops', 'cybersecurity', 'data engineering', 'algorithms']
    
    # If no domain selected yet, handle domain selection
    if not hasattr(state, 'selected_domain') or not state.selected_domain:
        user_domain = request["answer"].lower().strip()
        
        # Check if user input matches any valid domain
        matched_domain = None
        for domain in valid_domains:
            if domain in user_domain or user_domain in domain:
                matched_domain = domain
                break
        
        if matched_domain:
            state.selected_domain = matched_domain
            state.question_count = 0
            state.score = 0
            state.answers = []
            
            # Simple personalized response without AI
            user_name = getattr(state, 'user_name', 'there')
            personalized_msg = f"Excellent choice, {user_name}! Let's assess your {matched_domain} skills."
            
            return {
                "message": personalized_msg,
                "question": f"Do you have experience with {matched_domain} development?",
                "completed": False
            }
        else:
            return {
                "message": "Please select from the available domains only.",
                "question": "Which tech domain interests you most? Choose from: Backend, Frontend, Data Analytics, Machine Learning, DevOps, Cybersecurity, Data Engineering, or Algorithms.",
                "completed": False
            }
    
    # Initialize tracking if needed
    if not hasattr(state, 'question_count'):
        state.question_count = 0
        state.score = 0
        state.answers = []
    
    # Process current answer
    user_answer = request["answer"].lower().strip()
    is_yes = user_answer in ['yes', 'y', 'yeah', 'yep', 'sure', 'definitely']
    is_no = user_answer in ['no', 'n', 'nope', 'never', 'not really']
    
    # Questions and explanations for each domain (10 questions each, 6 will be randomly selected)
    domain_questions = {
        'frontend': [
            {"q": "Do you have experience with HTML5 semantic elements?", "exp": "HTML5 semantic elements like <header>, <nav>, <main>, <article>, and <section> provide meaning to web content structure. They improve accessibility, SEO, and code readability by clearly defining the purpose of different page sections."},
            {"q": "Have you worked with CSS Grid and Flexbox?", "exp": "CSS Grid and Flexbox are powerful layout systems. Grid is ideal for two-dimensional layouts (rows and columns), while Flexbox excels at one-dimensional layouts. Together, they enable responsive, flexible designs without floats or positioning hacks."},
            {"q": "Are you familiar with JavaScript ES6+ features?", "exp": "ES6+ features like arrow functions, destructuring, template literals, modules, and async/await modernize JavaScript development. They provide cleaner syntax, better performance, and improved code organization for building scalable applications."},
            {"q": "Do you understand responsive design principles?", "exp": "Responsive design ensures websites work seamlessly across all devices and screen sizes. It involves using flexible grid layouts, fluid images, and CSS media queries to adapt content presentation for optimal user experience on any device."},
            {"q": "Have you used React, Vue, or Angular frameworks?", "exp": "Modern JavaScript frameworks like React, Vue, and Angular provide component-based architecture for building interactive user interfaces. They offer state management, virtual DOM, and reusable components for scalable web applications."},
            {"q": "Are you familiar with CSS preprocessors like Sass or Less?", "exp": "CSS preprocessors extend CSS with programming features like variables, nesting, mixins, and functions. They help write more maintainable and organized stylesheets, especially for large-scale projects with complex styling requirements."},
            {"q": "Do you know about web performance optimization?", "exp": "Web performance optimization involves techniques like image compression, lazy loading, code splitting, minification, and CDN usage. These practices improve page load times, user experience, and search engine rankings."},
            {"q": "Have you worked with build tools like Webpack or Vite?", "exp": "Build tools automate development workflows by bundling, optimizing, and transforming code. Webpack handles complex configurations and asset management, while Vite provides faster development with instant hot module replacement."},
            {"q": "Are you experienced with version control using Git?", "exp": "Git is essential for tracking code changes, collaborating with teams, and managing project versions. Understanding branching, merging, and workflows like GitFlow enables effective collaboration and code management."},
            {"q": "Do you understand web accessibility (WCAG) guidelines?", "exp": "Web accessibility ensures websites are usable by people with disabilities. Following WCAG guidelines involves proper semantic HTML, keyboard navigation, screen reader compatibility, and inclusive design practices."}
        ],
        'backend': [
            {"q": "Do you have experience with server-side programming?", "exp": "Server-side programming involves creating applications that run on servers to handle business logic, database operations, and API endpoints. It's essential for building the infrastructure that powers web and mobile applications."},
            {"q": "Have you worked with relational databases like PostgreSQL or MySQL?", "exp": "Relational databases store structured data in tables with relationships. Understanding SQL queries, database design, indexing, and optimization is crucial for building scalable applications that handle data efficiently."},
            {"q": "Are you familiar with REST API design and development?", "exp": "REST APIs provide standardized ways for applications to communicate over HTTP. Understanding HTTP methods, status codes, resource naming, and API design principles enables building maintainable and scalable web services."},
            {"q": "Do you understand authentication and authorization systems?", "exp": "Authentication verifies user identity, while authorization determines access permissions. Implementing secure systems with JWT tokens, OAuth, password hashing, and session management protects applications from security threats."},
            {"q": "Have you used cloud platforms like AWS, Azure, or GCP?", "exp": "Cloud platforms provide scalable infrastructure and managed services for deploying applications. Understanding compute, storage, databases, and networking services enables building resilient, cost-effective solutions."},
            {"q": "Are you experienced with containerization using Docker?", "exp": "Docker containers package applications with their dependencies, ensuring consistent environments across development, testing, and production. Containerization improves deployment reliability and scalability."},
            {"q": "Do you know about microservices architecture?", "exp": "Microservices break applications into small, independent services that communicate via APIs. This architecture enables scalability, technology diversity, and fault isolation but requires careful design and orchestration."},
            {"q": "Have you implemented caching strategies?", "exp": "Caching improves application performance by storing frequently accessed data in memory. Understanding different caching levels (browser, CDN, application, database) and tools like Redis optimizes user experience."},
            {"q": "Are you familiar with message queues and event-driven systems?", "exp": "Message queues enable asynchronous communication between services, improving system resilience and scalability. Tools like RabbitMQ, Apache Kafka handle high-throughput, distributed messaging patterns."},
            {"q": "Do you understand database optimization and indexing?", "exp": "Database optimization involves query tuning, proper indexing, and schema design to improve performance. Understanding execution plans, index types, and normalization ensures efficient data retrieval at scale."}
        ],
        'data analytics': [
            {"q": "Do you have experience with statistical analysis?", "exp": "Statistical analysis involves collecting, analyzing, and interpreting data to discover patterns and insights. It includes descriptive statistics, hypothesis testing, and inferential statistics for data-driven decision making."},
            {"q": "Have you worked with SQL for data querying?", "exp": "SQL is fundamental for extracting and manipulating data from relational databases. Advanced SQL skills include complex joins, window functions, CTEs, and query optimization for efficient data analysis."},
            {"q": "Are you familiar with Python or R for data analysis?", "exp": "Python and R are powerful programming languages for data analysis. Python offers Pandas, NumPy, and Matplotlib, while R provides comprehensive statistical packages and excellent visualization capabilities."},
            {"q": "Do you understand data visualization principles?", "exp": "Effective data visualization communicates insights clearly through appropriate chart types, color schemes, and design principles. Understanding when to use bar charts, line graphs, heatmaps, and interactive dashboards is crucial."},
            {"q": "Have you used business intelligence tools like Tableau or Power BI?", "exp": "BI tools enable creating interactive dashboards and reports for stakeholders. They connect to various data sources and provide drag-and-drop interfaces for building compelling data visualizations."},
            {"q": "Are you experienced with data cleaning and preprocessing?", "exp": "Data cleaning involves handling missing values, removing duplicates, correcting inconsistencies, and standardizing formats. Quality data preprocessing is essential for accurate analysis and reliable insights."},
            {"q": "Do you know about A/B testing and experimental design?", "exp": "A/B testing compares two versions to determine which performs better. Understanding experimental design, statistical significance, and hypothesis testing enables making data-driven product and marketing decisions."},
            {"q": "Have you worked with time series analysis?", "exp": "Time series analysis examines data points collected over time to identify trends, seasonality, and patterns. It's essential for forecasting, financial analysis, and understanding temporal data relationships."},
            {"q": "Are you familiar with data warehousing concepts?", "exp": "Data warehouses centralize data from multiple sources for analysis and reporting. Understanding ETL processes, dimensional modeling, and OLAP systems enables building robust analytics infrastructure."},
            {"q": "Do you understand machine learning basics for analytics?", "exp": "Basic ML knowledge enhances analytics capabilities through predictive modeling, clustering, and classification. Understanding when and how to apply ML algorithms improves analytical insights and business value."}
        ],
        'machine learning': [
            {"q": "Do you have experience with supervised learning algorithms?", "exp": "Supervised learning uses labeled data to train models for prediction and classification. Understanding algorithms like linear regression, decision trees, and neural networks is fundamental for ML applications."},
            {"q": "Are you familiar with unsupervised learning techniques?", "exp": "Unsupervised learning finds patterns in unlabeled data through clustering, dimensionality reduction, and association rules. Techniques like K-means, PCA, and DBSCAN reveal hidden data structures."},
            {"q": "Have you worked with deep learning frameworks?", "exp": "Deep learning frameworks like TensorFlow and PyTorch enable building neural networks for complex tasks. Understanding layers, activation functions, and training processes is essential for modern AI applications."},
            {"q": "Do you understand feature engineering and selection?", "exp": "Feature engineering creates meaningful input variables from raw data, while feature selection identifies the most relevant features. These processes significantly impact model performance and interpretability."},
            {"q": "Are you experienced with model evaluation and validation?", "exp": "Proper model evaluation uses techniques like cross-validation, train-test splits, and appropriate metrics. Understanding overfitting, underfitting, and bias-variance tradeoffs ensures reliable model performance."},
            {"q": "Have you deployed machine learning models in production?", "exp": "Model deployment involves making trained models available for real-world use through APIs, batch processing, or embedded systems. Understanding MLOps practices ensures reliable, scalable ML systems."},
            {"q": "Do you know about natural language processing (NLP)?", "exp": "NLP enables computers to understand and process human language. Techniques include tokenization, sentiment analysis, named entity recognition, and transformer models for various text applications."},
            {"q": "Are you familiar with computer vision techniques?", "exp": "Computer vision processes and analyzes visual information using techniques like image classification, object detection, and segmentation. CNNs and transfer learning are key approaches for vision tasks."},
            {"q": "Have you worked with time series forecasting?", "exp": "Time series forecasting predicts future values based on historical data patterns. Methods include ARIMA, exponential smoothing, and neural networks for applications like demand forecasting and financial modeling."},
            {"q": "Do you understand reinforcement learning concepts?", "exp": "Reinforcement learning trains agents to make decisions through trial and error, receiving rewards or penalties. It's used in game AI, robotics, and optimization problems where agents learn optimal strategies."}
        ],
        'devops': [
            {"q": "Do you have experience with CI/CD pipeline implementation?", "exp": "CI/CD pipelines automate building, testing, and deploying code changes. They reduce manual errors, accelerate delivery, and ensure consistent deployment processes across environments."},
            {"q": "Are you familiar with containerization and orchestration?", "exp": "Containerization packages applications with dependencies, while orchestration manages container deployment, scaling, and networking. Docker and Kubernetes are essential tools for modern application deployment."},
            {"q": "Have you worked with infrastructure as code (IaC)?", "exp": "IaC manages infrastructure through code using tools like Terraform and CloudFormation. It enables version control, repeatability, and automated provisioning of cloud resources."},
            {"q": "Do you understand monitoring and observability?", "exp": "Monitoring tracks system health and performance, while observability provides insights into system behavior. Tools like Prometheus, Grafana, and ELK stack enable proactive issue detection and resolution."},
            {"q": "Are you experienced with cloud platform services?", "exp": "Cloud platforms offer managed services for compute, storage, networking, and databases. Understanding service selection, cost optimization, and security best practices is crucial for cloud adoption."},
            {"q": "Have you implemented automated testing strategies?", "exp": "Automated testing includes unit, integration, and end-to-end tests that run in CI/CD pipelines. It ensures code quality, reduces bugs, and enables confident deployments."},
            {"q": "Do you know about configuration management?", "exp": "Configuration management tools like Ansible, Chef, and Puppet automate system configuration and ensure consistency across environments. They reduce manual configuration errors and drift."},
            {"q": "Are you familiar with security practices in DevOps?", "exp": "DevSecOps integrates security throughout the development lifecycle. It includes vulnerability scanning, secrets management, compliance automation, and security testing in pipelines."},
            {"q": "Have you worked with service mesh technologies?", "exp": "Service mesh provides communication infrastructure for microservices, handling traffic management, security, and observability. Tools like Istio and Linkerd simplify complex service interactions."},
            {"q": "Do you understand disaster recovery and backup strategies?", "exp": "Disaster recovery ensures business continuity through backup systems, failover procedures, and recovery planning. Understanding RTO, RPO, and testing strategies minimizes downtime impact."}
        ],
        'cybersecurity': [
            {"q": "Do you have experience with network security fundamentals?", "exp": "Network security protects network infrastructure through firewalls, intrusion detection systems, VPNs, and network segmentation. Understanding protocols and attack vectors is essential for defense."},
            {"q": "Are you familiar with vulnerability assessment and penetration testing?", "exp": "Vulnerability assessments identify security weaknesses, while penetration testing simulates attacks to exploit them. These proactive approaches help organizations strengthen their security posture."},
            {"q": "Have you worked with security incident response?", "exp": "Incident response involves detecting, analyzing, containing, and recovering from security breaches. Proper procedures minimize damage and ensure lessons learned improve future security measures."},
            {"q": "Do you understand cryptography and encryption?", "exp": "Cryptography protects data through encryption algorithms, digital signatures, and key management. Understanding symmetric, asymmetric encryption, and hashing is fundamental for data security."},
            {"q": "Are you experienced with security compliance frameworks?", "exp": "Compliance frameworks like ISO 27001, NIST, and SOC 2 provide structured approaches to implementing security controls and meeting regulatory requirements for different industries."},
            {"q": "Have you implemented identity and access management (IAM)?", "exp": "IAM systems control user access to resources through authentication, authorization, and user lifecycle management. Proper IAM implementation prevents unauthorized access and data breaches."},
            {"q": "Do you know about threat intelligence and analysis?", "exp": "Threat intelligence involves collecting and analyzing information about current and emerging security threats. It helps organizations proactively defend against targeted attacks and vulnerabilities."},
            {"q": "Are you familiar with security awareness training?", "exp": "Security awareness training educates employees about cybersecurity threats and best practices. Human factors are often the weakest security link, making training programs critical for defense."},
            {"q": "Have you worked with security orchestration and automation?", "exp": "Security orchestration automates incident response and security operations through playbooks and workflows. It improves response times and consistency while reducing manual effort."},
            {"q": "Do you understand cloud security best practices?", "exp": "Cloud security involves shared responsibility models, proper configuration, identity management, and monitoring. Understanding cloud-specific threats and controls is essential for secure cloud adoption."}
        ],
        'data engineering': [
            {"q": "Do you have experience with ETL/ELT pipeline development?", "exp": "ETL/ELT pipelines extract, transform, and load data between systems. Understanding data flow design, error handling, and performance optimization is crucial for reliable data processing."},
            {"q": "Are you familiar with big data technologies?", "exp": "Big data technologies like Hadoop, Spark, and Kafka handle large-scale data processing and streaming. They enable processing datasets that exceed traditional database capabilities."},
            {"q": "Have you worked with data warehousing and modeling?", "exp": "Data warehouses centralize data for analytics using dimensional modeling techniques. Understanding star schemas, fact tables, and OLAP systems enables efficient analytical queries."},
            {"q": "Do you understand stream processing and real-time data?", "exp": "Stream processing handles continuous data flows for real-time analytics and decision-making. Technologies like Apache Kafka and Flink enable low-latency data processing at scale."},
            {"q": "Are you experienced with cloud data platforms?", "exp": "Cloud data platforms provide managed services for data storage, processing, and analytics. Understanding services like AWS Redshift, Google BigQuery, and Azure Synapse optimizes data solutions."},
            {"q": "Have you implemented data quality and governance?", "exp": "Data quality ensures accuracy, completeness, and consistency of data. Governance frameworks establish policies, procedures, and controls for data management and compliance."},
            {"q": "Do you know about data lake architecture?", "exp": "Data lakes store raw data in its native format, enabling flexible analytics and machine learning. Understanding storage formats, partitioning, and metadata management optimizes data lake performance."},
            {"q": "Are you familiar with workflow orchestration tools?", "exp": "Workflow orchestration tools like Apache Airflow and Prefect manage complex data pipeline dependencies, scheduling, and monitoring. They ensure reliable, scalable data processing workflows."},
            {"q": "Have you worked with NoSQL databases?", "exp": "NoSQL databases handle unstructured and semi-structured data using document, key-value, column-family, or graph models. Understanding when to use each type optimizes data storage and retrieval."},
            {"q": "Do you understand data security and privacy?", "exp": "Data security protects sensitive information through encryption, access controls, and compliance measures. Understanding regulations like GDPR and CCPA ensures proper data handling and privacy protection."}
        ],
        'algorithms': [
            {"q": "Do you have experience with fundamental data structures?", "exp": "Data structures like arrays, linked lists, stacks, queues, trees, and graphs organize data efficiently. Understanding their properties and use cases is essential for algorithm design and optimization."},
            {"q": "Are you familiar with sorting and searching algorithms?", "exp": "Sorting algorithms organize data, while searching algorithms find specific elements. Understanding their time complexities and trade-offs helps choose optimal approaches for different scenarios."},
            {"q": "Have you solved problems using dynamic programming?", "exp": "Dynamic programming solves complex problems by breaking them into simpler subproblems and storing solutions. It's essential for optimization problems with overlapping subproblems and optimal substructure."},
            {"q": "Do you understand graph algorithms and traversals?", "exp": "Graph algorithms solve problems involving networks and relationships. BFS, DFS, shortest path, and minimum spanning tree algorithms are fundamental for many real-world applications."},
            {"q": "Are you experienced with algorithmic complexity analysis?", "exp": "Complexity analysis evaluates algorithm efficiency using Big O notation. Understanding time and space complexity helps compare algorithms and predict performance at scale."},
            {"q": "Have you worked with greedy algorithms?", "exp": "Greedy algorithms make locally optimal choices at each step, hoping to find a global optimum. They're efficient for specific problem types but don't always guarantee optimal solutions."},
            {"q": "Do you know about divide and conquer strategies?", "exp": "Divide and conquer breaks problems into smaller subproblems, solves them recursively, and combines results. Examples include merge sort, quick sort, and binary search."},
            {"q": "Are you familiar with backtracking algorithms?", "exp": "Backtracking explores solution spaces by trying partial solutions and abandoning them if they can't lead to complete solutions. It's useful for constraint satisfaction and optimization problems."},
            {"q": "Have you participated in competitive programming?", "exp": "Competitive programming develops problem-solving skills through timed algorithmic challenges. It improves pattern recognition, coding speed, and ability to handle complex problems under pressure."},
            {"q": "Do you understand advanced tree algorithms?", "exp": "Advanced tree algorithms include balanced trees (AVL, Red-Black), segment trees, and trie structures. They enable efficient operations on hierarchical data and specialized query processing."}
        ]
    }
    
    # Get questions for current domain and randomly select 6 out of 10
    all_questions = domain_questions.get(state.selected_domain, [])
    if len(all_questions) >= 6:
        # Use session_id as seed for consistent question selection per session
        random.seed(hash(request["session_id"]) % (2**32))
        questions = random.sample(all_questions, 6)
        # Reset random seed
        random.seed()
    else:
        questions = all_questions
    
    current_question = questions[state.question_count]
    
    if is_yes:
        state.score += 1
        state.answers.append({"question": current_question["q"], "answer": "Yes", "explanation": None})
        state.question_count += 1
        
        if state.question_count >= 6:
            return _generate_detailed_results(state, questions)
        
        next_question = questions[state.question_count]
        return {
            "message": "Great!",
            "question": next_question["q"],
            "completed": False
        }
    
    elif is_no:
        state.answers.append({"question": current_question["q"], "answer": "No", "explanation": current_question["exp"]})
        state.question_count += 1
        
        if state.question_count >= 6:
            return _generate_detailed_results(state, questions)
        
        next_question = questions[state.question_count]
        return {
            "message": f"No worries! {current_question['exp']}",
            "question": next_question["q"],
            "completed": False
        }
    
    else:
        return {
            "message": "Please answer with 'yes' or 'no'.",
            "question": current_question["q"],
            "completed": False
        }

def _generate_detailed_results(state, questions):
    # Calculate level
    percentage = (state.score / 6) * 100
    if percentage >= 80:
        level = "Advanced"
        level_desc = "You have strong expertise in this domain with comprehensive knowledge across multiple areas."
    elif percentage >= 50:
        level = "Intermediate"
        level_desc = "You have solid foundational knowledge with room to grow in some areas."
    else:
        level = "Beginner"
        level_desc = "You're starting your journey in this domain. Focus on building fundamental skills."
    
    # Areas to improve (questions answered 'No')
    areas_to_improve = []
    for ans in state.answers:
        if ans["answer"] == "No":
            areas_to_improve.append({
                "question": ans["question"],
                "answer": ans["answer"],
                "explanation": ans["explanation"]
            })
    
    # Domain-specific recommendations
    domain_recommendations = {
        'frontend': {
            'topics': ['HTML5 Semantic Elements & Accessibility', 'CSS Grid & Flexbox Mastery', 'Modern JavaScript (ES6+)', 'React Hooks & State Management', 'Web Performance Optimization', 'Progressive Web Apps (PWA)'],
            'projects': ['Interactive Portfolio with Animations', 'E-commerce Product Catalog with Filters', 'Real-time Chat Application UI', 'Responsive Dashboard with Charts', 'Weather App with Geolocation', 'Task Management App with Drag & Drop']
        },
        'backend': {
            'topics': ['RESTful API Design Patterns', 'Database Optimization & Indexing', 'Authentication & JWT Security', 'Microservices Architecture', 'Cloud Deployment & DevOps', 'API Rate Limiting & Caching'],
            'projects': ['User Authentication System with JWT', 'RESTful API with Database Integration', 'File Upload & Processing Service', 'Real-time Notification System', 'Payment Gateway Integration', 'Microservices with Docker & Kubernetes']
        },
        'data analytics': {
            'topics': ['Advanced SQL & Query Optimization', 'Statistical Analysis & Hypothesis Testing', 'Data Visualization Best Practices', 'Python/R for Data Science', 'Business Intelligence Tools', 'A/B Testing & Experimentation'],
            'projects': ['Sales Performance Dashboard', 'Customer Segmentation Analysis', 'Predictive Analytics Model', 'Real-time Business Metrics', 'Market Research Analysis', 'Financial Forecasting System']
        },
        'machine learning': {
            'topics': ['Supervised & Unsupervised Learning', 'Feature Engineering & Selection', 'Model Evaluation & Validation', 'Deep Learning with Neural Networks', 'MLOps & Model Deployment', 'Natural Language Processing'],
            'projects': ['Image Classification System', 'Recommendation Engine', 'Fraud Detection Model', 'Sentiment Analysis Tool', 'Time Series Forecasting', 'Chatbot with NLP']
        },
        'devops': {
            'topics': ['Container Orchestration with Kubernetes', 'Infrastructure as Code (Terraform)', 'CI/CD Pipeline Automation', 'Cloud Security & Compliance', 'Monitoring & Observability', 'Site Reliability Engineering'],
            'projects': ['Automated Deployment Pipeline', 'Multi-Environment Infrastructure', 'Container Orchestration Platform', 'Monitoring & Alerting System', 'Disaster Recovery Setup', 'Security Compliance Automation']
        },
        'cybersecurity': {
            'topics': ['Penetration Testing & Ethical Hacking', 'Security Incident Response', 'Network Security & Firewalls', 'Compliance Frameworks (ISO 27001)', 'Threat Intelligence & Analysis', 'Security Awareness Training'],
            'projects': ['Vulnerability Assessment Tool', 'Security Monitoring Dashboard', 'Incident Response Playbook', 'Network Security Audit', 'Phishing Simulation Platform', 'Compliance Reporting System']
        },
        'data engineering': {
            'topics': ['Big Data Processing (Spark/Hadoop)', 'Real-time Stream Processing', 'Data Pipeline Orchestration', 'Cloud Data Platforms', 'Data Quality & Governance', 'ETL/ELT Best Practices'],
            'projects': ['Real-time Data Pipeline', 'Data Lake Architecture', 'ETL Automation System', 'Stream Processing Platform', 'Data Quality Monitoring', 'Multi-source Data Integration']
        },
        'algorithms': {
            'topics': ['Advanced Data Structures', 'Dynamic Programming Techniques', 'Graph Algorithms & Applications', 'Complexity Analysis & Optimization', 'Competitive Programming Strategies', 'System Design Fundamentals'],
            'projects': ['Algorithm Visualization Tool', 'Coding Interview Prep Platform', 'Graph Analysis System', 'Optimization Problem Solver', 'Data Structure Library', 'Performance Benchmarking Tool']
        }
    }
    
    recommendations = domain_recommendations.get(state.selected_domain, {
        'topics': [f'{state.selected_domain} Fundamentals', 'Best Practices', 'Project Development', 'Testing', 'Deployment'],
        'projects': [f'Basic {state.selected_domain} Project', f'Intermediate {state.selected_domain} App', f'Advanced {state.selected_domain} System']
    })
    
    return {
        "message": "Assessment completed!",
        "question": None,
        "completed": True,
        "recommendations": {
            "level": level,
            "domain": state.selected_domain.title(),
            "score": f"{state.score}/6",
            "percentage": f"{percentage:.0f}%",
            "level_description": level_desc,
            "areas_to_improve": areas_to_improve,
            "topics": recommendations['topics'],
            "projects": recommendations['projects'],
            "explanation": f"Based on your {state.selected_domain} assessment, you scored {state.score} out of 6 questions correctly ({percentage:.0f}%). {level_desc} Focus on the recommended topics and try building the suggested projects to enhance your skills."
        }
    }

@app.post("/detailed-roadmap")
def get_detailed_roadmap(request: dict):
    # Get domain from request or session
    domain = request.get("domain")
    
    # If no domain in request, get from session
    if not domain and request.get("session_id") in sessions:
        state = sessions[request["session_id"]]
        domain = getattr(state, 'selected_domain', 'frontend')
    
    # Default to frontend if still no domain
    if not domain:
        domain = 'frontend'
    
    domain = domain.lower()
    
    detailed_roadmaps = {
        'frontend': {
            'title': 'Frontend Development Roadmap',
            'description': 'Complete guide to becoming a proficient frontend developer',
            'prerequisites': 'Basic computer knowledge, understanding of how websites work',
            'duration': '6-8 months with consistent practice',
            'steps': [
                {
                    'step': 1,
                    'title': 'Web Fundamentals 🌐',
                    'duration': '4-6 weeks',
                    'topics': [
                        'HTML5 semantic elements and structure',
                        'CSS3 fundamentals and box model',
                        'Responsive design with Flexbox and Grid',
                        'Basic JavaScript and DOM manipulation',
                        'Browser developer tools'
                    ],
                    'resources': [
                        {'title': 'MDN Web Docs', 'url': 'https://developer.mozilla.org/en-US/'},
                        {'title': 'freeCodeCamp HTML/CSS', 'url': 'https://www.freecodecamp.org/learn/responsive-web-design/'},
                        {'title': 'CSS-Tricks Flexbox Guide', 'url': 'https://css-tricks.com/snippets/css/a-guide-to-flexbox/'}
                    ],
                    'projects': ['Personal portfolio website', 'Responsive landing page', 'CSS Grid layout showcase']
                },
                {
                    'step': 2,
                    'title': 'JavaScript Mastery 📜',
                    'duration': '6-8 weeks',
                    'topics': [
                        'ES6+ features (arrow functions, destructuring, modules)',
                        'Asynchronous JavaScript (Promises, async/await)',
                        'Fetch API and working with APIs',
                        'Local storage and session storage',
                        'Error handling and debugging'
                    ],
                    'resources': [
                        {'title': 'JavaScript.info', 'url': 'https://javascript.info/'},
                        {'title': 'Eloquent JavaScript', 'url': 'https://eloquentjavascript.net/'},
                        {'title': 'You Don\'t Know JS', 'url': 'https://github.com/getify/You-Dont-Know-JS'}
                    ],
                    'projects': ['Weather app with API', 'Todo list with local storage', 'Interactive quiz application']
                },
                {
                    'step': 3,
                    'title': 'Modern Frontend Framework 🚀',
                    'duration': '8-10 weeks',
                    'topics': [
                        'React fundamentals (components, props, state)',
                        'React Hooks and functional components',
                        'State management (Context API, Redux)',
                        'React Router for navigation',
                        'Component lifecycle and effects'
                    ],
                    'resources': [
                        {'title': 'React Official Docs', 'url': 'https://react.dev/'},
                        {'title': 'React Tutorial', 'url': 'https://react.dev/learn/tutorial-tic-tac-toe'},
                        {'title': 'Redux Toolkit', 'url': 'https://redux-toolkit.js.org/'}
                    ],
                    'projects': ['E-commerce product catalog', 'Social media dashboard', 'Real-time chat application']
                },
                {
                    'step': 4,
                    'title': 'Build Tools & Optimization ⚡',
                    'duration': '3-4 weeks',
                    'topics': [
                        'Package managers (npm, yarn)',
                        'Build tools (Webpack, Vite)',
                        'CSS preprocessors (Sass, Less)',
                        'Code formatting (Prettier, ESLint)',
                        'Performance optimization techniques'
                    ],
                    'resources': [
                        {'title': 'Webpack Documentation', 'url': 'https://webpack.js.org/'},
                        {'title': 'Vite Guide', 'url': 'https://vitejs.dev/guide/'},
                        {'title': 'Sass Documentation', 'url': 'https://sass-lang.com/documentation'}
                    ],
                    'projects': ['Optimized portfolio with build pipeline', 'Multi-page application with routing']
                },
                {
                    'step': 5,
                    'title': 'Testing & Deployment 🧪',
                    'duration': '4-5 weeks',
                    'topics': [
                        'Unit testing with Jest',
                        'Component testing with React Testing Library',
                        'End-to-end testing with Cypress',
                        'Git version control',
                        'Deployment (Netlify, Vercel, GitHub Pages)'
                    ],
                    'resources': [
                        {'title': 'Jest Documentation', 'url': 'https://jestjs.io/docs/getting-started'},
                        {'title': 'React Testing Library', 'url': 'https://testing-library.com/docs/react-testing-library/intro/'},
                        {'title': 'Cypress Documentation', 'url': 'https://docs.cypress.io/'}
                    ],
                    'projects': ['Fully tested application', 'CI/CD pipeline setup', 'Production deployment']
                },
                {
                    'step': 6,
                    'title': 'Advanced Topics & Specialization 🎯',
                    'duration': '6-8 weeks',
                    'topics': [
                        'Progressive Web Apps (PWA)',
                        'Server-Side Rendering (Next.js)',
                        'TypeScript for type safety',
                        'Advanced state management',
                        'Micro-frontends architecture'
                    ],
                    'resources': [
                        {'title': 'Next.js Documentation', 'url': 'https://nextjs.org/docs'},
                        {'title': 'TypeScript Handbook', 'url': 'https://www.typescriptlang.org/docs/'},
                        {'title': 'PWA Guide', 'url': 'https://web.dev/progressive-web-apps/'}
                    ],
                    'projects': ['PWA with offline functionality', 'SSR application with Next.js', 'TypeScript migration project']
                }
            ],
            'career_paths': [
                'Frontend Developer',
                'React Developer',
                'UI/UX Developer',
                'Full-Stack Developer',
                'Frontend Architect'
            ],
            'tips': [
                'Build projects consistently to reinforce learning',
                'Join frontend communities and contribute to open source',
                'Stay updated with latest web standards and frameworks',
                'Focus on user experience and accessibility',
                'Practice responsive design for all screen sizes'
            ]
        },
        'backend': {
            'title': 'Backend Development Roadmap',
            'description': 'Complete guide to becoming a skilled backend developer',
            'prerequisites': 'Basic programming knowledge, understanding of web concepts',
            'duration': '6-8 months with consistent practice',
            'steps': [
                {
                    'step': 1,
                    'title': 'Server Fundamentals 🖥️',
                    'duration': '4-6 weeks',
                    'topics': [
                        'HTTP protocols and REST principles',
                        'Server-side programming basics',
                        'API design and development',
                        'Request/response cycle',
                        'Status codes and error handling'
                    ],
                    'resources': [
                        {'title': 'FastAPI Documentation', 'url': 'https://fastapi.tiangolo.com/'},
                        {'title': 'Node.js Documentation', 'url': 'https://nodejs.org/en/docs/'},
                        {'title': 'REST API Tutorial', 'url': 'https://restfulapi.net/'}
                    ],
                    'projects': ['Simple REST API', 'CRUD operations server', 'Basic HTTP server']
                },
                {
                    'step': 2,
                    'title': 'Database Integration 🗄️',
                    'duration': '6-8 weeks',
                    'topics': [
                        'SQL fundamentals and advanced queries',
                        'Database design and normalization',
                        'ORM/ODM usage and best practices',
                        'Connection pooling and optimization',
                        'Database migrations and versioning'
                    ],
                    'resources': [
                        {'title': 'PostgreSQL Documentation', 'url': 'https://www.postgresql.org/docs/'},
                        {'title': 'SQLAlchemy Tutorial', 'url': 'https://docs.sqlalchemy.org/en/14/tutorial/'},
                        {'title': 'MongoDB University', 'url': 'https://university.mongodb.com/'}
                    ],
                    'projects': ['User management system', 'E-commerce database', 'Blog with comments system']
                },
                {
                    'step': 3,
                    'title': 'Authentication & Security 🔐',
                    'duration': '4-5 weeks',
                    'topics': [
                        'User authentication systems',
                        'JWT tokens and session management',
                        'Password hashing and validation',
                        'OAuth and third-party authentication',
                        'API security best practices'
                    ],
                    'resources': [
                        {'title': 'Auth0 Documentation', 'url': 'https://auth0.com/docs'},
                        {'title': 'JWT.io', 'url': 'https://jwt.io/introduction'},
                        {'title': 'OWASP Security Guide', 'url': 'https://owasp.org/www-project-api-security/'}
                    ],
                    'projects': ['JWT authentication API', 'OAuth integration', 'Role-based access control']
                },
                {
                    'step': 4,
                    'title': 'Advanced Backend Features 🚀',
                    'duration': '6-7 weeks',
                    'topics': [
                        'File uploads and processing',
                        'Email services and notifications',
                        'Caching strategies (Redis)',
                        'Background jobs and queues',
                        'API documentation and testing'
                    ],
                    'resources': [
                        {'title': 'Redis Documentation', 'url': 'https://redis.io/documentation'},
                        {'title': 'Celery Documentation', 'url': 'https://docs.celeryproject.org/'},
                        {'title': 'Swagger/OpenAPI', 'url': 'https://swagger.io/docs/'}
                    ],
                    'projects': ['File upload service', 'Email notification system', 'Background job processor']
                },
                {
                    'step': 5,
                    'title': 'Cloud & Deployment ☁️',
                    'duration': '5-6 weeks',
                    'topics': [
                        'Cloud platforms (AWS, Azure, GCP)',
                        'Containerization with Docker',
                        'Environment configuration',
                        'CI/CD pipelines',
                        'Monitoring and logging'
                    ],
                    'resources': [
                        {'title': 'AWS Documentation', 'url': 'https://docs.aws.amazon.com/'},
                        {'title': 'Docker Documentation', 'url': 'https://docs.docker.com/'},
                        {'title': 'GitHub Actions', 'url': 'https://docs.github.com/en/actions'}
                    ],
                    'projects': ['Dockerized application', 'AWS deployment', 'CI/CD pipeline setup']
                },
                {
                    'step': 6,
                    'title': 'Scalability & Architecture 📈',
                    'duration': '6-8 weeks',
                    'topics': [
                        'Microservices architecture',
                        'Load balancing and scaling',
                        'Message queues and event systems',
                        'Database optimization',
                        'System design principles'
                    ],
                    'resources': [
                        {'title': 'Microservices Patterns', 'url': 'https://microservices.io/patterns/'},
                        {'title': 'Apache Kafka', 'url': 'https://kafka.apache.org/documentation/'},
                        {'title': 'System Design Primer', 'url': 'https://github.com/donnemartin/system-design-primer'}
                    ],
                    'projects': ['Microservices system', 'Message queue implementation', 'Scalable API design']
                }
            ],
            'career_paths': [
                'Backend Developer',
                'Full-Stack Developer',
                'DevOps Engineer',
                'System Architect',
                'API Developer'
            ],
            'tips': [
                'Focus on understanding system design principles',
                'Practice building scalable and maintainable code',
                'Learn about database optimization and caching',
                'Stay updated with cloud technologies',
                'Understand security best practices'
            ]
        },
        'data analytics': {
            'title': 'Data Analytics Roadmap',
            'description': 'Complete guide to becoming a proficient data analyst',
            'prerequisites': 'Basic mathematics and statistics knowledge',
            'duration': '5-7 months with consistent practice',
            'steps': [
                {
                    'step': 1,
                    'title': 'Data Foundations 📊',
                    'duration': '3-4 weeks',
                    'topics': [
                        'Statistics fundamentals',
                        'Data types and structures',
                        'Excel/Google Sheets mastery',
                        'Basic data visualization principles',
                        'Data collection methods'
                    ],
                    'resources': [
                        {'title': 'Khan Academy Statistics', 'url': 'https://www.khanacademy.org/math/statistics-probability'},
                        {'title': 'Excel Tutorial', 'url': 'https://support.microsoft.com/en-us/office/excel-help-center'},
                        {'title': 'Data Visualization Guide', 'url': 'https://www.tableau.com/learn/articles/data-visualization'}
                    ],
                    'projects': ['Sales data analysis in Excel', 'Statistical analysis report', 'Basic charts and graphs']
                },
                {
                    'step': 2,
                    'title': 'SQL Mastery 🗃️',
                    'duration': '4-5 weeks',
                    'topics': [
                        'SQL fundamentals and syntax',
                        'Complex joins and subqueries',
                        'Window functions and CTEs',
                        'Data aggregation and grouping',
                        'Query optimization techniques'
                    ],
                    'resources': [
                        {'title': 'W3Schools SQL', 'url': 'https://www.w3schools.com/sql/'},
                        {'title': 'SQLBolt Interactive Tutorial', 'url': 'https://sqlbolt.com/'},
                        {'title': 'PostgreSQL Tutorial', 'url': 'https://www.postgresqltutorial.com/'}
                    ],
                    'projects': ['Database analysis project', 'Complex query challenges', 'Data extraction pipeline']
                },
                {
                    'step': 3,
                    'title': 'Python for Data Analysis 🐍',
                    'duration': '6-8 weeks',
                    'topics': [
                        'Python basics and data structures',
                        'Pandas for data manipulation',
                        'NumPy for numerical computing',
                        'Data cleaning and preprocessing',
                        'Jupyter notebook workflows'
                    ],
                    'resources': [
                        {'title': 'Pandas Documentation', 'url': 'https://pandas.pydata.org/docs/'},
                        {'title': 'Python for Data Analysis Book', 'url': 'https://wesmckinney.com/book/'},
                        {'title': 'Kaggle Learn Python', 'url': 'https://www.kaggle.com/learn/python'}
                    ],
                    'projects': ['Data cleaning project', 'Exploratory data analysis', 'Automated reporting script']
                },
                {
                    'step': 4,
                    'title': 'Data Visualization 📈',
                    'duration': '4-5 weeks',
                    'topics': [
                        'Matplotlib and Seaborn',
                        'Interactive visualizations',
                        'Dashboard design principles',
                        'Storytelling with data',
                        'Color theory and accessibility'
                    ],
                    'resources': [
                        {'title': 'Matplotlib Documentation', 'url': 'https://matplotlib.org/stable/contents.html'},
                        {'title': 'Seaborn Tutorial', 'url': 'https://seaborn.pydata.org/tutorial.html'},
                        {'title': 'Plotly Documentation', 'url': 'https://plotly.com/python/'}
                    ],
                    'projects': ['Interactive dashboard', 'Data story presentation', 'Visualization library']
                },
                {
                    'step': 5,
                    'title': 'Business Intelligence Tools 💼',
                    'duration': '5-6 weeks',
                    'topics': [
                        'Tableau fundamentals',
                        'Power BI development',
                        'Dashboard best practices',
                        'KPI identification and tracking',
                        'Report automation'
                    ],
                    'resources': [
                        {'title': 'Tableau Learning', 'url': 'https://www.tableau.com/learn'},
                        {'title': 'Power BI Documentation', 'url': 'https://docs.microsoft.com/en-us/power-bi/'},
                        {'title': 'BI Best Practices', 'url': 'https://www.sisense.com/blog/business-intelligence-best-practices/'}
                    ],
                    'projects': ['Executive dashboard', 'Sales performance tracker', 'Automated reporting system']
                },
                {
                    'step': 6,
                    'title': 'Advanced Analytics 🎯',
                    'duration': '6-7 weeks',
                    'topics': [
                        'Statistical hypothesis testing',
                        'A/B testing and experimentation',
                        'Predictive analytics basics',
                        'Time series analysis',
                        'Machine learning for analysts'
                    ],
                    'resources': [
                        {'title': 'Statistical Methods', 'url': 'https://www.statmethods.net/'},
                        {'title': 'A/B Testing Guide', 'url': 'https://blog.hubspot.com/marketing/how-to-do-a-b-testing'},
                        {'title': 'Scikit-learn', 'url': 'https://scikit-learn.org/stable/user_guide.html'}
                    ],
                    'projects': ['A/B test analysis', 'Forecasting model', 'Customer segmentation']
                }
            ],
            'career_paths': [
                'Data Analyst',
                'Business Analyst',
                'Marketing Analyst',
                'Financial Analyst',
                'Data Scientist'
            ],
            'tips': [
                'Focus on understanding business context',
                'Practice storytelling with data',
                'Learn to ask the right questions',
                'Master data cleaning and validation',
                'Stay curious and keep learning new tools'
            ]
        },
        'machine learning': {
            'title': 'Machine Learning Roadmap',
            'description': 'Complete guide to becoming a machine learning engineer',
            'prerequisites': 'Programming knowledge, basic mathematics and statistics',
            'duration': '8-12 months with consistent practice',
            'steps': [
                {
                    'step': 1,
                    'title': 'ML Fundamentals 🤖',
                    'duration': '4-6 weeks',
                    'topics': [
                        'Machine learning concepts and types',
                        'Python for ML (NumPy, Pandas)',
                        'Data preprocessing and cleaning',
                        'Basic statistics and probability',
                        'Linear algebra essentials'
                    ],
                    'resources': [
                        {'title': 'Scikit-learn Documentation', 'url': 'https://scikit-learn.org/stable/'},
                        {'title': 'Andrew Ng ML Course', 'url': 'https://www.coursera.org/learn/machine-learning'},
                        {'title': 'Python Machine Learning Book', 'url': 'https://sebastianraschka.com/books.html'}
                    ],
                    'projects': ['Iris classification', 'House price prediction', 'Data exploration notebook']
                },
                {
                    'step': 2,
                    'title': 'Supervised Learning 📚',
                    'duration': '6-8 weeks',
                    'topics': [
                        'Linear and logistic regression',
                        'Decision trees and random forests',
                        'Support vector machines',
                        'Model evaluation metrics',
                        'Cross-validation techniques'
                    ],
                    'resources': [
                        {'title': 'Hands-On ML Book', 'url': 'https://www.oreilly.com/library/view/hands-on-machine-learning/9781492032632/'},
                        {'title': 'ML Algorithms Explained', 'url': 'https://towardsdatascience.com/machine-learning-algorithms-explained-8d20f8f1b9f0'},
                        {'title': 'Kaggle Learn ML', 'url': 'https://www.kaggle.com/learn/intro-to-machine-learning'}
                    ],
                    'projects': ['Customer churn prediction', 'Credit risk assessment', 'Medical diagnosis classifier']
                },
                {
                    'step': 3,
                    'title': 'Unsupervised Learning 🔍',
                    'duration': '4-5 weeks',
                    'topics': [
                        'Clustering algorithms (K-means, DBSCAN)',
                        'Dimensionality reduction (PCA, t-SNE)',
                        'Association rules and market basket analysis',
                        'Anomaly detection techniques',
                        'Feature selection methods'
                    ],
                    'resources': [
                        {'title': 'Unsupervised Learning Guide', 'url': 'https://scikit-learn.org/stable/unsupervised_learning.html'},
                        {'title': 'Clustering Algorithms', 'url': 'https://towardsdatascience.com/the-5-clustering-algorithms-data-scientists-need-to-know-a36d136ef68'},
                        {'title': 'PCA Explained', 'url': 'https://builtin.com/data-science/step-step-explanation-principal-component-analysis'}
                    ],
                    'projects': ['Customer segmentation', 'Recommendation system', 'Fraud detection model']
                },
                {
                    'step': 4,
                    'title': 'Deep Learning 🧠',
                    'duration': '8-10 weeks',
                    'topics': [
                        'Neural network fundamentals',
                        'TensorFlow and PyTorch basics',
                        'Convolutional Neural Networks (CNN)',
                        'Recurrent Neural Networks (RNN)',
                        'Transfer learning and fine-tuning'
                    ],
                    'resources': [
                        {'title': 'TensorFlow Documentation', 'url': 'https://www.tensorflow.org/learn'},
                        {'title': 'PyTorch Tutorials', 'url': 'https://pytorch.org/tutorials/'},
                        {'title': 'Deep Learning Specialization', 'url': 'https://www.coursera.org/specializations/deep-learning'}
                    ],
                    'projects': ['Image classification CNN', 'Text sentiment analysis', 'Time series forecasting']
                },
                {
                    'step': 5,
                    'title': 'MLOps & Deployment 🚀',
                    'duration': '5-6 weeks',
                    'topics': [
                        'Model versioning and tracking',
                        'Model deployment strategies',
                        'API development for ML models',
                        'Monitoring and maintenance',
                        'A/B testing for ML systems'
                    ],
                    'resources': [
                        {'title': 'MLflow Documentation', 'url': 'https://mlflow.org/docs/latest/index.html'},
                        {'title': 'Docker for ML', 'url': 'https://docs.docker.com/'},
                        {'title': 'FastAPI for ML', 'url': 'https://fastapi.tiangolo.com/'}
                    ],
                    'projects': ['ML API service', 'Model monitoring dashboard', 'Automated ML pipeline']
                },
                {
                    'step': 6,
                    'title': 'Specialized Applications 🎯',
                    'duration': '6-8 weeks',
                    'topics': [
                        'Natural Language Processing',
                        'Computer Vision applications',
                        'Reinforcement Learning basics',
                        'Time series forecasting',
                        'Ensemble methods and stacking'
                    ],
                    'resources': [
                        {'title': 'Hugging Face Transformers', 'url': 'https://huggingface.co/docs/transformers/index'},
                        {'title': 'OpenCV Documentation', 'url': 'https://docs.opencv.org/'},
                        {'title': 'OpenAI Gym', 'url': 'https://gym.openai.com/docs/'}
                    ],
                    'projects': ['Chatbot with NLP', 'Object detection system', 'Stock price predictor']
                }
            ],
            'career_paths': [
                'Machine Learning Engineer',
                'Data Scientist',
                'AI Research Scientist',
                'MLOps Engineer',
                'Computer Vision Engineer'
            ],
            'tips': [
                'Focus on understanding concepts, not just using libraries',
                'Implement algorithms from scratch to deepen understanding',
                'Stay updated with latest research and papers',
                'Build a strong portfolio with diverse projects',
                'Practice explaining complex concepts simply'
            ]
        },
        'devops': {
            'title': 'DevOps Engineering Roadmap',
            'description': 'Complete guide to becoming a DevOps engineer',
            'prerequisites': 'Basic programming and system administration knowledge',
            'duration': '6-9 months with consistent practice',
            'steps': [
                {
                    'step': 1,
                    'title': 'Foundation & Version Control 🏗️',
                    'duration': '3-4 weeks',
                    'topics': [
                        'Linux system administration',
                        'Git advanced workflows',
                        'Shell scripting and automation',
                        'Network fundamentals',
                        'Security basics'
                    ],
                    'resources': [
                        {'title': 'Linux Command Line', 'url': 'https://linuxcommand.org/'},
                        {'title': 'Git Documentation', 'url': 'https://git-scm.com/doc'},
                        {'title': 'Bash Scripting Guide', 'url': 'https://tldp.org/LDP/Bash-Beginners-Guide/html/'}
                    ],
                    'projects': ['Automated backup script', 'Git workflow setup', 'System monitoring script']
                },
                {
                    'step': 2,
                    'title': 'Containerization 🐳',
                    'duration': '4-5 weeks',
                    'topics': [
                        'Docker fundamentals',
                        'Container orchestration',
                        'Kubernetes basics',
                        'Multi-stage builds',
                        'Container security'
                    ],
                    'resources': [
                        {'title': 'Docker Documentation', 'url': 'https://docs.docker.com/'},
                        {'title': 'Kubernetes Documentation', 'url': 'https://kubernetes.io/docs/home/'},
                        {'title': 'Docker Best Practices', 'url': 'https://docs.docker.com/develop/dev-best-practices/'}
                    ],
                    'projects': ['Dockerized web application', 'Kubernetes cluster setup', 'Container registry']
                },
                {
                    'step': 3,
                    'title': 'CI/CD Pipelines ⚙️',
                    'duration': '5-6 weeks',
                    'topics': [
                        'Continuous Integration concepts',
                        'GitHub Actions and GitLab CI',
                        'Jenkins pipeline development',
                        'Automated testing integration',
                        'Deployment strategies'
                    ],
                    'resources': [
                        {'title': 'GitHub Actions', 'url': 'https://docs.github.com/en/actions'},
                        {'title': 'Jenkins Documentation', 'url': 'https://www.jenkins.io/doc/'},
                        {'title': 'GitLab CI/CD', 'url': 'https://docs.gitlab.com/ee/ci/'}
                    ],
                    'projects': ['Automated deployment pipeline', 'Multi-environment CI/CD', 'Testing automation']
                },
                {
                    'step': 4,
                    'title': 'Infrastructure as Code 🏗️',
                    'duration': '5-6 weeks',
                    'topics': [
                        'Terraform fundamentals',
                        'CloudFormation templates',
                        'Ansible automation',
                        'Infrastructure versioning',
                        'State management'
                    ],
                    'resources': [
                        {'title': 'Terraform Documentation', 'url': 'https://www.terraform.io/docs'},
                        {'title': 'Ansible Documentation', 'url': 'https://docs.ansible.com/'},
                        {'title': 'AWS CloudFormation', 'url': 'https://docs.aws.amazon.com/cloudformation/'}
                    ],
                    'projects': ['Cloud infrastructure automation', 'Multi-cloud deployment', 'Configuration management']
                },
                {
                    'step': 5,
                    'title': 'Monitoring & Observability 📊',
                    'duration': '4-5 weeks',
                    'topics': [
                        'Prometheus and Grafana',
                        'ELK Stack (Elasticsearch, Logstash, Kibana)',
                        'Application performance monitoring',
                        'Alerting and incident response',
                        'Distributed tracing'
                    ],
                    'resources': [
                        {'title': 'Prometheus Documentation', 'url': 'https://prometheus.io/docs/'},
                        {'title': 'Grafana Documentation', 'url': 'https://grafana.com/docs/'},
                        {'title': 'Elastic Stack', 'url': 'https://www.elastic.co/guide/index.html'}
                    ],
                    'projects': ['Monitoring dashboard', 'Log aggregation system', 'Alerting setup']
                },
                {
                    'step': 6,
                    'title': 'Cloud & Security 🔒',
                    'duration': '6-7 weeks',
                    'topics': [
                        'AWS/Azure/GCP services',
                        'Cloud security best practices',
                        'Secrets management',
                        'Compliance and governance',
                        'Disaster recovery planning'
                    ],
                    'resources': [
                        {'title': 'AWS Documentation', 'url': 'https://docs.aws.amazon.com/'},
                        {'title': 'Azure Documentation', 'url': 'https://docs.microsoft.com/en-us/azure/'},
                        {'title': 'Cloud Security Alliance', 'url': 'https://cloudsecurityalliance.org/'}
                    ],
                    'projects': ['Secure cloud architecture', 'Backup and recovery system', 'Compliance automation']
                }
            ],
            'career_paths': [
                'DevOps Engineer',
                'Site Reliability Engineer',
                'Cloud Engineer',
                'Platform Engineer',
                'Infrastructure Engineer'
            ],
            'tips': [
                'Automate everything you can',
                'Focus on reliability and scalability',
                'Learn multiple cloud platforms',
                'Practice incident response scenarios',
                'Stay updated with security best practices'
            ]
        },
        'cybersecurity': {
            'title': 'Cybersecurity Roadmap',
            'description': 'Complete guide to becoming a cybersecurity professional',
            'prerequisites': 'Basic networking and system administration knowledge',
            'duration': '8-12 months with consistent practice',
            'steps': [
                {
                    'step': 1,
                    'title': 'Security Fundamentals 🛡️',
                    'duration': '4-6 weeks',
                    'topics': [
                        'Information security principles',
                        'Network security basics',
                        'Operating system security',
                        'Risk assessment fundamentals',
                        'Security frameworks overview'
                    ],
                    'resources': [
                        {'title': 'NIST Cybersecurity Framework', 'url': 'https://www.nist.gov/cyberframework'},
                        {'title': 'OWASP Foundation', 'url': 'https://owasp.org/'},
                        {'title': 'CompTIA Security+', 'url': 'https://www.comptia.org/certifications/security'}
                    ],
                    'projects': ['Security policy document', 'Risk assessment report', 'Network security audit']
                },
                {
                    'step': 2,
                    'title': 'Network Security 🌐',
                    'duration': '5-6 weeks',
                    'topics': [
                        'Firewalls and intrusion detection',
                        'VPN technologies',
                        'Network monitoring and analysis',
                        'Wireless security',
                        'Network segmentation'
                    ],
                    'resources': [
                        {'title': 'Wireshark Documentation', 'url': 'https://www.wireshark.org/docs/'},
                        {'title': 'pfSense Documentation', 'url': 'https://docs.netgate.com/pfsense/en/latest/'},
                        {'title': 'Cisco Security', 'url': 'https://www.cisco.com/c/en/us/products/security/index.html'}
                    ],
                    'projects': ['Firewall configuration', 'Network traffic analysis', 'IDS/IPS setup']
                },
                {
                    'step': 3,
                    'title': 'Ethical Hacking & Penetration Testing 🔍',
                    'duration': '6-8 weeks',
                    'topics': [
                        'Penetration testing methodology',
                        'Vulnerability assessment tools',
                        'Web application security testing',
                        'Social engineering awareness',
                        'Exploit development basics'
                    ],
                    'resources': [
                        {'title': 'Kali Linux Documentation', 'url': 'https://www.kali.org/docs/'},
                        {'title': 'OWASP Testing Guide', 'url': 'https://owasp.org/www-project-web-security-testing-guide/'},
                        {'title': 'Metasploit Documentation', 'url': 'https://docs.rapid7.com/metasploit/'}
                    ],
                    'projects': ['Vulnerability scanner', 'Web app penetration test', 'Security assessment report']
                },
                {
                    'step': 4,
                    'title': 'Incident Response & Forensics 🚨',
                    'duration': '5-6 weeks',
                    'topics': [
                        'Incident response procedures',
                        'Digital forensics techniques',
                        'Malware analysis basics',
                        'Evidence collection and preservation',
                        'Threat hunting methodologies'
                    ],
                    'resources': [
                        {'title': 'SANS Incident Response', 'url': 'https://www.sans.org/white-papers/'},
                        {'title': 'Volatility Framework', 'url': 'https://www.volatilityfoundation.org/'},
                        {'title': 'NIST Incident Response Guide', 'url': 'https://csrc.nist.gov/publications/detail/sp/800-61/rev-2/final'}
                    ],
                    'projects': ['Incident response playbook', 'Forensics investigation', 'Malware analysis lab']
                },
                {
                    'step': 5,
                    'title': 'Compliance & Governance 📋',
                    'duration': '4-5 weeks',
                    'topics': [
                        'Regulatory compliance (GDPR, HIPAA, SOX)',
                        'Security audit procedures',
                        'Policy development and implementation',
                        'Business continuity planning',
                        'Third-party risk management'
                    ],
                    'resources': [
                        {'title': 'ISO 27001 Standard', 'url': 'https://www.iso.org/isoiec-27001-information-security.html'},
                        {'title': 'GDPR Compliance Guide', 'url': 'https://gdpr.eu/'},
                        {'title': 'SOC 2 Framework', 'url': 'https://www.aicpa.org/interestareas/frc/assuranceadvisoryservices/aicpasoc2report.html'}
                    ],
                    'projects': ['Compliance assessment', 'Security policy framework', 'Audit preparation']
                },
                {
                    'step': 6,
                    'title': 'Advanced Security & Specialization 🎯',
                    'duration': '6-8 weeks',
                    'topics': [
                        'Cloud security architecture',
                        'DevSecOps implementation',
                        'Threat intelligence analysis',
                        'Security automation and orchestration',
                        'Emerging threats and technologies'
                    ],
                    'resources': [
                        {'title': 'AWS Security', 'url': 'https://aws.amazon.com/security/'},
                        {'title': 'MITRE ATT&CK Framework', 'url': 'https://attack.mitre.org/'},
                        {'title': 'SANS Security Training', 'url': 'https://www.sans.org/cyber-security-courses/'}
                    ],
                    'projects': ['Cloud security assessment', 'Threat intelligence platform', 'Security automation tool']
                }
            ],
            'career_paths': [
                'Security Analyst',
                'Penetration Tester',
                'Security Architect',
                'Incident Response Specialist',
                'Compliance Officer'
            ],
            'tips': [
                'Stay updated with latest threats and vulnerabilities',
                'Practice in controlled lab environments',
                'Develop both technical and communication skills',
                'Understand business impact of security decisions',
                'Build a network within the security community'
            ]
        },
        'data engineering': {
            'title': 'Data Engineering Roadmap',
            'description': 'Complete guide to becoming a data engineer',
            'prerequisites': 'Programming knowledge, basic database concepts',
            'duration': '7-10 months with consistent practice',
            'steps': [
                {
                    'step': 1,
                    'title': 'Data Fundamentals 📊',
                    'duration': '4-5 weeks',
                    'topics': [
                        'Data types and structures',
                        'Database design principles',
                        'SQL advanced queries',
                        'Data modeling concepts',
                        'ETL/ELT fundamentals'
                    ],
                    'resources': [
                        {'title': 'PostgreSQL Documentation', 'url': 'https://www.postgresql.org/docs/'},
                        {'title': 'SQL Tutorial', 'url': 'https://www.w3schools.com/sql/'},
                        {'title': 'Data Modeling Guide', 'url': 'https://www.guru99.com/data-modelling-conceptual-logical.html'}
                    ],
                    'projects': ['Database design project', 'Complex SQL queries', 'Data warehouse schema']
                },
                {
                    'step': 2,
                    'title': 'Programming for Data 🐍',
                    'duration': '5-6 weeks',
                    'topics': [
                        'Python for data engineering',
                        'Data manipulation with Pandas',
                        'API development and integration',
                        'Error handling and logging',
                        'Code versioning and testing'
                    ],
                    'resources': [
                        {'title': 'Python Documentation', 'url': 'https://docs.python.org/3/'},
                        {'title': 'Pandas Documentation', 'url': 'https://pandas.pydata.org/docs/'},
                        {'title': 'FastAPI Documentation', 'url': 'https://fastapi.tiangolo.com/'}
                    ],
                    'projects': ['Data processing pipeline', 'REST API for data', 'Automated data validation']
                },
                {
                    'step': 3,
                    'title': 'Big Data Technologies 🚀',
                    'duration': '6-8 weeks',
                    'topics': [
                        'Apache Spark fundamentals',
                        'Hadoop ecosystem overview',
                        'Distributed computing concepts',
                        'Data partitioning strategies',
                        'Performance optimization'
                    ],
                    'resources': [
                        {'title': 'Apache Spark Documentation', 'url': 'https://spark.apache.org/docs/latest/'},
                        {'title': 'Hadoop Documentation', 'url': 'https://hadoop.apache.org/docs/'},
                        {'title': 'Databricks Learning', 'url': 'https://databricks.com/learn'}
                    ],
                    'projects': ['Spark data processing job', 'Distributed data analysis', 'Big data pipeline']
                },
                {
                    'step': 4,
                    'title': 'Stream Processing 🌊',
                    'duration': '5-6 weeks',
                    'topics': [
                        'Apache Kafka fundamentals',
                        'Real-time data processing',
                        'Stream processing patterns',
                        'Event-driven architecture',
                        'Data streaming best practices'
                    ],
                    'resources': [
                        {'title': 'Apache Kafka Documentation', 'url': 'https://kafka.apache.org/documentation/'},
                        {'title': 'Confluent Platform', 'url': 'https://docs.confluent.io/'},
                        {'title': 'Apache Flink', 'url': 'https://flink.apache.org/learn-flink/'}
                    ],
                    'projects': ['Real-time analytics pipeline', 'Event streaming system', 'Stream processing application']
                },
                {
                    'step': 5,
                    'title': 'Cloud Data Platforms ☁️',
                    'duration': '5-6 weeks',
                    'topics': [
                        'AWS data services (S3, Redshift, EMR)',
                        'Google Cloud Platform (BigQuery, Dataflow)',
                        'Azure data services (Synapse, Data Factory)',
                        'Data lake architecture',
                        'Serverless data processing'
                    ],
                    'resources': [
                        {'title': 'AWS Data Analytics', 'url': 'https://aws.amazon.com/big-data/datalakes-and-analytics/'},
                        {'title': 'Google Cloud Data', 'url': 'https://cloud.google.com/products/data-analytics'},
                        {'title': 'Azure Data Services', 'url': 'https://azure.microsoft.com/en-us/product-categories/analytics/'}
                    ],
                    'projects': ['Cloud data warehouse', 'Serverless ETL pipeline', 'Multi-cloud data integration']
                },
                {
                    'step': 6,
                    'title': 'DataOps & Orchestration 🎯',
                    'duration': '4-5 weeks',
                    'topics': [
                        'Apache Airflow workflow management',
                        'Data pipeline orchestration',
                        'Data quality monitoring',
                        'CI/CD for data pipelines',
                        'Data governance and lineage'
                    ],
                    'resources': [
                        {'title': 'Apache Airflow', 'url': 'https://airflow.apache.org/docs/'},
                        {'title': 'Prefect Documentation', 'url': 'https://docs.prefect.io/'},
                        {'title': 'Great Expectations', 'url': 'https://docs.greatexpectations.io/'}
                    ],
                    'projects': ['Automated data pipeline', 'Data quality framework', 'Workflow orchestration system']
                }
            ],
            'career_paths': [
                'Data Engineer',
                'Big Data Engineer',
                'Cloud Data Engineer',
                'Data Platform Engineer',
                'Analytics Engineer'
            ],
            'tips': [
                'Focus on building scalable and reliable systems',
                'Understand both batch and real-time processing',
                'Learn multiple cloud platforms',
                'Practice data modeling and optimization',
                'Stay updated with emerging data technologies'
            ]
        },
        'algorithms': {
            'title': 'Algorithms & Data Structures Roadmap',
            'description': 'Complete guide to mastering algorithms and data structures',
            'prerequisites': 'Basic programming knowledge in any language',
            'duration': '6-9 months with consistent practice',
            'steps': [
                {
                    'step': 1,
                    'title': 'Fundamentals & Complexity 📚',
                    'duration': '3-4 weeks',
                    'topics': [
                        'Big O notation and complexity analysis',
                        'Basic data structures (arrays, linked lists)',
                        'Stacks and queues implementation',
                        'Hash tables and hash functions',
                        'Problem-solving strategies'
                    ],
                    'resources': [
                        {'title': 'Introduction to Algorithms (CLRS)', 'url': 'https://mitpress.mit.edu/books/introduction-algorithms-third-edition'},
                        {'title': 'LeetCode Explore', 'url': 'https://leetcode.com/explore/'},
                        {'title': 'GeeksforGeeks DSA', 'url': 'https://www.geeksforgeeks.org/data-structures/'}
                    ],
                    'projects': ['Data structure implementations', 'Complexity analysis exercises', 'Basic algorithm challenges']
                },
                {
                    'step': 2,
                    'title': 'Sorting & Searching 🔍',
                    'duration': '4-5 weeks',
                    'topics': [
                        'Sorting algorithms (bubble, merge, quick, heap)',
                        'Binary search and variations',
                        'Two pointers technique',
                        'Sliding window problems',
                        'Search in rotated arrays'
                    ],
                    'resources': [
                        {'title': 'Sorting Algorithms Visualizer', 'url': 'https://www.sortvisualizer.com/'},
                        {'title': 'Binary Search Patterns', 'url': 'https://leetcode.com/discuss/general-discussion/786126/python-powerful-ultimate-binary-search-template-solved-many-problems'},
                        {'title': 'Algorithm Visualizations', 'url': 'https://algorithm-visualizer.org/'}
                    ],
                    'projects': ['Sorting algorithm comparison', 'Search optimization problems', 'Custom search implementations']
                },
                {
                    'step': 3,
                    'title': 'Trees & Graphs 🌳',
                    'duration': '6-7 weeks',
                    'topics': [
                        'Binary trees and BST operations',
                        'Tree traversals (DFS, BFS)',
                        'Graph representations and algorithms',
                        'Shortest path algorithms (Dijkstra, Floyd-Warshall)',
                        'Minimum spanning trees'
                    ],
                    'resources': [
                        {'title': 'Tree Algorithms', 'url': 'https://www.geeksforgeeks.org/binary-tree-data-structure/'},
                        {'title': 'Graph Algorithms', 'url': 'https://www.geeksforgeeks.org/graph-data-structure-and-algorithms/'},
                        {'title': 'Visualizing Algorithms', 'url': 'https://bost.ocks.org/mike/algorithms/'}
                    ],
                    'projects': ['Binary search tree implementation', 'Graph traversal algorithms', 'Pathfinding visualizer']
                },
                {
                    'step': 4,
                    'title': 'Dynamic Programming 💡',
                    'duration': '5-6 weeks',
                    'topics': [
                        'DP fundamentals and patterns',
                        'Memoization vs tabulation',
                        'Classic DP problems (knapsack, LCS, LIS)',
                        'State space optimization',
                        'Advanced DP techniques'
                    ],
                    'resources': [
                        {'title': 'Dynamic Programming Patterns', 'url': 'https://leetcode.com/discuss/general-discussion/458695/dynamic-programming-patterns'},
                        {'title': 'DP Tutorial', 'url': 'https://www.topcoder.com/community/competitive-programming/tutorials/dynamic-programming-from-novice-to-advanced/'},
                        {'title': 'DP Problems Collection', 'url': 'https://atcoder.jp/contests/dp'}
                    ],
                    'projects': ['Classic DP problem solutions', 'DP optimization challenges', 'Custom DP applications']
                },
                {
                    'step': 5,
                    'title': 'Advanced Algorithms 🚀',
                    'duration': '5-6 weeks',
                    'topics': [
                        'Greedy algorithms and proofs',
                        'Divide and conquer strategies',
                        'Backtracking and branch & bound',
                        'String algorithms (KMP, Rabin-Karp)',
                        'Advanced data structures (segment trees, tries)'
                    ],
                    'resources': [
                        {'title': 'Advanced Algorithms Course', 'url': 'https://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-854j-advanced-algorithms-fall-2008/'},
                        {'title': 'String Algorithms', 'url': 'https://www.geeksforgeeks.org/string-data-structure/'},
                        {'title': 'Competitive Programming Handbook', 'url': 'https://cses.fi/book/book.pdf'}
                    ],
                    'projects': ['String matching algorithms', 'Advanced tree structures', 'Optimization problems']
                },
                {
                    'step': 6,
                    'title': 'System Design & Practice 🎯',
                    'duration': '4-5 weeks',
                    'topics': [
                        'System design fundamentals',
                        'Scalability and performance',
                        'Competitive programming strategies',
                        'Interview preparation techniques',
                        'Code optimization and debugging'
                    ],
                    'resources': [
                        {'title': 'System Design Primer', 'url': 'https://github.com/donnemartin/system-design-primer'},
                        {'title': 'Codeforces', 'url': 'https://codeforces.com/'},
                        {'title': 'Interview Preparation', 'url': 'https://www.interviewbit.com/courses/programming/'}
                    ],
                    'projects': ['System design case studies', 'Contest participation', 'Mock interview practice']
                }
            ],
            'career_paths': [
                'Software Engineer',
                'Competitive Programmer',
                'Algorithm Engineer',
                'Research Scientist',
                'Technical Interviewer'
            ],
            'tips': [
                'Practice consistently on coding platforms',
                'Focus on understanding patterns and techniques',
                'Participate in programming contests',
                'Implement algorithms from scratch',
                'Explain your solutions clearly'
            ]
        }
    }
    
    roadmap = detailed_roadmaps.get(domain, detailed_roadmaps['frontend'])
    return roadmap

@app.post("/download-roadmap")
def download_roadmap_pdf(request: dict):
    # Get domain from request or session
    domain = request.get("domain")
    
    # If no domain in request, get from session
    if not domain and request.get("session_id") in sessions:
        state = sessions[request["session_id"]]
        domain = getattr(state, 'selected_domain', 'frontend')
    
    # Default to frontend if still no domain
    if not domain:
        domain = 'frontend'
    
    domain = domain.lower()
    
    # Get roadmap data
    roadmap_response = get_detailed_roadmap({"domain": domain})
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    
    # Create PDF
    doc = SimpleDocTemplate(temp_file.name, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=HexColor('#2E86AB')
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        textColor=HexColor('#A23B72')
    )
    
    story = []
    
    # Title
    story.append(Paragraph(roadmap_response['title'], title_style))
    story.append(Spacer(1, 12))
    
    # Description
    story.append(Paragraph(f"<b>Description:</b> {roadmap_response['description']}", styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Prerequisites
    story.append(Paragraph(f"<b>Prerequisites:</b> {roadmap_response['prerequisites']}", styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Duration
    story.append(Paragraph(f"<b>Total Duration:</b> {roadmap_response['duration']}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Steps
    for step in roadmap_response['steps']:
        story.append(Paragraph(f"Step {step['step']}: {step['title']}", heading_style))
        story.append(Paragraph(f"<b>Duration:</b> {step['duration']}", styles['Normal']))
        story.append(Spacer(1, 8))
        
        # Topics
        story.append(Paragraph("<b>Topics to Learn:</b>", styles['Normal']))
        for topic in step['topics']:
            story.append(Paragraph(f"• {topic}", styles['Normal']))
        story.append(Spacer(1, 8))
        
        # Projects
        story.append(Paragraph("<b>Practice Projects:</b>", styles['Normal']))
        for project in step['projects']:
            story.append(Paragraph(f"• {project}", styles['Normal']))
        story.append(Spacer(1, 8))
        
        # Resources
        story.append(Paragraph("<b>Learning Resources:</b>", styles['Normal']))
        for resource in step['resources']:
            story.append(Paragraph(f"• {resource['title']}: {resource['url']}", styles['Normal']))
        
        story.append(Spacer(1, 20))
    
    # Career paths
    story.append(Paragraph("Career Opportunities", heading_style))
    for career in roadmap_response['career_paths']:
        story.append(Paragraph(f"• {career}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Tips
    story.append(Paragraph("Success Tips", heading_style))
    for tip in roadmap_response['tips']:
        story.append(Paragraph(f"• {tip}", styles['Normal']))
    
    # Build PDF
    doc.build(story)
    
    # Return file
    return FileResponse(
        temp_file.name,
        media_type='application/pdf',
        filename=f"{domain}_roadmap.pdf"
    )

@app.post("/feedback")
def submit_feedback(request: dict):
    if request.get("session_id") not in sessions:
        return {"message": "Thank you for your feedback!"}
    
    state = sessions[request["session_id"]]
    user_name = getattr(state, 'user_name', 'there')
    domain = getattr(state, 'selected_domain', 'frontend')
    
    # Domain-specific documentation links
    domain_docs = {
        'frontend': {
            'message': f"Thank you so much for your valuable feedback, {user_name}! For further learning, I recommend checking these official resources:",
            'docs': [
                {'title': 'MDN Web Docs', 'url': 'https://developer.mozilla.org/en-US/'},
                {'title': 'React Documentation', 'url': 'https://react.dev/'},
                {'title': 'CSS-Tricks', 'url': 'https://css-tricks.com/'}
            ]
        },
        'backend': {
            'message': f"Thank you so much for your valuable feedback, {user_name}! For further learning, I recommend checking these official resources:",
            'docs': [
                {'title': 'FastAPI Documentation', 'url': 'https://fastapi.tiangolo.com/'},
                {'title': 'Node.js Documentation', 'url': 'https://nodejs.org/en/docs/'},
                {'title': 'PostgreSQL Documentation', 'url': 'https://www.postgresql.org/docs/'}
            ]
        },
        'data analytics': {
            'message': f"Thank you so much for your valuable feedback, {user_name}! For further learning, I recommend checking these official resources:",
            'docs': [
                {'title': 'Pandas Documentation', 'url': 'https://pandas.pydata.org/docs/'},
                {'title': 'Tableau Learning', 'url': 'https://www.tableau.com/learn'},
                {'title': 'SQL Tutorial - W3Schools', 'url': 'https://www.w3schools.com/sql/'}
            ]
        },
        'machine learning': {
            'message': f"Thank you so much for your valuable feedback, {user_name}! For further learning, I recommend checking these official resources:",
            'docs': [
                {'title': 'Scikit-learn Documentation', 'url': 'https://scikit-learn.org/stable/'},
                {'title': 'TensorFlow Documentation', 'url': 'https://www.tensorflow.org/learn'},
                {'title': 'PyTorch Documentation', 'url': 'https://pytorch.org/docs/stable/index.html'}
            ]
        },
        'devops': {
            'message': f"Thank you so much for your valuable feedback, {user_name}! For further learning, I recommend checking these official resources:",
            'docs': [
                {'title': 'Docker Documentation', 'url': 'https://docs.docker.com/'},
                {'title': 'Kubernetes Documentation', 'url': 'https://kubernetes.io/docs/home/'},
                {'title': 'AWS Documentation', 'url': 'https://docs.aws.amazon.com/'}
            ]
        },
        'cybersecurity': {
            'message': f"Thank you so much for your valuable feedback, {user_name}! For further learning, I recommend checking these official resources:",
            'docs': [
                {'title': 'OWASP Foundation', 'url': 'https://owasp.org/'},
                {'title': 'NIST Cybersecurity Framework', 'url': 'https://www.nist.gov/cyberframework'},
                {'title': 'SANS Institute', 'url': 'https://www.sans.org/white-papers/'}
            ]
        },
        'data engineering': {
            'message': f"Thank you so much for your valuable feedback, {user_name}! For further learning, I recommend checking these official resources:",
            'docs': [
                {'title': 'Apache Spark Documentation', 'url': 'https://spark.apache.org/docs/latest/'},
                {'title': 'Apache Kafka Documentation', 'url': 'https://kafka.apache.org/documentation/'},
                {'title': 'Airflow Documentation', 'url': 'https://airflow.apache.org/docs/'}
            ]
        },
        'algorithms': {
            'message': f"Thank you so much for your valuable feedback, {user_name}! For further learning, I recommend checking these official resources:",
            'docs': [
                {'title': 'LeetCode', 'url': 'https://leetcode.com/'},
                {'title': 'GeeksforGeeks', 'url': 'https://www.geeksforgeeks.org/'},
                {'title': 'Algorithm Visualizer', 'url': 'https://algorithm-visualizer.org/'}
            ]
        }
    }
    
    domain_info = domain_docs.get(domain, domain_docs['frontend'])
    
    # Log feedback for improvement (optional)
    print(f"Feedback from {user_name}: {request['feedback']}")
    
    return {
        "message": domain_info['message'],
        "docs": domain_info['docs']
    }

@app.post("/chat")
def chat(request: dict):
    if request.get("session_id") not in sessions:
        return {"message": "Session not found"}
    
    state = sessions[request["session_id"]]
    user_message = request["message"].lower().strip()
    
    # Initialize docs_shown flag if not exists
    if not hasattr(state, 'docs_shown'):
        state.docs_shown = False
    
    # Check if user mentions a different domain after assessment
    valid_domains = ['backend', 'frontend', 'data analytics', 'machine learning', 'devops', 'cybersecurity', 'data engineering', 'algorithms']
    mentioned_domain = None
    
    for domain in valid_domains:
        if domain in user_message or any(word in user_message for word in domain.split()):
            mentioned_domain = domain
            break
    
    # If user mentions a different domain, offer to switch
    if mentioned_domain and mentioned_domain != getattr(state, 'selected_domain', None):
        state.pending_domain_switch = mentioned_domain
        return {
            "message": f"I see you're interested in {mentioned_domain}! Would you like me to provide a roadmap for {mentioned_domain} instead? Just say 'yes' and I'll generate it for you.",
            "switch_domain": mentioned_domain
        }
    
    # Handle domain switch confirmation
    if hasattr(state, 'pending_domain_switch') and user_message in ['yes', 'y', 'sure', 'okay', 'ok']:
        # Switch to new domain
        new_domain = state.pending_domain_switch
        state.selected_domain = new_domain
        delattr(state, 'pending_domain_switch')
        return {
            "message": f"Great! I've switched to {new_domain}. Let me generate a roadmap for you.",
            "generate_roadmap": new_domain
        }
    
    domain = getattr(state, 'selected_domain', 'frontend')
    
    # Domain-specific documentation links
    domain_docs = {
        'frontend': [
            {'title': 'MDN Web Docs', 'url': 'https://developer.mozilla.org/en-US/'},
            {'title': 'React Documentation', 'url': 'https://react.dev/'},
            {'title': 'CSS-Tricks', 'url': 'https://css-tricks.com/'}
        ],
        'backend': [
            {'title': 'FastAPI Documentation', 'url': 'https://fastapi.tiangolo.com/'},
            {'title': 'Node.js Documentation', 'url': 'https://nodejs.org/en/docs/'},
            {'title': 'PostgreSQL Documentation', 'url': 'https://www.postgresql.org/docs/'}
        ],
        'data analytics': [
            {'title': 'Pandas Documentation', 'url': 'https://pandas.pydata.org/docs/'},
            {'title': 'Tableau Learning', 'url': 'https://www.tableau.com/learn'},
            {'title': 'SQL Tutorial - W3Schools', 'url': 'https://www.w3schools.com/sql/'}
        ],
        'machine learning': [
            {'title': 'Scikit-learn Documentation', 'url': 'https://scikit-learn.org/stable/'},
            {'title': 'TensorFlow Documentation', 'url': 'https://www.tensorflow.org/learn'},
            {'title': 'PyTorch Documentation', 'url': 'https://pytorch.org/docs/stable/index.html'}
        ],
        'devops': [
            {'title': 'Docker Documentation', 'url': 'https://docs.docker.com/'},
            {'title': 'Kubernetes Documentation', 'url': 'https://kubernetes.io/docs/home/'},
            {'title': 'AWS Documentation', 'url': 'https://docs.aws.amazon.com/'}
        ],
        'cybersecurity': [
            {'title': 'OWASP Foundation', 'url': 'https://owasp.org/'},
            {'title': 'NIST Cybersecurity Framework', 'url': 'https://www.nist.gov/cyberframework'},
            {'title': 'SANS Institute', 'url': 'https://www.sans.org/white-papers/'}
        ],
        'data engineering': [
            {'title': 'Apache Spark Documentation', 'url': 'https://spark.apache.org/docs/latest/'},
            {'title': 'Apache Kafka Documentation', 'url': 'https://kafka.apache.org/documentation/'},
            {'title': 'Airflow Documentation', 'url': 'https://airflow.apache.org/docs/'}
        ],
        'algorithms': [
            {'title': 'LeetCode', 'url': 'https://leetcode.com/'},
            {'title': 'GeeksforGeeks', 'url': 'https://www.geeksforgeeks.org/'},
            {'title': 'Algorithm Visualizer', 'url': 'https://algorithm-visualizer.org/'}
        ]
    }
    
    # Handle thank you messages
    if any(word in user_message for word in ['thank', 'thanks', 'appreciate', 'helpful']):
        return {
            "message": "You're very welcome! I'm glad I could help. Feel free to ask if you have any other questions about your learning journey!"
        }
    
    # Handle improvement questions
    if any(word in user_message for word in ['improve', 'better', 'learn', 'study', 'focus', 'next', 'recommend']):
        if hasattr(state, 'selected_domain') and state.selected_domain:
            domain_tips = {
                'frontend': {
                    'beginner': ['HTML5 semantic elements', 'CSS Flexbox and Grid', 'JavaScript ES6+ features', 'Responsive design principles'],
                    'intermediate': ['React or Vue.js', 'State management', 'Build tools (Webpack/Vite)', 'CSS preprocessors'],
                    'advanced': ['Performance optimization', 'Advanced React patterns', 'Testing frameworks', 'Progressive Web Apps']
                },
                'backend': {
                    'beginner': ['HTTP and REST principles', 'Database fundamentals', 'Basic authentication', 'API design'],
                    'intermediate': ['Advanced SQL queries', 'Caching strategies', 'Microservices basics', 'Cloud deployment'],
                    'advanced': ['System design', 'Load balancing', 'Database optimization', 'Security best practices']
                }
            }
            
            # Determine level based on score
            if hasattr(state, 'score'):
                percentage = (state.score / 6) * 100
                level = 'advanced' if percentage >= 80 else 'intermediate' if percentage >= 50 else 'beginner'
            else:
                level = 'beginner'
            
            tips = domain_tips.get(state.selected_domain, {}).get(level, [f'{state.selected_domain} fundamentals', 'Best practices', 'Hands-on projects'])
            
            return {
                "message": f"To improve your {state.selected_domain} skills, I recommend focusing on: {', '.join(tips)}. Start with hands-on projects and practice regularly!",
                "docs": domain_docs.get(domain, domain_docs['frontend'])
            }
    
    # Handle general questions with documentation links (only if not shown before)
    if any(word in user_message for word in ['how', 'what', 'why', 'when', 'where', 'help', 'guide', 'tutorial']):
        if not state.docs_shown:
            state.docs_shown = True
            return {
                "message": "That's a great question! For specific technical guidance, I recommend checking these official resources and documentation:",
                "docs": domain_docs.get(domain, domain_docs['frontend'])
            }
        else:
            return {
                "message": "I'd be happy to help! Could you be more specific about what you'd like to know? You can also refer to the documentation links I shared earlier."
            }
    
    # Default response
    return {
        "message": "Thanks for your question! I'm here to help with your learning journey. Is there anything specific you'd like to know about your assessment or career path?"
    }