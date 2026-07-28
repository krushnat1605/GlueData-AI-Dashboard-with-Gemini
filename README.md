# AI GlueOps Intelligence Dashboard

An interactive **AWS Glue execution analytics and AI copilot dashboard** built with Streamlit, Google Gemini, DuckDB, Plotly, Pandas, and a locally running Ollama model.

The application transforms AWS Glue execution data into operational intelligence across **cost, runtime, failures, DPU consumption, applications, business units, environments, and job reliability**.

It also provides an AI-powered natural-language analytics interface where users can ask questions about their Glue execution data without manually writing SQL.

---

## Overview

**AI GlueOps Intelligence** is designed to simplify operational and FinOps analysis of AWS Glue workloads.

Users can upload Glue execution data, explore interactive dashboards, filter workloads by application, business unit, and environment, and ask analytical questions in natural language.

The AI Copilot uses **Google Gemini for natural-language-to-DuckDB SQL generation**, executes the generated query locally using DuckDB, and then uses a **local Ollama/Qwen model** to explain the calculated results.

This hybrid architecture keeps large dataset processing local while using Gemini only for SQL generation.

---

## Key Features

### Executive Dashboard

* Total Glue executions
* Success and failure rates
* Total execution cost
* Runtime and DPU consumption
* Job-status distribution
* Daily execution trends
* Top applications by cost
* Runtime distribution
* Application, business-unit, and environment filtering

### Cost Analytics

* Total execution cost
* Average, minimum, and maximum cost
* Top expensive Glue jobs
* Cost by business unit
* Cost by environment
* Daily cost trends
* Failed and unsuccessful execution cost analysis

### Runtime Analytics

* Total runtime
* Average runtime
* Minimum and maximum runtime
* Longest-running Glue jobs
* Runtime distribution
* Runtime analysis across filtered workloads

### Failure Analytics

* Failed execution count
* Failure percentage
* Estimated failed/wasted cost
* Lost runtime
* Wasted DPU consumption
* Detailed failed-job execution view
* Application and business-unit failure analysis

---

## AI Copilot

The AI Copilot allows users to analyze Glue execution data using natural-language questions.

Key capabilities include:

* Natural-language analytics over Glue execution data
* Google Gemini-powered SQL generation
* Dynamic schema-aware prompting
* DuckDB-compatible SQL generation
* Local DuckDB query execution
* Read-only SQL validation
* Automatic SQL repair using Gemini when a generated query fails
* Result-driven AI analysis using local Ollama
* Support for cost, reliability, runtime, DPU, failure, and operational questions
* Generated SQL inspection directly from the Streamlit interface

Gemini does **not** process the complete uploaded dataset.

Only the dataset schema, selected representative values, analytical rules, and user question are provided for SQL generation. The actual analytical query runs locally using DuckDB.

---

## Architecture

```text
                 Glue Execution Dataset
                   CSV / Excel / JSON
                          |
                          v
                  +---------------+
                  |   Streamlit   |
                  |    app.py     |
                  +-------+-------+
                          |
             +------------+-------------+
             |                          |
             v                          v
     Analytics Dashboards          AI Copilot UI
      Pandas + Plotly             copilot_ui.py
                                         |
                                         v
                                  CopilotRouter
                                    router.py
                                         |
                                         v
                              Google Gemini Flash
                           Natural Language -> SQL
                                         |
                                         v
                                SQL Validation
                                         |
                                         v
                                      DuckDB
                               Local Query Execution
                                         |
                           +-------------+-------------+
                           |                           |
                      SQL Success                  SQL Failure
                           |                           |
                           |                           v
                           |                   Gemini SQL Repair
                           |                           |
                           +-------------+-------------+
                                         |
                                         v
                                Result DataFrame
                                         |
                                         v
                                Ollama / Qwen 2.5
                                  Local Analysis
                                         |
                                         v
                              AI-Generated Insights
```

---

## Hybrid AI Architecture

The project deliberately separates SQL generation from result interpretation.

### Google Gemini

Gemini is responsible for:

* Understanding the user's analytical question
* Interpreting the uploaded dataset schema
* Mapping business terminology to actual columns
* Generating DuckDB SQL
* Repairing invalid SQL when DuckDB reports an execution error

Gemini receives only the information required for query generation rather than the complete dataset.

### DuckDB

DuckDB is responsible for:

* Executing generated analytical SQL
* Aggregating the uploaded Glue execution data
* Calculating cost, runtime, DPU, failure, and reliability metrics
* Keeping analytical processing local

### Ollama / Qwen 2.5

The local Qwen model is responsible only for:

* Reading the calculated DuckDB result
* Explaining important findings
* Highlighting relevant rankings and comparisons
* Producing concise operational insights

The local model is not responsible for SQL generation.

---

## Technology Stack

| Component             | Technology      |
| --------------------- | --------------- |
| Frontend / Dashboard  | Streamlit       |
| Data Processing       | Pandas          |
| Visualization         | Plotly          |
| Analytical SQL Engine | DuckDB          |
| SQL Generation        | Google Gemini   |
| Local LLM Runtime     | Ollama          |
| Local Summary Model   | Qwen 2.5 3B     |
| Input Formats         | CSV, XLSX, JSON |

---

## Project Structure

```text
AI_Gemini/
│
├── app.py
├── router.py
├── copilot_ui.py
├── requirements.txt
├── sample_questions.md
├── .env
├── .gitignore
└── README.md
```

### `app.py`

Handles:

* Dataset upload
* Data preprocessing
* Filters
* KPI calculations
* Executive dashboard
* Cost analytics
* Runtime analytics
* Failure analytics
* AI Copilot integration

### `copilot_ui.py`

Provides the Streamlit AI chat interface and displays:

* AI-generated insights
* DuckDB query results
* Generated SQL

### `router.py`

Handles the complete AI analytics pipeline:

```text
User Question
      ↓
Gemini SQL Generation
      ↓
SQL Validation
      ↓
DuckDB Execution
      ↓
Gemini SQL Repair (if required)
      ↓
Result DataFrame
      ↓
Local Ollama Summary
```

---

## Prerequisites

* Python 3.10+
* Google Gemini API key
* Ollama installed locally
* Qwen 2.5 3B Ollama model
* Required Python dependencies

---

## Gemini Setup

Create a Gemini API key using Google AI Studio.

Store the key in a `.env` file in the project root:

```text
GEMINI_API_KEY=your_api_key_here
```

Never commit the `.env` file to GitHub.

Make sure `.gitignore` contains:

```text
.env
```

The application loads the API key using `python-dotenv`.

---

## Ollama Setup

Install Ollama for your operating system.

Pull the local model used for result summarization:

```bash
ollama pull qwen2.5:3b
```

Verify the model:

```bash
ollama list
```

Make sure Ollama is running before starting the application.

---

## Install Dependencies

Install the project dependencies:

```bash
pip install -r requirements.txt
```

Core dependencies include:

```text
streamlit
pandas
numpy
plotly
duckdb
google-genai
python-dotenv
ollama
tabulate
openpyxl
```

---

## Run the Application

Start the Streamlit dashboard:

```bash
streamlit run app.py
```

Open the Streamlit URL displayed in the terminal.

Upload a supported Glue execution dataset to begin analysis.

---

## Example AI Questions

### Basic Analytics

```text
What is the total cost of all Glue executions?

How many Glue executions failed?

What is the overall failure rate?

Which applications have the highest total cost?

Show the top 10 longest-running jobs.
```

### Cost and Reliability

```text
Which applications are expensive and unreliable?

Which business unit has the highest failure rate?

How much cost was wasted on unsuccessful executions?

What percentage of total cost comes from unsuccessful executions?

Which jobs have the highest failed cost?
```

### Advanced Analytics

```text
Which applications are expensive and unreliable?
Show the top 10 applications with total executions,
failed executions, failure rate, total cost, and failed cost.
```

```text
Which business units represent the greatest operational and
financial risk from Glue workloads?

Compare execution volume, failure rate, total spend, wasted spend,
runtime, and DPU consumption.
```

```text
Find Glue jobs that appear inefficient compared with other jobs.

Consider total executions, average runtime, average cost per execution,
total DPU usage, failure rate, and failed cost.

Exclude jobs with fewer than 20 executions and return the top 10 jobs
where high resource consumption is combined with poor reliability.
```

```text
Assume you are reviewing this Glue platform for cost optimization
and reliability improvement.

Based only on the available data, identify the top 10 applications
where optimization could potentially have the greatest impact.

Use execution volume, total cost, wasted cost, failure rate,
runtime, and DPU consumption as evidence.
```

Additional examples can be maintained in `sample_questions.md`.

---

## How the AI Copilot Works

1. The user uploads Glue execution data.

2. The dataset is registered locally as a DuckDB table named `glue_jobs`.

3. The router extracts the actual dataframe schema and selected representative categorical values.

4. The user's natural-language question, schema information, and analytical rules are sent to Google Gemini.

5. Gemini generates exactly one read-only DuckDB SQL query.

6. The generated SQL passes through application-level safety validation before execution.

7. DuckDB executes the query locally against the uploaded dataset.

8. If DuckDB rejects the generated SQL, the SQL statement and DuckDB error are sent back to Gemini for one repair attempt.

9. The resulting dataframe is passed to the locally running Qwen 2.5 model through Ollama.

10. Ollama generates an analytical explanation using only the calculated DuckDB result.

11. Streamlit displays the AI insight, result dataframe, and generated SQL.

---
