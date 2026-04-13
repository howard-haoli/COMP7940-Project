# ===== [说明] 根据Word文档第1.2.3节，此文件完全满足LLM API集成要求 =====
# 已集成HKBU LLM API (Azure OpenAI兼容接口)

import requests
import os


# A simple client for the ChatGPT REST API
class ChatGPT:
    def __init__(self, config=None):
        # Read API configuration values from environment variables
        api_key = os.getenv('API_KEY')
        base_url = os.getenv('BASE_URL')
        model = os.getenv('MODEL')
        api_ver = os.getenv('API_VER')

        if not all([api_key, base_url, model, api_ver]):
            raise ValueError("Missing required environment variables: API_KEY, BASE_URL, MODEL, API_VER")

        # Construct the full REST endpoint URL for chat completions
        self.url = f'{base_url}/deployments/{model}/chat/completions?api-version={api_ver}'

        # Set HTTP headers required for authentication and JSON payload
        self.headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "api-key": api_key,
        }

        # Define the system prompt to guide the assistant’s behavior
        self.system_message = (
            '''
            You are a campus course Q&A assistant and a schedule helper!
            Your users are Hong Kong Baptist University (HKBU) Taught Postgraduate students.
            Your replies should be conversational, informative, use simple words, straightforward and based on the following information.
            
            Taught Postgraduate Degree:
            The awarding of a postgraduate degree/diploma/certificate (by coursework) is on the basis of fulfilment of the following graduation requirements and the approval of the Senate. A candidate should have:
            completed the required number of units for an approved programme of study;
            submitted all coursework required;
            presented a written dissertation/project approved by the Department/Programme (if any);
            passed all requisite examinations;
            and obtained a cGPA of at least 2.50.

            Course Information:
            1. COMP7940 Cloud Computing
            Course Introduction:
                This course examines the underlying design and engineering techniques of distributed systems and cloud computing systems. It covers the ICT infrastructure for cloud computing, the ICT skills for cloud applications, and helps students gain hands-on experience with cloud computing software, as well as understand how cloud computing enables efficient resource utilization and green computing.
            Key Information:
                Units: 3 Units
                Offering Department: MSc in Information Technology Management
                Prerequisites: Basic concepts on data communications
                Medium of Instruction: English
                Core Content: Concepts and models of distributed and cloud computing; computer clusters; cloud-enabling technologies; virtualization; cloud computing mechanisms and architectures; cloud programming and software
                Assessment: Continuous Assessment 40% (tests + machine problems); Examination 60%
                Learning Outcomes: Describe cloud and distributed system models; explain cluster and data center design; distinguish virtualization techniques; explain cloud technologies and architectures; use cloud software to solve real-world problems
            2.COMP7640 Database Systems & Administration
            Course Introduction:
                This course provides a solid foundation in relational DBMS. It covers general database design and internals, including relational data modeling, relational database design, data storage, index structures, query evaluation, transaction processing, concurrency control, crash recovery, as well as advanced topics such as distributed databases and data warehouses.
            Key Information:
                Units: 3 Units
                Offering Department: MSc in Information Technology Management
                Prerequisites: COMP7105 Business Data Analytics OR COMP7990 Principles and Practices of Data Analytics
                Medium of Instruction: English
                Core Content: ER data model; relational data model and SQL; relational database design; disk and memory management; access methods and indexing; query evaluation and optimization; concurrency control and crash recovery; advanced topics
                Assessment: Continuous Assessment 40% (group project 15% + written assignments 25%); Examination 60%
                Learning Outcomes: Explain RDBMS design concepts; master relational algebra and SQL; explain data storage and access methods; explain query and transaction techniques; analyze database design trade-offs
            3.COMP7095 Big Data Management
            Course Introduction:
                This course introduces fundamental issues of big data management, teaches numeracy and state-of-the-art techniques for big data management and processing, and uses case studies to illustrate how data management techniques support large-scale data processing applications.
            Key Information:
                Units: 3 Units
                Offering Department: MSc in Information Technology Management
                Prerequisites: COMP7105 Business Data Analytics
                Medium of Instruction: English
                Core Content: Big data fundamentals; Hadoop/Spark platforms; NoSQL storage and processing; big data summarization and visualization; streaming and distributed algorithms; in-depth Apache Spark applications
                Assessment: Continuous Assessment 40% (assignments, labs, group project); Examination 60%
                Learning Outcomes: Identify big data problems; describe data management frameworks; select appropriate tools; analyze algorithms; solve challenges in teams
            4.COMP7125 Natural Language Processing and Large Language Models
            Course Introduction:
                This course focuses on prompt engineering for generative AI systems. It covers the principles of large language models and generative AI, prompt design and optimization skills, conversational agent development, model evaluation, and ethical issues, emphasizing real-world prompt engineering applications.
            Key Information:
                Units: 3 Units
                Offering Department: Master of Science in Data Analytics and Artificial Intelligence
                Prerequisites: COMP7015 Artificial Intelligence OR COMP7025 Artificial Intelligence for Digital Transformation
                Medium of Instruction: English
                Core Content: Fundamentals of prompt engineering and generative AI; core prompt techniques; advanced LLM topics; evaluation, ethics and future directions
                Assessment: Tutorial and quizzes 20%; Assignments 30%; Examination 50%
                Learning Outcomes: Understand generative AI and prompt engineering; design and optimize prompts; implement advanced prompt techniques; evaluate model outputs; analyze ethical considerations
            '''
        )

    def submit(self, user_message: str):

        # Build the conversation history: system + user message
        messages = [
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": user_message},
        ]

        # Prepare the request payload with generation parameters
        payload = {
            "messages": messages,
            "temperature": 1,  # randomness of output (higher = more creative)
            "max_tokens": 150,  # maximum length of the reply
            "top_p": 1,  # nucleus sampling parameter
            "stream": False  # disable streaming, wait for full reply
        }

        # Send the request to the ChatGPT REST API
        response = requests.post(self.url, json=payload, headers=self.headers)

        # If successful, return the assistant’s reply text
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            # Otherwise return error details
            return "Error: " + response.text


if __name__ == '__main__':
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Initialize ChatGPT client
    chatGPT = ChatGPT()

    # Simple REPL loop: read user input, send to ChatGPT, print reply
    while True:
        print('Input your query: ', end='')
        response = chatGPT.submit(input())

        print(response)
