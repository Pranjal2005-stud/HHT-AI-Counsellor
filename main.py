from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uuid
import json
import os

from state import ConversationState, ConversationStage
from state_controller import StateController
from engine import update_score, should_repeat

app = FastAPI()

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
    
    # Questions and explanations for each domain
    domain_questions = {
        'frontend': [
            {"q": "Do you have experience with frontend development?", "exp": "Frontend development is the practice of creating user interfaces and user experiences for web applications. It involves writing code that runs in web browsers and directly interacts with users. Frontend developers work with HTML for structure, CSS for styling, and JavaScript for interactivity. This field requires understanding of responsive design principles, browser compatibility, and user experience best practices. Modern frontend development also involves working with frameworks like React, Vue, or Angular to build complex, interactive applications."},
            {"q": "Have you worked with React, Vue, or Angular?", "exp": "React, Vue, and Angular are the three most popular JavaScript frameworks for building modern web applications. React, developed by Facebook, uses a component-based architecture and virtual DOM for efficient rendering. Vue.js is known for its gentle learning curve and progressive adoption approach. Angular, maintained by Google, is a full-featured framework with TypeScript by default. These frameworks help developers build scalable, maintainable applications by providing structured ways to manage state, handle user interactions, and organize code into reusable components."},
            {"q": "Do you understand responsive design principles?", "exp": "Responsive design is a web development approach that ensures websites work seamlessly across all devices and screen sizes. It involves using flexible grid layouts, fluid images, and CSS media queries to adapt content presentation. Key principles include mobile-first design, flexible layouts using percentages instead of fixed pixels, and progressive enhancement. Understanding responsive design means knowing how to create layouts that look great on smartphones, tablets, laptops, and desktop computers. This skill is essential in today's multi-device world where users access websites from various screen sizes."},
            {"q": "Are you familiar with CSS preprocessors like Sass or Less?", "exp": "CSS preprocessors like Sass (Syntactically Awesome Style Sheets) and Less extend CSS with programming features such as variables, nesting, mixins, and functions. These tools help developers write more maintainable and organized stylesheets by allowing code reuse and better structure. Sass offers features like partials for modular CSS, mathematical operations, and control directives. Learning preprocessors significantly improves CSS workflow efficiency and helps manage large-scale styling projects. They compile into regular CSS that browsers can understand, making them powerful development tools."},
            {"q": "Have you used build tools like Webpack or Vite?", "exp": "Build tools like Webpack and Vite are essential for modern frontend development workflows. Webpack is a module bundler that processes and optimizes JavaScript, CSS, images, and other assets for production deployment. It handles tasks like code splitting, minification, and asset optimization. Vite is a newer, faster build tool that provides instant server start and lightning-fast hot module replacement during development. These tools automate repetitive tasks, optimize code for performance, and enable developers to use modern JavaScript features while maintaining browser compatibility."},
            {"q": "Do you know about web performance optimization?", "exp": "Web performance optimization involves techniques to make websites load faster and run more efficiently. This includes optimizing images through compression and modern formats like WebP, implementing lazy loading for images and content, minimizing and compressing CSS and JavaScript files, and using content delivery networks (CDNs). Performance optimization also covers code splitting to load only necessary code, caching strategies, and reducing the number of HTTP requests. Understanding performance metrics like Core Web Vitals and using tools like Lighthouse helps developers create faster, more user-friendly web experiences."}
        ],
        'backend': [
            {"q": "Do you have experience with backend development?", "exp": "Backend development involves creating server-side applications that handle business logic, database operations, and API endpoints. Backend developers work with server technologies, databases, and cloud services to build the infrastructure that powers web and mobile applications. This includes designing database schemas, implementing authentication and authorization systems, handling data processing, and ensuring application security. Backend development requires understanding of server architectures, API design principles, and how to build scalable, maintainable systems that can handle multiple users and large amounts of data."},
            {"q": "Have you worked with databases like MySQL or PostgreSQL?", "exp": "MySQL and PostgreSQL are powerful relational database management systems used to store and retrieve application data. MySQL is known for its speed and reliability, making it popular for web applications and content management systems. PostgreSQL offers advanced features like JSON support, full-text search, and complex data types, making it suitable for complex applications. Working with these databases involves understanding SQL queries, database design principles, indexing for performance, and data relationships. Knowledge of database optimization, backup strategies, and security practices is essential for building robust backend systems."},
            {"q": "Are you familiar with REST API development?", "exp": "REST (Representational State Transfer) APIs are a standard way for different software applications to communicate over the internet. REST APIs use HTTP methods (GET, POST, PUT, DELETE) to perform operations on resources identified by URLs. Understanding REST involves knowing how to design clean, intuitive API endpoints, handle different HTTP status codes, implement proper error handling, and structure JSON responses. REST API development also includes authentication mechanisms, rate limiting, documentation practices, and versioning strategies. These APIs enable frontend applications, mobile apps, and third-party services to interact with backend systems."},
            {"q": "Do you understand authentication and authorization?", "exp": "Authentication and authorization are critical security concepts in backend development. Authentication verifies user identity through methods like username/password, OAuth, or multi-factor authentication. Authorization determines what authenticated users can access or do within the application. This involves implementing role-based access control (RBAC), permission systems, and secure session management. Understanding includes working with JWT tokens, password hashing, secure cookie handling, and protecting against common security vulnerabilities like CSRF and XSS attacks. Proper implementation ensures that only authorized users can access sensitive data and functionality."},
            {"q": "Have you used cloud services like AWS or Azure?", "exp": "Cloud platforms like Amazon Web Services (AWS) and Microsoft Azure provide scalable infrastructure and services for deploying backend applications. These platforms offer compute resources (EC2, Azure VMs), databases (RDS, Azure SQL), storage solutions (S3, Azure Blob), and managed services for authentication, messaging, and monitoring. Understanding cloud services involves knowing how to deploy applications, configure auto-scaling, set up load balancers, and manage costs. Cloud knowledge also includes understanding serverless computing, containerization with Docker and Kubernetes, and implementing CI/CD pipelines for automated deployment."},
            {"q": "Do you know about microservices architecture?", "exp": "Microservices architecture is a design approach where applications are built as a collection of small, independent services that communicate over well-defined APIs. Each microservice handles a specific business function and can be developed, deployed, and scaled independently. This architecture offers benefits like technology diversity, fault isolation, and easier maintenance. Understanding microservices involves knowing about service discovery, API gateways, distributed data management, and handling challenges like network latency and data consistency. It also requires knowledge of containerization, orchestration tools, and monitoring distributed systems."}
        ],
        'data analytics': [
            {"q": "Do you have experience with data analytics?", "exp": "Data analytics involves examining datasets to draw conclusions about the information they contain. It encompasses collecting, cleaning, processing, and analyzing data to discover useful insights for business decision-making. Data analysts work with statistical methods, visualization tools, and programming languages like Python or R to identify patterns, trends, and correlations in data. This field requires understanding of statistical concepts, data visualization principles, and domain knowledge to interpret results meaningfully. Modern data analytics also involves working with big data technologies and machine learning techniques."},
            {"q": "Have you worked with SQL for data querying?", "exp": "SQL (Structured Query Language) is the standard language for managing and querying relational databases in data analytics. It allows analysts to extract, filter, aggregate, and manipulate data from databases efficiently. Advanced SQL skills include writing complex joins, subqueries, window functions, and stored procedures. Understanding SQL involves knowing how to optimize queries for performance, work with different database systems, and handle various data types. SQL is fundamental for data analysts as most organizational data is stored in relational databases, making it essential for data extraction and analysis workflows."},
            {"q": "Are you familiar with data visualization tools like Tableau or Power BI?", "exp": "Data visualization tools like Tableau and Power BI enable analysts to create interactive dashboards, charts, and reports that make data insights accessible to stakeholders. These tools allow for drag-and-drop interface creation, real-time data connections, and advanced analytics features. Understanding these platforms involves knowing how to design effective visualizations, create calculated fields, implement filters and parameters, and build user-friendly dashboards. Effective data visualization requires understanding of design principles, color theory, and how to choose appropriate chart types for different data stories."},
            {"q": "Do you understand statistical analysis and hypothesis testing?", "exp": "Statistical analysis and hypothesis testing are fundamental concepts in data analytics for making data-driven decisions and validating assumptions. This involves understanding descriptive statistics (mean, median, standard deviation), probability distributions, confidence intervals, and various statistical tests (t-tests, chi-square, ANOVA). Hypothesis testing helps determine if observed differences or relationships in data are statistically significant or due to random chance. Knowledge includes understanding p-values, Type I and Type II errors, and choosing appropriate statistical methods based on data types and research questions."},
            {"q": "Have you used Python or R for data analysis?", "exp": "Python and R are powerful programming languages specifically designed for data analysis and statistical computing. Python offers libraries like Pandas for data manipulation, NumPy for numerical computing, Matplotlib and Seaborn for visualization, and Scikit-learn for machine learning. R provides comprehensive statistical packages, excellent data visualization capabilities with ggplot2, and specialized libraries for various analytical techniques. Understanding these languages involves knowing how to clean and transform data, perform statistical analysis, create visualizations, and automate analytical workflows through scripting."},
            {"q": "Do you know about data cleaning and preprocessing techniques?", "exp": "Data cleaning and preprocessing are crucial steps in the analytics pipeline, often consuming 70-80% of an analyst's time. This involves identifying and handling missing values, removing duplicates, correcting inconsistencies, and standardizing data formats. Preprocessing techniques include data normalization, encoding categorical variables, handling outliers, and feature engineering. Understanding these processes requires knowledge of data quality assessment, various imputation methods, and the impact of data quality on analysis results. Proper data cleaning ensures accurate and reliable analytical outcomes."}
        ],
        'machine learning': [
            {"q": "Do you have experience with machine learning?", "exp": "Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed for every scenario. It involves training algorithms on datasets to recognize patterns and make predictions on new, unseen data. ML encompasses supervised learning (classification and regression), unsupervised learning (clustering and dimensionality reduction), and reinforcement learning. Understanding machine learning requires knowledge of statistical concepts, programming skills, and domain expertise to select appropriate algorithms and interpret results effectively."},
            {"q": "Are you familiar with supervised learning algorithms?", "exp": "Supervised learning algorithms learn from labeled training data to make predictions on new data. Common algorithms include linear and logistic regression for prediction and classification, decision trees for interpretable models, random forests for ensemble learning, and support vector machines for complex decision boundaries. Neural networks and deep learning models are also supervised learning approaches. Understanding supervised learning involves knowing when to use each algorithm, how to prepare training data, evaluate model performance using metrics like accuracy and F1-score, and avoid overfitting through techniques like cross-validation."},
            {"q": "Have you worked with popular ML libraries like scikit-learn or TensorFlow?", "exp": "Scikit-learn and TensorFlow are essential libraries for machine learning implementation. Scikit-learn provides user-friendly implementations of classical ML algorithms, data preprocessing tools, and model evaluation metrics, making it ideal for traditional machine learning tasks. TensorFlow is Google's framework for building and training neural networks and deep learning models, offering both high-level APIs (Keras) and low-level operations. Understanding these libraries involves knowing how to implement ML pipelines, tune hyperparameters, handle different data types, and deploy models for production use."},
            {"q": "Do you understand model evaluation and validation techniques?", "exp": "Model evaluation and validation are critical for assessing machine learning model performance and ensuring reliability. This includes understanding train-validation-test splits, cross-validation techniques, and various evaluation metrics for different problem types (accuracy, precision, recall, F1-score for classification; MSE, MAE, R² for regression). Advanced techniques include learning curves, validation curves, and statistical significance testing. Proper evaluation helps detect overfitting, underfitting, and bias in models, ensuring they generalize well to new data and perform reliably in production environments."},
            {"q": "Are you familiar with feature engineering and selection?", "exp": "Feature engineering involves creating new features from existing data to improve model performance, while feature selection identifies the most relevant features for the prediction task. Techniques include creating polynomial features, binning continuous variables, encoding categorical data, and extracting features from text or images. Feature selection methods include statistical tests, recursive feature elimination, and regularization techniques like Lasso. Understanding feature engineering requires domain knowledge, creativity, and understanding of how different algorithms respond to various feature types and scales."},
            {"q": "Have you deployed machine learning models in production?", "exp": "Model deployment involves making trained machine learning models available for real-world use through APIs, web services, or embedded systems. This includes model serialization, creating prediction endpoints, handling real-time and batch predictions, and monitoring model performance over time. Deployment considerations include scalability, latency requirements, model versioning, and handling concept drift. Understanding deployment involves knowledge of cloud platforms, containerization with Docker, API development, and MLOps practices for continuous integration and delivery of ML systems."}
        ],
        'devops': [
            {"q": "Do you have experience with DevOps practices?", "exp": "DevOps is a cultural and technical movement that combines software development (Dev) and IT operations (Ops) to shorten development cycles and deliver high-quality software continuously. It emphasizes collaboration, automation, monitoring, and shared responsibility between development and operations teams. DevOps practices include continuous integration/continuous deployment (CI/CD), infrastructure as code, automated testing, and monitoring. Understanding DevOps requires knowledge of various tools, cloud platforms, and methodologies that enable faster, more reliable software delivery while maintaining system stability and security."},
            {"q": "Are you familiar with containerization using Docker?", "exp": "Docker is a containerization platform that packages applications and their dependencies into lightweight, portable containers. Containers ensure consistent environments across development, testing, and production systems, solving the 'it works on my machine' problem. Docker involves understanding images, containers, Dockerfiles for building custom images, and Docker Compose for multi-container applications. Containerization benefits include improved resource utilization, faster deployment, easier scaling, and better isolation between applications. Knowledge includes container orchestration, security best practices, and integration with CI/CD pipelines."},
            {"q": "Have you worked with cloud platforms like AWS, Azure, or GCP?", "exp": "Cloud platforms like Amazon Web Services (AWS), Microsoft Azure, and Google Cloud Platform (GCP) provide on-demand computing resources and services for building, deploying, and scaling applications. These platforms offer compute instances, storage solutions, databases, networking, and managed services for various use cases. Understanding cloud platforms involves knowing how to provision resources, configure networking and security, implement auto-scaling, and manage costs. Cloud knowledge also includes understanding different service models (IaaS, PaaS, SaaS) and deployment strategies for high availability and disaster recovery."},
            {"q": "Do you understand CI/CD pipeline implementation?", "exp": "Continuous Integration/Continuous Deployment (CI/CD) pipelines automate the process of building, testing, and deploying software changes. CI involves automatically building and testing code changes when developers commit to version control, ensuring early detection of integration issues. CD extends this by automatically deploying tested changes to staging and production environments. Understanding CI/CD involves knowledge of version control systems, automated testing strategies, build tools, deployment automation, and pipeline orchestration tools like Jenkins, GitLab CI, or GitHub Actions. Proper CI/CD implementation reduces manual errors and accelerates software delivery."},
            {"q": "Are you familiar with infrastructure as code (IaC) tools?", "exp": "Infrastructure as Code (IaC) treats infrastructure provisioning and management as software development, using code to define and manage infrastructure resources. Tools like Terraform, AWS CloudFormation, and Ansible enable declarative infrastructure definition, version control of infrastructure changes, and automated provisioning. IaC benefits include consistency, repeatability, scalability, and the ability to track infrastructure changes over time. Understanding IaC involves knowing how to write infrastructure templates, manage state, handle dependencies, and implement infrastructure testing and validation practices."},
            {"q": "Have you implemented monitoring and logging solutions?", "exp": "Monitoring and logging are essential for maintaining system health, performance, and security in production environments. Monitoring involves collecting metrics on system performance, application behavior, and user experience, while logging captures detailed event information for debugging and auditing. Tools include Prometheus for metrics collection, ELK stack (Elasticsearch, Logstash, Kibana) for log management, and Grafana for visualization. Understanding monitoring involves setting up alerting systems, defining SLAs/SLOs, implementing distributed tracing, and creating dashboards that provide actionable insights for system optimization and incident response."}
        ],
        'cybersecurity': [
            {"q": "Do you have experience with cybersecurity fundamentals?", "exp": "Cybersecurity involves protecting digital systems, networks, and data from cyber threats and attacks. It encompasses understanding various attack vectors, security frameworks, risk assessment, and defense strategies. Fundamental concepts include the CIA triad (Confidentiality, Integrity, Availability), defense in depth, threat modeling, and security by design. Cybersecurity professionals must understand both technical and non-technical aspects, including human factors, compliance requirements, and business impact of security decisions. The field requires continuous learning due to evolving threats and technologies."},
            {"q": "Are you familiar with network security and firewalls?", "exp": "Network security involves protecting network infrastructure and data transmission from unauthorized access, attacks, and breaches. Firewalls are critical components that control network traffic based on predetermined security rules, acting as barriers between trusted and untrusted networks. Understanding network security includes knowledge of network protocols, intrusion detection/prevention systems (IDS/IPS), VPNs, network segmentation, and wireless security. Advanced topics include next-generation firewalls, network access control (NAC), and software-defined perimeter (SDP) technologies for modern network protection."},
            {"q": "Have you worked with vulnerability assessment and penetration testing?", "exp": "Vulnerability assessment and penetration testing are proactive security practices used to identify and evaluate security weaknesses in systems and applications. Vulnerability assessments involve systematic scanning and analysis to discover known vulnerabilities, while penetration testing simulates real-world attacks to exploit vulnerabilities and assess their impact. These practices require knowledge of security tools like Nessus, Nmap, Metasploit, and Burp Suite, understanding of common vulnerabilities (OWASP Top 10), and methodologies like PTES or OWASP Testing Guide. Results help organizations prioritize security improvements and validate security controls."},
            {"q": "Do you understand incident response and forensics?", "exp": "Incident response involves systematic approaches to handling security breaches, cyber attacks, and other security incidents to minimize damage and recovery time. This includes preparation, identification, containment, eradication, recovery, and lessons learned phases. Digital forensics involves collecting, preserving, and analyzing digital evidence from security incidents for investigation and legal purposes. Understanding these areas requires knowledge of forensic tools, chain of custody procedures, malware analysis, log analysis, and coordination with legal and law enforcement agencies when necessary."},
            {"q": "Are you familiar with security compliance frameworks?", "exp": "Security compliance frameworks provide structured approaches to implementing and maintaining security controls to meet regulatory, industry, or organizational requirements. Common frameworks include ISO 27001 for information security management, NIST Cybersecurity Framework for risk management, SOC 2 for service organizations, and PCI DSS for payment card security. Understanding compliance involves knowing how to conduct risk assessments, implement appropriate controls, maintain documentation, and undergo audits. Compliance frameworks help organizations establish baseline security practices and demonstrate due diligence to stakeholders and regulators."},
            {"q": "Have you implemented security awareness and training programs?", "exp": "Security awareness and training programs educate employees about cybersecurity threats, best practices, and their role in maintaining organizational security. These programs address topics like phishing recognition, password security, social engineering, data handling, and incident reporting. Effective programs include regular training sessions, simulated phishing exercises, security newsletters, and metrics to measure effectiveness. Understanding this area involves knowledge of adult learning principles, behavior change techniques, and how to create engaging content that translates to improved security behaviors. Human factors are often the weakest link in security, making awareness programs critical."}
        ],
        'data engineering': [
            {"q": "Do you have experience with data engineering?", "exp": "Data engineering involves designing, building, and maintaining systems that collect, store, process, and serve data at scale. Data engineers create data pipelines that transform raw data into formats suitable for analysis and machine learning. This field requires understanding of distributed systems, data modeling, ETL/ELT processes, and various data storage technologies. Data engineers work with both batch and real-time data processing, ensuring data quality, reliability, and performance. The role bridges software engineering and data science, requiring strong programming skills and understanding of data architecture patterns."},
            {"q": "Are you familiar with big data technologies like Hadoop or Spark?", "exp": "Apache Hadoop and Spark are foundational technologies for processing large-scale datasets that exceed the capacity of traditional databases. Hadoop provides distributed storage (HDFS) and processing (MapReduce) across clusters of computers, while Spark offers faster in-memory processing for iterative algorithms and interactive queries. Understanding these technologies involves knowledge of distributed computing concepts, cluster management, data partitioning, and fault tolerance. Modern data engineering often uses Spark for its versatility in batch processing, stream processing, machine learning, and graph processing workloads."},
            {"q": "Have you built ETL/ELT data pipelines?", "exp": "ETL (Extract, Transform, Load) and ELT (Extract, Load, Transform) pipelines are core data engineering processes for moving and transforming data between systems. ETL transforms data before loading into the target system, while ELT loads raw data first and transforms it in the target system. Building pipelines involves data extraction from various sources, implementing transformation logic for data cleaning and enrichment, handling data quality issues, and ensuring reliable data delivery. Modern pipeline tools include Apache Airflow, Luigi, and cloud-native services that provide workflow orchestration and monitoring capabilities."},
            {"q": "Do you understand data warehousing and data lake concepts?", "exp": "Data warehouses and data lakes are different approaches to storing and organizing large amounts of data for analytics. Data warehouses use structured, schema-on-write approaches with predefined data models optimized for specific analytical queries. Data lakes store raw data in its native format using schema-on-read approaches, providing flexibility for various analytical use cases. Understanding these concepts involves knowledge of dimensional modeling, data partitioning strategies, data governance, and when to use each approach. Modern architectures often combine both approaches in lakehouse patterns that provide the benefits of both systems."},
            {"q": "Are you familiar with stream processing and real-time data?", "exp": "Stream processing involves analyzing and processing data in real-time as it flows through systems, enabling immediate insights and responses to events. Technologies like Apache Kafka for messaging, Apache Storm, Apache Flink, and Spark Streaming enable real-time data processing at scale. Understanding stream processing involves concepts like event time vs. processing time, windowing operations, exactly-once processing guarantees, and handling late-arriving data. Real-time data processing is crucial for applications like fraud detection, recommendation systems, IoT analytics, and monitoring systems that require immediate responses to data changes."},
            {"q": "Have you worked with cloud data services?", "exp": "Cloud data services provide managed solutions for various data engineering tasks, reducing operational overhead and enabling scalable data processing. Services include data warehouses (Amazon Redshift, Google BigQuery, Azure Synapse), data lakes (Amazon S3, Azure Data Lake), ETL services (AWS Glue, Azure Data Factory), and streaming platforms (Amazon Kinesis, Azure Event Hubs). Understanding cloud data services involves knowing how to architect data solutions using managed services, optimize costs, implement security and governance, and integrate different services to build comprehensive data platforms."}
        ],
        'algorithms': [
            {"q": "Do you have experience with algorithms and data structures?", "exp": "Algorithms and data structures form the foundation of computer science and software engineering. Algorithms are step-by-step procedures for solving computational problems, while data structures organize and store data efficiently. Understanding this field involves knowing how to analyze algorithm complexity using Big O notation, implement fundamental data structures (arrays, linked lists, trees, graphs), and apply appropriate algorithms for different problem types. This knowledge is essential for writing efficient code, solving complex programming challenges, and succeeding in technical interviews at technology companies."},
            {"q": "Are you familiar with sorting and searching algorithms?", "exp": "Sorting and searching algorithms are fundamental building blocks in computer science used to organize and retrieve data efficiently. Common sorting algorithms include bubble sort, merge sort, quick sort, and heap sort, each with different time and space complexity characteristics. Searching algorithms include linear search, binary search, and hash-based lookups. Understanding these algorithms involves knowing their implementation, complexity analysis, and when to use each approach. These concepts are crucial for optimizing application performance and are frequently tested in coding interviews and competitive programming."},
            {"q": "Have you solved problems using dynamic programming?", "exp": "Dynamic programming is an algorithmic technique for solving complex problems by breaking them down into simpler subproblems and storing solutions to avoid redundant calculations. It's particularly useful for optimization problems with overlapping subproblems and optimal substructure properties. Classic examples include the knapsack problem, longest common subsequence, and Fibonacci sequence optimization. Understanding dynamic programming involves recognizing when to apply it, designing state representations, and implementing both top-down (memoization) and bottom-up (tabulation) approaches. This technique is essential for solving many algorithmic challenges efficiently."},
            {"q": "Do you understand graph algorithms and tree traversals?", "exp": "Graph algorithms and tree traversals are essential for solving problems involving relationships and hierarchical data structures. Graph algorithms include breadth-first search (BFS), depth-first search (DFS), shortest path algorithms (Dijkstra's, Bellman-Ford), and minimum spanning tree algorithms (Kruskal's, Prim's). Tree traversals include in-order, pre-order, and post-order traversals for binary trees. Understanding these concepts involves knowing how to represent graphs and trees, implement traversal algorithms, and apply them to solve real-world problems like social network analysis, route planning, and decision trees."},
            {"q": "Are you familiar with time and space complexity analysis?", "exp": "Time and space complexity analysis involves evaluating how algorithm performance scales with input size, typically expressed using Big O notation. Time complexity measures how execution time grows with input size, while space complexity measures memory usage growth. Understanding complexity analysis involves recognizing common patterns (O(1), O(log n), O(n), O(n²), O(2ⁿ)), analyzing loops and recursive calls, and comparing algorithm efficiency. This knowledge is crucial for choosing appropriate algorithms, optimizing code performance, and making informed decisions about trade-offs between time and space efficiency in software development."},
            {"q": "Have you participated in competitive programming or coding contests?", "exp": "Competitive programming involves solving algorithmic problems under time constraints, typically in contests like ACM ICPC, Codeforces, or LeetCode competitions. It requires quick problem analysis, efficient algorithm implementation, and strong debugging skills. Competitive programming helps develop pattern recognition for common problem types, improves coding speed and accuracy, and builds confidence in handling complex algorithmic challenges. Experience in competitive programming demonstrates strong problem-solving abilities and is highly valued by technology companies for technical roles, as it indicates proficiency in algorithms, data structures, and coding under pressure."}
        ]
    }
    
    # Get questions for current domain (fallback to generic if domain not found)
    questions = domain_questions.get(state.selected_domain, [
        {"q": f"Do you have experience with {state.selected_domain}?", "exp": f"This involves working with {state.selected_domain} technologies and concepts."},
        {"q": f"Have you built projects in {state.selected_domain}?", "exp": f"Practical experience building {state.selected_domain} projects is valuable for skill development."},
        {"q": f"Are you familiar with {state.selected_domain} best practices?", "exp": f"Best practices help ensure code quality, maintainability, and performance in {state.selected_domain}."},
        {"q": f"Do you understand {state.selected_domain} testing?", "exp": f"Testing ensures your {state.selected_domain} code works correctly and prevents bugs in production."},
        {"q": f"Have you worked with {state.selected_domain} tools?", "exp": f"Tools and frameworks make {state.selected_domain} development more efficient and productive."},
        {"q": f"Do you know {state.selected_domain} deployment?", "exp": f"Deployment involves making your {state.selected_domain} applications available to users in production environments."}
    ])
    
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

@app.post("/roadmap")
def get_roadmap(request: dict):
    if request.get("session_id") not in sessions:
        return {"message": "Session not found"}
    
    state = sessions[request["session_id"]]
    domain = getattr(state, 'selected_domain', 'frontend')
    
    # 5-week roadmaps for each domain
    roadmaps = {
        'frontend': {
            'week1': {
                'title': 'Week 1 – Basics',
                'topics': ['HTML5 (semantic tags, forms)', 'CSS3 (box model, flexbox, basics of grid)', 'Build 2 static pages']
            },
            'week2': {
                'title': 'Week 2 – Responsive UI',
                'topics': ['Advanced CSS (grid, media queries)', 'Mobile-first design', 'One fully responsive website']
            },
            'week3': {
                'title': 'Week 3 – JavaScript Core',
                'topics': ['JS basics (variables, loops, functions)', 'DOM manipulation, events', 'Build small interactive apps (todo, calculator)']
            },
            'week4': {
                'title': 'Week 4 – Modern Frontend',
                'topics': ['Git & GitHub', 'React basics (components, props, state)', 'One React mini project']
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
                "message": f"To improve your {state.selected_domain} skills, I recommend focusing on: {', '.join(tips)}. Start with hands-on projects and practice regularly!"
            }
    
    # Handle general questions
    if any(word in user_message for word in ['how', 'what', 'why', 'when', 'where']):
        return {
            "message": "That's a great question! For specific technical guidance, I recommend checking official documentation, online tutorials, or joining developer communities. Is there a particular area you'd like to focus on?"
        }
    
    # Default response
    return {
        "message": "Thanks for your question! I'm here to help with your learning journey. Feel free to ask about improving your skills, learning resources, or career advice."
    }
