# AI GlueOps Intelligence Dashboard

An interactive **AWS Glue execution analytics and AI copilot dashboard** built with Streamlit, DuckDB, Plotly, Pandas, and a locally running Ollama model.

The application turns AWS Glue execution data into operational dashboards for **cost, runtime, failures, DPU consumption, application/business-unit analysis, and natural-language analytics**.

## Overview

AI GlueOps Intelligence is designed to make AWS Glue execution data easier to explore without requiring users to manually write SQL for every analytical question.

Users upload a Glue execution dataset, explore interactive dashboards, apply application/business-unit/environment filters, and ask questions in natural language. The AI copilot converts those questions into read-only DuckDB SQL, executes the query against the uploaded data, and summarizes the calculated result.

## Key Features

### Executive Dashboard
- Total Glue executions
- Success and failure rates
- Total execution cost
- Runtime and DPU consumption
- Job-status distribution
- Daily execution trends
- Top applications by cost
- Runtime distribution

### Cost Analytics
- Total, average, minimum, and maximum cost
- Top expensive Glue jobs
- Cost by business unit
- Cost by environment
- Daily cost trends

### Runtime Analytics
- Total and average runtime
- Minimum and maximum runtime
- Top longest-running jobs

### Failure Analytics
- Failed execution count
- Failure percentage
- Estimated wasted cost
- Lost runtime
- Wasted DPU calculation
- Detailed failed-job execution view

### AI Copilot
- Natural-language questions over Glue execution data
- Schema-aware SQL generation
- DuckDB-based local analytics
- Read-only query constraints
- Result-driven AI summaries
- Local Ollama inference
- No external LLM API required

## Architecture

```
                    Glue Execution Dataset
                     CSV / Excel / JSON
                            |
                            v
                    +---------------+
                    |   Streamlit   |
                    |    app.py     |
                    +-------+-------+
                            |
             +--------------+--------------+
             |                             |
             v                             v
      Analytics Dashboards           AI Copilot UI
      Plotly + Pandas               copilot_ui.py
                                           |
                                           v
                                    CopilotRouter
                                      router.py
                                           |
                                           |
                                           v
                                     Ollama / Qwen 2.5 
                                    Natural Language -> SQL
                                           |
                                           |
                                           v
                                          DuckDB
                                     Query Execution
                                           |
                                           |
                                           v
                                    Ollama / Qwen 2.5 
                                        Summary      
```

## Technology Stack

Frontend / Dashboard - Streamlit 
Data Processing -  Pandas 
Visualization - Plotly 
Analytical SQL Engine - DuckDB 
Local LLM Runtime - Ollama 
LLM Model - Qwen 2.5 3B 
Input Formats - CSV, XLSX, JSON 


`app.py` contains data loading, preprocessing, filtering, KPIs, and dashboard tabs.
`copilot_ui.py` provides the Streamlit chat interface.
`router.py` handles schema-aware prompt construction, natural-language-to-SQL generation, DuckDB execution, and AI result summarization.

## Prerequisites
- Python 3.10+ recommended
- Ollama installed and running locally
- Qwen 2.5 3B Ollama model

## Ollama Setup
Install Ollama from its official distribution for your operating system
Pull the model used by the application:
```bash
ollama pull qwen2.5:3b
```
Verify that the model is available:
```bash
ollama list
```
Make sure Ollama is running before starting the dashboard.
## Run the Application
```bash
streamlit run app.py
```
Open the local Streamlit URL displayed in the terminal, then upload a supported Glue execution dataset.


## Example AI Questions
Try questions such as:
```text
Give me an overall summary of Glue executions.
Which applications have the highest total cost?
Which business unit has the highest failure rate?
Show the top 10 longest-running jobs.
How much cost was wasted on unsuccessful executions?
Which jobs are expensive and unreliable?
What percentage of total cost comes from unsuccessful executions?
Compare DPU consumption by environment.
Which application should we investigate based on failures?
Show the daily cost trend.
```
More examples are available in `sample_questions.md`.

## How the AI Copilot Works
1. The uploaded dataset is registered as a DuckDB table named `glue_jobs`.
2. The router builds a prompt containing the actual dataframe schema and representative categorical values.
3. Ollama converts the user's analytical question into one read-only DuckDB query.
4. DuckDB executes the generated SQL locally.
5. The resulting dataframe is displayed in the application.
6. Ollama produces a concise explanation based only on the calculated result.
The SQL-generation prompt explicitly restricts the model from inventing tables or columns and from generating destructive SQL operations.

## Current Scope
This project focuses on analytical exploration of uploaded Glue execution data. AI-generated SQL can occasionally be imperfect, so results should be validated before using them for production or financial decisions.
