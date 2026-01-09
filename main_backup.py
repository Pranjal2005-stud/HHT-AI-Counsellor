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
    } knapsack problem, longest common subsequence, and Fibonacci sequence optimization. Understanding dynamic programming involves recognizing when to apply it, designing state representations, and implementing both top-down (memoization) and bottom-up (tabulation) approaches. This technique is essential for solving many algorithmic challenges efficiently."},
            {"q": "Do you understand graph algorithms and tree traversals?", "exp": "Graph algorithms and tree traversals are essential for solving problems involving relationships and hierarchical data structures. Graph algorithms include breadth-first search (BFS), depth-first search (DFS), shortest path algorithms (Dijkstra's, Bellman-Ford), and minimum spanning tree algorithms (Kruskal's, Prim's). Tree traversals include in-order, pre-order, and post-order traversals for binary trees. Understanding these concepts involves knowing how to represent graphs and trees, implement traversal algorithms, and apply them to solve real-world problems like social network analysis, route planning, and decision trees."},
            {"q": "Are you familiar with time and space complexity analysis?", "exp": "Time and space complexity analysis involves evaluating how algorithm performance scales with input size, typically expressed using Big O notation. Time complexity measures how execution time grows with input size, while space complexity measures memory usage growth. Understanding complexity analysis involves recognizing common patterns (O(1), O(log n), O(n), O(n²), O(2ⁿ)), analyzing loops and recursive calls, and comparing algorithm efficiency. This knowledge is crucial for choosing appropriate algorithms, optimizing code performance, and making informed decisions about trade-offs between time and space efficiency in software development."},
            {"q": "Have you participated in competitive programming or coding contests?", "exp": "Competitive programming involves solving algorithmic problems under time constraints, typically in contests like ACM ICPC, Codeforces, or LeetCode competitions. It requires quick problem analysis, efficient algorithm implementation, and strong debugging skills. Competitive programming helps develop pattern recognition for common problem types, improves coding speed and accuracy, and builds confidence in handling complex algorithmic challenges. Experience in competitive programming demonstrates strong problem-solving abilities and is highly valued by technology companies for technical roles, as it indicates proficiency in algorithms, data structures, and coding under pressure."}
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
            # Create a more meaningful explanation
            topic_explanations = {
                'frontend': {
                    'Do you have experience with frontend development?': 'Frontend Development Fundamentals: Learn HTML5, CSS3, and JavaScript basics to build user interfaces.',
                    'Have you worked with React, Vue, or Angular?': 'Modern JavaScript Frameworks: Master component-based development with popular frameworks.',
                    'Do you understand responsive design principles?': 'Responsive Web Design: Create websites that work seamlessly across all devices and screen sizes.',
                    'Are you familiar with CSS preprocessors like Sass or Less?': 'CSS Preprocessors: Use advanced CSS tools for better code organization and maintainability.',
                    'Have you used build tools like Webpack or Vite?': 'Build Tools & Bundlers: Optimize development workflow with modern build and bundling tools.',
                    'Do you know about web performance optimization?': 'Web Performance: Implement techniques to make websites faster and more efficient.'
                },
                'backend': {
                    'Do you have experience with backend development?': 'Backend Development Fundamentals: Learn server-side programming, APIs, and database integration.',
                    'Have you worked with databases like MySQL or PostgreSQL?': 'Database Management: Master SQL databases for data storage and retrieval in applications.',
                    'Are you familiar with REST API development?': 'API Development: Build RESTful services for communication between applications.',
                    'Do you understand authentication and authorization?': 'Security & Authentication: Implement secure user authentication and access control systems.',
                    'Have you used cloud services like AWS or Azure?': 'Cloud Computing: Deploy and scale applications using modern cloud platforms.',
                    'Do you know about microservices architecture?': 'Microservices Architecture: Design scalable, distributed systems with independent services.'
                },
                'data analytics': {
                    'Do you have experience with data analytics?': 'Data Analytics Fundamentals: Learn statistical analysis, data visualization, and insight generation.',
                    'Have you worked with SQL for data querying?': 'SQL Mastery: Master database querying and data manipulation for analytics.',
                    'Are you familiar with data visualization tools like Tableau or Power BI?': 'Data Visualization: Create compelling dashboards and reports using modern BI tools.',
                    'Do you understand statistical analysis and hypothesis testing?': 'Statistical Analysis: Apply statistical methods and hypothesis testing for data-driven decisions.',
                    'Have you used Python or R for data analysis?': 'Programming for Analytics: Use Python or R for advanced data analysis and automation.',
                    'Do you know about data cleaning and preprocessing techniques?': 'Data Preprocessing: Master data cleaning and preparation techniques for quality analysis.'
                },
                'machine learning': {
                    'Do you have experience with machine learning?': 'Machine Learning Fundamentals: Understand algorithms, model training, and prediction systems.',
                    'Are you familiar with supervised learning algorithms?': 'Supervised Learning: Master classification and regression algorithms for predictive modeling.',
                    'Have you worked with popular ML libraries like scikit-learn or TensorFlow?': 'ML Libraries & Frameworks: Use industry-standard tools for machine learning implementation.',
                    'Do you understand model evaluation and validation techniques?': 'Model Evaluation: Learn techniques to assess and validate machine learning model performance.',
                    'Are you familiar with feature engineering and selection?': 'Feature Engineering: Master the art of creating and selecting relevant features for ML models.',
                    'Have you deployed machine learning models in production?': 'ML Deployment: Learn to deploy and maintain machine learning models in production environments.'
                },
                'devops': {
                    'Do you have experience with DevOps practices?': 'DevOps Fundamentals: Learn collaboration, automation, and continuous delivery practices.',
                    'Are you familiar with containerization using Docker?': 'Containerization: Master Docker for application packaging and deployment consistency.',
                    'Have you worked with cloud platforms like AWS, Azure, or GCP?': 'Cloud Platforms: Deploy and manage applications using major cloud service providers.',
                    'Do you understand CI/CD pipeline implementation?': 'CI/CD Pipelines: Automate build, test, and deployment processes for faster delivery.',
                    'Are you familiar with infrastructure as code (IaC) tools?': 'Infrastructure as Code: Manage infrastructure through code using tools like Terraform.',
                    'Have you implemented monitoring and logging solutions?': 'Monitoring & Logging: Implement comprehensive observability for system health and performance.'
                },
                'cybersecurity': {
                    'Do you have experience with cybersecurity fundamentals?': 'Cybersecurity Fundamentals: Learn security principles, threat assessment, and defense strategies.',
                    'Are you familiar with network security and firewalls?': 'Network Security: Master network protection, firewalls, and intrusion detection systems.',
                    'Have you worked with vulnerability assessment and penetration testing?': 'Security Testing: Learn to identify and exploit vulnerabilities through ethical hacking.',
                    'Do you understand incident response and forensics?': 'Incident Response: Master security incident handling and digital forensics techniques.',
                    'Are you familiar with security compliance frameworks?': 'Security Compliance: Understand regulatory frameworks and compliance requirements.',
                    'Have you implemented security awareness and training programs?': 'Security Awareness: Develop programs to educate users about cybersecurity best practices.'
                },
                'data engineering': {
                    'Do you have experience with data engineering?': 'Data Engineering Fundamentals: Learn to build scalable data pipelines and infrastructure.',
                    'Are you familiar with big data technologies like Hadoop or Spark?': 'Big Data Technologies: Master distributed computing frameworks for large-scale data processing.',
                    'Have you built ETL/ELT data pipelines?': 'Data Pipelines: Design and implement robust ETL/ELT processes for data transformation.',
                    'Do you understand data warehousing and data lake concepts?': 'Data Architecture: Learn modern data storage and organization strategies.',
                    'Are you familiar with stream processing and real-time data?': 'Stream Processing: Handle real-time data streams for immediate insights and responses.',
                    'Have you worked with cloud data services?': 'Cloud Data Services: Leverage managed cloud services for scalable data solutions.'
                },
                'algorithms': {
                    'Do you have experience with algorithms and data structures?': 'Algorithms & Data Structures: Master fundamental computer science concepts for efficient programming.',
                    'Are you familiar with sorting and searching algorithms?': 'Sorting & Searching: Learn essential algorithms for data organization and retrieval.',
                    'Have you solved problems using dynamic programming?': 'Dynamic Programming: Master optimization techniques for complex algorithmic problems.',
                    'Do you understand graph algorithms and tree traversals?': 'Graph Algorithms: Learn to solve problems involving networks, relationships, and hierarchical data.',
                    'Are you familiar with time and space complexity analysis?': 'Complexity Analysis: Understand algorithm efficiency and performance optimization.',
                    'Have you participated in competitive programming or coding contests?': 'Competitive Programming: Develop problem-solving skills through algorithmic challenges and contests.'
                }
            }
            
            
            domain_topics = topic_explanations.get(state.selected_domain, {})
            topic_explanation = domain_topics.get(ans["question"], f"Learn more about: {ans['question'].replace('Do you ', '').replace('Have you ', '').replace('Are you ', '')}")
            
            areas_to_improve.append({
                "question": ans["question"],
                "answer": ans["answer"],
                "explanation": topic_explanation
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
    domain = request.get("domain", "frontend").lower()
    
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
            'description': 'Comprehensive path to becoming a skilled backend developer',
            'prerequisites': 'Basic programming knowledge, understanding of databases',
            'duration': '8-10 months with consistent practice',
            'steps': [
                {
                    'step': 1,
                    'title': 'Programming Language Mastery 💻',
                    'duration': '6-8 weeks',
                    'topics': [
                        'Python/Node.js fundamentals',
                        'Object-oriented programming concepts',
                        'Data structures and algorithms',
                        'File handling and I/O operations',
                        'Error handling and debugging'
                    ],
                    'resources': [
                        {'title': 'Python Official Tutorial', 'url': 'https://docs.python.org/3/tutorial/'},
                        {'title': 'Node.js Documentation', 'url': 'https://nodejs.org/en/docs/'},
                        {'title': 'LeetCode Practice', 'url': 'https://leetcode.com/'}
                    ],
                    'projects': ['Command-line calculator', 'File processing utility', 'Basic web scraper']
                },
                {
                    'step': 2,
                    'title': 'Database Fundamentals 🗄️',
                    'duration': '4-6 weeks',
                    'topics': [
                        'SQL basics and advanced queries',
                        'Database design and normalization',
                        'PostgreSQL/MySQL administration',
                        'Indexing and query optimization',
                        'NoSQL databases (MongoDB)'
                    ],
                    'resources': [
                        {'title': 'PostgreSQL Tutorial', 'url': 'https://www.postgresql.org/docs/current/tutorial.html'},
                        {'title': 'SQL Bolt', 'url': 'https://sqlbolt.com/'},
                        {'title': 'MongoDB University', 'url': 'https://university.mongodb.com/'}
                    ],
                    'projects': ['Library management system', 'E-commerce database design', 'Data analysis with SQL']
                },
                {
                    'step': 3,
                    'title': 'Web Framework & APIs 🌐',
                    'duration': '8-10 weeks',
                    'topics': [
                        'REST API design principles',
                        'FastAPI/Express.js framework',
                        'Request/Response handling',
                        'Middleware and routing',
                        'API documentation with Swagger'
                    ],
                    'resources': [
                        {'title': 'FastAPI Documentation', 'url': 'https://fastapi.tiangolo.com/'},
                        {'title': 'Express.js Guide', 'url': 'https://expressjs.com/en/guide/routing.html'},
                        {'title': 'REST API Tutorial', 'url': 'https://restfulapi.net/'}
                    ],
                    'projects': ['Blog API with CRUD operations', 'User management system', 'File upload service']
                },
                {
                    'step': 4,
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
                        {'title': 'JWT.io', 'url': 'https://jwt.io/'},
                        {'title': 'OWASP Security Guide', 'url': 'https://owasp.org/www-project-top-ten/'},
                        {'title': 'Auth0 Documentation', 'url': 'https://auth0.com/docs'}
                    ],
                    'projects': ['Secure login system', 'Role-based access control', 'OAuth integration']
                },
                {
                    'step': 5,
                    'title': 'Cloud & DevOps Basics ☁️',
                    'duration': '6-8 weeks',
                    'topics': [
                        'Cloud platforms (AWS, Azure, GCP)',
                        'Containerization with Docker',
                        'CI/CD pipelines',
                        'Environment configuration',
                        'Monitoring and logging'
                    ],
                    'resources': [
                        {'title': 'AWS Documentation', 'url': 'https://docs.aws.amazon.com/'},
                        {'title': 'Docker Documentation', 'url': 'https://docs.docker.com/'},
                        {'title': 'GitHub Actions', 'url': 'https://docs.github.com/en/actions'}
                    ],
                    'projects': ['Dockerized application', 'AWS deployment', 'Automated deployment pipeline']
                },
                {
                    'step': 6,
                    'title': 'Advanced Architecture 🏗️',
                    'duration': '8-10 weeks',
                    'topics': [
                        'Microservices architecture',
                        'Message queues and event-driven systems',
                        'Caching strategies (Redis)',
                        'Load balancing and scaling',
                        'System design principles'
                    ],
                    'resources': [
                        {'title': 'Microservices Patterns', 'url': 'https://microservices.io/patterns/'},
                        {'title': 'Redis Documentation', 'url': 'https://redis.io/documentation'},
                        {'title': 'System Design Primer', 'url': 'https://github.com/donnemartin/system-design-primer'}
                    ],
                    'projects': ['Microservices application', 'Real-time notification system', 'High-availability system']
                }
            ],
            'career_paths': [
                'Backend Developer',
                'API Developer',
                'DevOps Engineer',
                'System Architect',
                'Full-Stack Developer'
            ],
            'tips': [
                'Focus on writing clean, maintainable code',
                'Learn database optimization techniques',
                'Understand system design principles',
                'Practice with real-world projects',
                'Stay updated with cloud technologies'
            ]
        },
        'data analytics': {
            'title': 'Data Analytics Roadmap',
            'description': 'Complete guide to becoming a skilled data analyst',
            'prerequisites': 'Basic mathematics, statistics knowledge, Excel proficiency',
            'duration': '6-8 months with consistent practice',
            'steps': [
                {
                    'step': 1,
                    'title': 'Foundation & Excel Mastery 📊',
                    'duration': '3-4 weeks',
                    'topics': [
                        'Statistics fundamentals and descriptive analytics',
                        'Advanced Excel functions and pivot tables',
                        'Data visualization principles',
                        'Business intelligence concepts',
                        'Data types and measurement scales'
                    ],
                    'resources': [
                        {'title': 'Khan Academy Statistics', 'url': 'https://www.khanacademy.org/math/statistics-probability'},
                        {'title': 'Excel Exposure', 'url': 'https://excelexposure.com/'},
                        {'title': 'Microsoft Excel Help', 'url': 'https://support.microsoft.com/en-us/excel'}
                    ],
                    'projects': ['Sales analysis dashboard in Excel', 'Statistical analysis of survey data', 'Financial modeling spreadsheet']
                },
                {
                    'step': 2,
                    'title': 'SQL & Database Fundamentals 🗄️',
                    'duration': '4-5 weeks',
                    'topics': [
                        'SQL basics: SELECT, WHERE, GROUP BY, JOIN',
                        'Advanced SQL: window functions, CTEs, subqueries',
                        'Database design and normalization',
                        'Data warehousing concepts',
                        'ETL processes and data quality'
                    ],
                    'resources': [
                        {'title': 'W3Schools SQL Tutorial', 'url': 'https://www.w3schools.com/sql/'},
                        {'title': 'SQLBolt Interactive Tutorial', 'url': 'https://sqlbolt.com/'},
                        {'title': 'PostgreSQL Documentation', 'url': 'https://www.postgresql.org/docs/'}
                    ],
                    'projects': ['E-commerce database analysis', 'Customer segmentation with SQL', 'Sales performance reporting system']
                },
                {
                    'step': 3,
                    'title': 'Python for Data Analysis 🐍',
                    'duration': '6-8 weeks',
                    'topics': [
                        'Python basics and data structures',
                        'Pandas for data manipulation and cleaning',
                        'NumPy for numerical computations',
                        'Matplotlib and Seaborn for visualization',
                        'Jupyter notebooks and data exploration'
                    ],
                    'resources': [
                        {'title': 'Pandas Documentation', 'url': 'https://pandas.pydata.org/docs/'},
                        {'title': 'Python for Data Analysis Book', 'url': 'https://wesmckinney.com/book/'},
                        {'title': 'Kaggle Learn Python', 'url': 'https://www.kaggle.com/learn/python'}
                    ],
                    'projects': ['COVID-19 data analysis', 'Stock market trend analysis', 'Customer churn prediction']
                },
                {
                    'step': 4,
                    'title': 'Statistical Analysis & Hypothesis Testing 📈',
                    'duration': '4-5 weeks',
                    'topics': [
                        'Probability distributions and sampling',
                        'Hypothesis testing and p-values',
                        'Correlation and regression analysis',
                        'A/B testing and experimental design',
                        'Confidence intervals and statistical significance'
                    ],
                    'resources': [
                        {'title': 'Statistics by Jim', 'url': 'https://statisticsbyjim.com/'},
                        {'title': 'Scipy Stats Documentation', 'url': 'https://docs.scipy.org/doc/scipy/reference/stats.html'},
                        {'title': 'Coursera Statistics Course', 'url': 'https://www.coursera.org/learn/statistical-inferences'}
                    ],
                    'projects': ['A/B test analysis for website optimization', 'Market research statistical study', 'Quality control analysis']
                },
                {
                    'step': 5,
                    'title': 'Business Intelligence Tools 📊',
                    'duration': '5-6 weeks',
                    'topics': [
                        'Tableau desktop and Tableau Public',
                        'Power BI desktop and Power BI Service',
                        'Dashboard design best practices',
                        'Data storytelling and presentation',
                        'KPI development and monitoring'
                    ],
                    'resources': [
                        {'title': 'Tableau Learning', 'url': 'https://www.tableau.com/learn'},
                        {'title': 'Microsoft Power BI Learning', 'url': 'https://docs.microsoft.com/en-us/power-bi/'},
                        {'title': 'Storytelling with Data', 'url': 'http://www.storytellingwithdata.com/'}
                    ],
                    'projects': ['Executive dashboard for retail business', 'HR analytics dashboard', 'Financial performance monitoring system']
                },
                {
                    'step': 6,
                    'title': 'Advanced Analytics & Portfolio 🎯',
                    'duration': '6-8 weeks',
                    'topics': [
                        'Time series analysis and forecasting',
                        'Cohort analysis and customer lifetime value',
                        'Advanced visualization techniques',
                        'Portfolio development and presentation',
                        'Industry-specific analytics applications'
                    ],
                    'resources': [
                        {'title': 'Time Series Analysis in Python', 'url': 'https://www.statsmodels.org/stable/tsa.html'},
                        {'title': 'Kaggle Datasets', 'url': 'https://www.kaggle.com/datasets'},
                        {'title': 'GitHub Portfolio Examples', 'url': 'https://github.com/topics/data-analysis'}
                    ],
                    'projects': ['End-to-end business analytics project', 'Predictive analytics model', 'Industry case study analysis']
                }
            ],
            'career_paths': [
                'Data Analyst',
                'Business Analyst',
                'Marketing Analyst',
                'Financial Analyst',
                'Operations Analyst'
            ],
            'tips': [
                'Focus on business context, not just technical skills',
                'Practice storytelling with data visualizations',
                'Build a portfolio with diverse industry projects',
                'Learn to ask the right business questions',
                'Stay updated with industry trends and tools'
            ]
        },
        'machine learning': {
            'title': 'Machine Learning Roadmap',
            'description': 'Comprehensive path to becoming an ML engineer',
            'prerequisites': 'Python programming, basic statistics, linear algebra',
            'duration': '8-12 months with consistent practice',
            'steps': [
                {
                    'step': 1,
                    'title': 'Mathematical Foundations 🔢',
                    'duration': '4-6 weeks',
                    'topics': [
                        'Linear algebra: vectors, matrices, eigenvalues',
                        'Calculus: derivatives, gradients, optimization',
                        'Statistics and probability theory',
                        'Information theory basics',
                        'Mathematical notation for ML'
                    ],
                    'resources': [
                        {'title': '3Blue1Brown Linear Algebra', 'url': 'https://www.3blue1brown.com/topics/linear-algebra'},
                        {'title': 'Khan Academy Calculus', 'url': 'https://www.khanacademy.org/math/calculus-1'},
                        {'title': 'Mathematics for Machine Learning', 'url': 'https://mml-book.github.io/'}
                    ],
                    'projects': ['Matrix operations implementation', 'Gradient descent from scratch', 'Statistical analysis of datasets']
                },
                {
                    'step': 2,
                    'title': 'Python & Data Science Libraries 🐍',
                    'duration': '4-5 weeks',
                    'topics': [
                        'Advanced Python programming concepts',
                        'NumPy for numerical computing',
                        'Pandas for data manipulation',
                        'Matplotlib and Seaborn for visualization',
                        'Jupyter notebooks and development workflow'
                    ],
                    'resources': [
                        {'title': 'NumPy Documentation', 'url': 'https://numpy.org/doc/stable/'},
                        {'title': 'Pandas User Guide', 'url': 'https://pandas.pydata.org/docs/user_guide/'},
                        {'title': 'Python Data Science Handbook', 'url': 'https://jakevdp.github.io/PythonDataScienceHandbook/'}
                    ],
                    'projects': ['Data cleaning and EDA project', 'Statistical visualization dashboard', 'Automated data processing pipeline']
                },
                {
                    'step': 3,
                    'title': 'Classical Machine Learning 🤖',
                    'duration': '6-8 weeks',
                    'topics': [
                        'Supervised learning: regression and classification',
                        'Unsupervised learning: clustering and dimensionality reduction',
                        'Model evaluation and cross-validation',
                        'Feature engineering and selection',
                        'Scikit-learn ecosystem'
                    ],
                    'resources': [
                        {'title': 'Scikit-learn Documentation', 'url': 'https://scikit-learn.org/stable/'},
                        {'title': 'Hands-On Machine Learning', 'url': 'https://www.oreilly.com/library/view/hands-on-machine-learning/9781492032632/'},
                        {'title': 'Andrew Ng ML Course', 'url': 'https://www.coursera.org/learn/machine-learning'}
                    ],
                    'projects': ['House price prediction model', 'Customer segmentation analysis', 'Image classification with traditional ML']
                },
                {
                    'step': 4,
                    'title': 'Deep Learning Fundamentals 🧠',
                    'duration': '8-10 weeks',
                    'topics': [
                        'Neural networks and backpropagation',
                        'TensorFlow and PyTorch frameworks',
                        'Convolutional Neural Networks (CNNs)',
                        'Recurrent Neural Networks (RNNs)',
                        'Transfer learning and pre-trained models'
                    ],
                    'resources': [
                        {'title': 'TensorFlow Documentation', 'url': 'https://www.tensorflow.org/learn'},
                        {'title': 'PyTorch Tutorials', 'url': 'https://pytorch.org/tutorials/'},
                        {'title': 'Deep Learning Specialization', 'url': 'https://www.coursera.org/specializations/deep-learning'}
                    ],
                    'projects': ['Image classification with CNNs', 'Text sentiment analysis with RNNs', 'Transfer learning for custom datasets']
                },
                {
                    'step': 5,
                    'title': 'MLOps & Production Deployment 🚀',
                    'duration': '6-8 weeks',
                    'topics': [
                        'Model versioning and experiment tracking',
                        'CI/CD pipelines for ML models',
                        'Model serving and API development',
                        'Monitoring and model drift detection',
                        'Cloud platforms for ML (AWS, GCP, Azure)'
                    ],
                    'resources': [
                        {'title': 'MLflow Documentation', 'url': 'https://mlflow.org/docs/latest/index.html'},
                        {'title': 'Kubeflow Documentation', 'url': 'https://www.kubeflow.org/docs/'},
                        {'title': 'AWS SageMaker', 'url': 'https://docs.aws.amazon.com/sagemaker/'}
                    ],
                    'projects': ['End-to-end ML pipeline', 'Model deployment with Docker', 'Real-time prediction API']
                },
                {
                    'step': 6,
                    'title': 'Specialized Applications & Research 🎯',
                    'duration': '8-10 weeks',
                    'topics': [
                        'Natural Language Processing (NLP)',
                        'Computer Vision applications',
                        'Reinforcement Learning basics',
                        'Generative AI and Large Language Models',
                        'Research paper implementation'
                    ],
                    'resources': [
                        {'title': 'Hugging Face Transformers', 'url': 'https://huggingface.co/docs/transformers/index'},
                        {'title': 'OpenAI Gym', 'url': 'https://gym.openai.com/docs/'},
                        {'title': 'Papers with Code', 'url': 'https://paperswithcode.com/'}
                    ],
                    'projects': ['Chatbot with transformer models', 'Object detection system', 'Recommendation engine']
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
        }
    }
    
    roadmap = detailed_roadmaps.get(domain, detailed_roadmaps['frontend'])
    return roadmap

@app.post("/download-roadmap")
def download_roadmap_pdf(request: dict):
    domain = request.get("domain", "frontend").lower()
    
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
@app.post("/roadmap")
def get_roadmap(request: dict):
    # Redirect to detailed roadmap
    return get_detailed_roadmap(request), 'One React mini project']
            },
            'week5': {
                'title': 'Week 5 – Polishing',
                'topics': ['APIs & fetch', 'Basic performance + clean UI', 'Final project + deploy (Netlify/Vercel)']
            }
        },
        'backend': {
            'week1': {
                'title': 'Week 1 – Server Fundamentals',
                'topics': ['HTTP protocols & REST principles', 'Node.js/Python basics', 'Build simple API endpoints']
            },
            'week2': {
                'title': 'Week 2 – Database Integration',
                'topics': ['SQL basics & database design', 'Connect API to database', 'CRUD operations implementation']
            },
            'week3': {
                'title': 'Week 3 – Authentication & Security',
                'topics': ['User authentication systems', 'JWT tokens & sessions', 'Password hashing & validation']
            },
            'week4': {
                'title': 'Week 4 – Advanced Features',
                'topics': ['File uploads & processing', 'Email services integration', 'API documentation with Swagger']
            },
            'week5': {
                'title': 'Week 5 – Deployment & Scaling',
                'topics': ['Cloud deployment (AWS/Heroku)', 'Environment configuration', 'Basic monitoring & logging']
            }
        },
        'data analytics': {
            'week1': {
                'title': 'Week 1 – Data Foundations',
                'topics': ['SQL fundamentals & queries', 'Excel/Google Sheets mastery', 'Basic statistical concepts']
            },
            'week2': {
                'title': 'Week 2 – Python for Data',
                'topics': ['Python basics & Pandas', 'Data cleaning & preprocessing', 'Jupyter notebook workflows']
            },
            'week3': {
                'title': 'Week 3 – Visualization & Analysis',
                'topics': ['Matplotlib & Seaborn charts', 'Statistical analysis techniques', 'Hypothesis testing basics']
            },
            'week4': {
                'title': 'Week 4 – Business Intelligence',
                'topics': ['Tableau/Power BI dashboards', 'KPI identification & tracking', 'Interactive report creation']
            },
            'week5': {
                'title': 'Week 5 – Real-world Projects',
                'topics': ['End-to-end analysis project', 'Presentation & storytelling', 'Portfolio development']
            }
        },
        'machine learning': {
            'week1': {
                'title': 'Week 1 – ML Fundamentals',
                'topics': ['Python & NumPy/Pandas', 'Supervised vs Unsupervised learning', 'Basic linear regression']
            },
            'week2': {
                'title': 'Week 2 – Core Algorithms',
                'topics': ['Classification algorithms', 'Decision trees & Random Forest', 'Model evaluation metrics']
            },
            'week3': {
                'title': 'Week 3 – Data Preprocessing',
                'topics': ['Feature engineering techniques', 'Handling missing data', 'Cross-validation methods']
            },
            'week4': {
                'title': 'Week 4 – Advanced Models',
                'topics': ['Neural networks basics', 'Scikit-learn & TensorFlow', 'Hyperparameter tuning']
            },
            'week5': {
                'title': 'Week 5 – Deployment & MLOps',
                'topics': ['Model deployment strategies', 'API creation for ML models', 'Monitoring model performance']
            }
        },
        'devops': {
            'week1': {
                'title': 'Week 1 – Version Control & CI/CD',
                'topics': ['Git advanced workflows', 'GitHub Actions basics', 'Automated testing setup']
            },
            'week2': {
                'title': 'Week 2 – Containerization',
                'topics': ['Docker fundamentals', 'Container orchestration', 'Multi-stage builds']
            },
            'week3': {
                'title': 'Week 3 – Cloud Infrastructure',
                'topics': ['AWS/Azure basics', 'Infrastructure as Code', 'Terraform fundamentals']
            },
            'week4': {
                'title': 'Week 4 – Monitoring & Security',
                'topics': ['Application monitoring', 'Log aggregation systems', 'Security best practices']
            },
            'week5': {
                'title': 'Week 5 – Production Deployment',
                'topics': ['Kubernetes basics', 'Load balancing & scaling', 'Disaster recovery planning']
            }
        },
        'cybersecurity': {
            'week1': {
                'title': 'Week 1 – Security Fundamentals',
                'topics': ['CIA Triad & risk assessment', 'Network security basics', 'Common attack vectors']
            },
            'week2': {
                'title': 'Week 2 – Ethical Hacking',
                'topics': ['Penetration testing basics', 'Vulnerability scanning tools', 'OWASP Top 10']
            },
            'week3': {
                'title': 'Week 3 – Network Security',
                'topics': ['Firewall configuration', 'Intrusion detection systems', 'Network monitoring']
            },
            'week4': {
                'title': 'Week 4 – Incident Response',
                'topics': ['Security incident handling', 'Digital forensics basics', 'Malware analysis']
            },
            'week5': {
                'title': 'Week 5 – Compliance & Governance',
                'topics': ['Security frameworks (ISO 27001)', 'Compliance auditing', 'Security awareness training']
            }
        },
        'data engineering': {
            'week1': {
                'title': 'Week 1 – Data Pipeline Basics',
                'topics': ['ETL concepts & design', 'Python for data processing', 'Database fundamentals']
            },
            'week2': {
                'title': 'Week 2 – Big Data Technologies',
                'topics': ['Apache Spark basics', 'Distributed computing concepts', 'Data formats (Parquet, Avro)']
            },
            'week3': {
                'title': 'Week 3 – Cloud Data Platforms',
                'topics': ['AWS/GCP data services', 'Data lakes vs warehouses', 'Serverless data processing']
            },
            'week4': {
                'title': 'Week 4 – Stream Processing',
                'topics': ['Real-time data processing', 'Apache Kafka basics', 'Event-driven architectures']
            },
            'week5': {
                'title': 'Week 5 – Data Quality & Monitoring',
                'topics': ['Data validation frameworks', 'Pipeline monitoring', 'Data governance practices']
            }
        },
        'algorithms': {
            'week1': {
                'title': 'Week 1 – Data Structures',
                'topics': ['Arrays, Linked Lists, Stacks, Queues', 'Time & Space complexity', 'Basic problem solving']
            },
            'week2': {
                'title': 'Week 2 – Sorting & Searching',
                'topics': ['Sorting algorithms comparison', 'Binary search variations', 'Hash tables & applications']
            },
            'week3': {
                'title': 'Week 3 – Trees & Graphs',
                'topics': ['Binary trees & traversals', 'Graph algorithms (BFS, DFS)', 'Tree-based problems']
            },
            'week4': {
                'title': 'Week 4 – Dynamic Programming',
                'topics': ['DP concepts & patterns', 'Memoization vs tabulation', 'Classic DP problems']
            },
            'week5': {
                'title': 'Week 5 – Advanced Topics',
                'topics': ['Greedy algorithms', 'Backtracking techniques', 'Competitive programming practice']
            }
        }
    }
    
    roadmap = roadmaps.get(domain, roadmaps['frontend'])
    
    return {
        "message": f"Here's your personalized 5-week {domain.title()} roadmap:",
        "roadmap": roadmap,
        "domain": domain.title()
    }

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
    
    # Handle general questions with documentation links
    if any(word in user_message for word in ['how', 'what', 'why', 'when', 'where', 'help', 'guide', 'tutorial']):
        return {
            "message": "That's a great question! For specific technical guidance, I recommend checking these official resources and documentation:",
            "docs": domain_docs.get(domain, domain_docs['frontend'])
        }
    
    # Default response with documentation links
    return {
        "message": "Thanks for your question! I'm here to help with your learning journey. Check out these official resources for detailed guidance:",
        "docs": domain_docs.get(domain, domain_docs['frontend'])
    }
