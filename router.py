import os
import re
import duckdb
import ollama
import pandas as pd
import logging
from dotenv import load_dotenv
from google import genai
logger = logging.getLogger(__name__)
load_dotenv()
class CopilotRouter:

    def __init__(
        self,
        df: pd.DataFrame = None,
        ollama_url: str = "http://localhost:11434/api/generate",
        ollama_model: str = "qwen2.5:3b",
        gemini_model: str = "gemini-3.5-flash-lite",
        **kwargs,
    ):
        # Ollama - used only for result summarization
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model

        # Gemini - used only for SQL generation
        self.gemini_model = gemini_model

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. Add it to your .env file."
            )

        self.gemini_client = genai.Client(
            api_key=api_key
        )

        # DuckDB
        self.con = duckdb.connect(database=":memory:")
        self.con.execute(
            "CREATE MACRO try_divide(a, b) AS a / NULLIF(b, 0)"
        )

        self.df = None

        if df is not None and not df.empty:
            self.update_dataframe(df)

    def update_dataframe(self, df: pd.DataFrame) -> None:
        if df is not None and not df.empty:
            self.df = df
            self.con.execute("CREATE OR REPLACE TABLE glue_jobs AS SELECT * FROM df;")


    def _build_system_prompt(self, question: str) -> str:
        schema_str = "No schema available"
        samples_str = "No sample data available"

        if self.df is not None and not self.df.empty:
            schema_info = [f"- {col} ({dtype})" for col, dtype in self.df.dtypes.items()]
            schema_str = "\n".join(schema_info)

            categorical_samples = []
            for col in self.df.select_dtypes(include=["object", "category"]).columns:
                sample_vals = self.df[col].dropna().unique()[:5].tolist()
                categorical_samples.append(f"- '{col}': {sample_vals}")
            if categorical_samples:
                samples_str = "\n".join(categorical_samples)

        return f"""
You generate DuckDB SQL for AWS Glue execution analytics.

TABLE: glue_jobs

SCHEMA:
{schema_str}

SAMPLE VALUES:
{samples_str}

QUESTION:
{question}

RULES:
- Return exactly ONE SQL query and nothing else. No markdown/comments.
- Query must start with SELECT or WITH and be read-only.
- Use only glue_jobs and columns present in SCHEMA, with exact names/case.
- Never invent columns, tables, values, statuses, dates, or data.
- Never use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, REPLACE,
  TRUNCATE, COPY, ATTACH, DETACH, INSTALL, LOAD, PRAGMA, or CALL.
- Prefer simple DuckDB SQL.
- If a requested metric cannot be calculated from SCHEMA, use the closest
  valid calculation supported by available columns; never invent a column.

BUSINESS MAPPING (only when the mapped column exists):
application/app = Application_Name
business unit/BU = Business_Unit
environment/env = Environment
team = Team
account = account_id
job = job_name
status = JobRunState
cost/spend = cost
DPU/compute = dpu_hours
runtime/duration = duration_hours
workers = number_of_worker

SEMANTICS:
- Each row = one Glue execution.
- executions = COUNT(*)
- unique jobs = COUNT(DISTINCT job_name)
- failed = JobRunState = 'FAILED'
- successful/succeeded = JobRunState = 'SUCCEEDED'
- unsuccessful/not successful/problem executions = JobRunState <> 'SUCCEEDED'
- wasted cost/runtime/DPU includes only JobRunState <> 'SUCCEEDED'.
- Use actual SAMPLE VALUES for categorical/status filters when available.

METRICS:
- total_cost = SUM(COALESCE(cost, 0))
- total_runtime = SUM(COALESCE(duration_hours, 0))
- total_dpu = SUM(COALESCE(dpu_hours, 0))
- failed_executions =
  SUM(CASE WHEN JobRunState = 'FAILED' THEN 1 ELSE 0 END)
- failed_cost =
  SUM(CASE WHEN JobRunState = 'FAILED' THEN COALESCE(cost,0) ELSE 0 END)
- wasted_cost =
  SUM(CASE WHEN JobRunState <> 'SUCCEEDED' THEN COALESCE(cost,0) ELSE 0 END)
- wasted_runtime =
  SUM(CASE WHEN JobRunState <> 'SUCCEEDED' THEN COALESCE(duration_hours,0) ELSE 0 END)
- wasted_dpu =
  SUM(CASE WHEN JobRunState <> 'SUCCEEDED' THEN COALESCE(dpu_hours,0) ELSE 0 END)
- percentage = ROUND(100.0 * numerator / NULLIF(denominator,0), 2)

Calculated names such as total_cost, failed_cost, wasted_cost, failure_rate,
success_rate, failed_executions, total_runtime, wasted_runtime, total_dpu and
wasted_dpu are aliases/analytical concepts, NOT source columns unless present
in SCHEMA. Calculate them from source columns.

QUERY INTENT:
- Group only by the dimension requested.
- highest/top/most/worst -> ORDER BY relevant metric DESC.
- lowest/least/minimum -> ORDER BY relevant metric ASC.
- Respect requested top N; otherwise ranking queries may use LIMIT 10.
- Runtime questions use duration_hours; cost uses cost; DPU uses dpu_hours.
- Trends must use a real date/time column from SCHEMA. Never invent one.
- Never invent root causes; return measurable evidence.
- For combined questions, include evidence for every requested concept.
  Example: expensive + unreliable should include both cost and failure metrics.
- Overall/platform summary -> one aggregated row using relevant available metrics.

Before responding, internally verify that all referenced source columns exist,
the query answers QUESTION, calculated metrics are calculated, divisions are
safe, and the SQL is valid read-only DuckDB.

Return SQL only.
"""
    
    def _clean_sql(self, sql_text: str) -> str:
        sql_match = re.search(
            r"```sql\s*(.*?)\s*```",
            sql_text,
            re.DOTALL
        )

        sql = (
            sql_match.group(1).strip()
            if sql_match
            else sql_text.strip()
        )

        return sql.replace("`", '"')


    def _validate_sql(self, sql: str) -> str:
        if not sql or not sql.strip():
            raise ValueError("Gemini returned empty SQL.")

        cleaned_sql = sql.strip()

        # Only SELECT / WITH queries are allowed
        if not re.match(r"^(SELECT|WITH)\b", cleaned_sql, re.IGNORECASE):
            raise ValueError(
                "Only SELECT or WITH queries are allowed."
            )

        # Block dangerous/non-read-only operations
        forbidden_keywords = [
            "INSERT",
            "UPDATE",
            "DELETE",
            "DROP",
            "ALTER",
            "CREATE",
            "REPLACE",
            "TRUNCATE",
            "COPY",
            "ATTACH",
            "DETACH",
            "INSTALL",
            "LOAD",
            "PRAGMA",
            "CALL",
        ]

        for keyword in forbidden_keywords:
            if re.search(rf"\b{keyword}\b", cleaned_sql, re.IGNORECASE):
                raise ValueError(
                    f"Unsafe SQL operation detected: {keyword}"
                )

        return cleaned_sql

    def _repair_sql(
        self,
        question: str,
        failed_sql: str,
        error_message: str,
    ) -> str:
        """Ask Gemini to repair a DuckDB query that failed execution."""
        if self.df is None or self.df.empty:
            raise ValueError("No dataframe is available for SQL repair.")

        schema_str = "\n".join(
            f"- {col} ({dtype})"
            for col, dtype in self.df.dtypes.items()
        )

        repair_prompt = f"""
You are an expert DuckDB SQL developer.

A SQL query generated for an AWS Glue analytics question failed in DuckDB.
Repair the query while preserving the user's original intent.

USER QUESTION:
{question}

TABLE:
glue_jobs

EXACT SCHEMA:
{schema_str}

FAILED SQL:
{failed_sql}

DUCKDB ERROR:
{error_message}

STRICT RULES:
1. Return SQL ONLY. No markdown, explanations, or comments.
2. Return exactly ONE query.
3. The query MUST start with SELECT or WITH.
4. glue_jobs is the ONLY physical table.
5. Use ONLY columns from EXACT SCHEMA.
6. Use exact column names and capitalization.
7. Preserve the USER QUESTION intent.
8. Never invent columns, tables, values, or data.
9. Never generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE,
   REPLACE, TRUNCATE, COPY, ATTACH, DETACH, INSTALL, LOAD,
   PRAGMA, or CALL.
10. Generate valid read-only DuckDB SQL.

Return the repaired SQL now.
"""

        response = self.gemini_client.models.generate_content(
            model=self.gemini_model,
            contents=repair_prompt,
        )

        if not response.text:
            raise ValueError("Gemini returned an empty SQL repair response.")

        repaired_sql = self._clean_sql(response.text)
        repaired_sql = self._validate_sql(repaired_sql)

        logger.info("Gemini repaired SQL: %s", repaired_sql)
        return repaired_sql

    def answer(self, question: str) -> dict:
        """Generate SQL with Gemini, execute in DuckDB, summarize with Ollama."""
        if not question or not question.strip():
            return {
                "status": "error",
                "sql": None,
                "df": pd.DataFrame(),
                "user_msg": "Please enter a question about the Glue job data.",
                "error": "Empty question.",
            }

        if self.df is None or self.df.empty:
            return {
                "status": "error",
                "sql": None,
                "df": pd.DataFrame(),
                "user_msg": "No Glue job data is currently available.",
                "error": "Dataframe is empty.",
            }

        sql = None

        # ------------------------------------------------------
        # 1. GEMINI: NATURAL LANGUAGE -> DUCKDB SQL
        # ------------------------------------------------------
        try:
            system_prompt = self._build_system_prompt(question)

            response = self.gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=system_prompt,
            )

            if not response.text:
                raise ValueError("Gemini returned an empty response.")

            sql = self._clean_sql(response.text)
            sql = self._validate_sql(sql)

            logger.info("Gemini generated SQL: %s", sql)

        except Exception as generation_err:
            logger.error(
                "Gemini SQL generation failed: %s",
                generation_err,
                exc_info=True,
            )
            return {
                "status": "error",
                "sql": sql,
                "df": pd.DataFrame(),
                "user_msg": (
                    "I couldn't generate a valid query for this question. "
                    "Please try rephrasing it."
                ),
                "error": str(generation_err),
            }

        # ------------------------------------------------------
        # 2. DUCKDB: EXECUTE SQL
        #    If it fails, give Gemini ONE repair attempt.
        # ------------------------------------------------------
        try:
            result_df = self.con.execute(sql).df()

        except Exception as db_err:
            logger.warning(
                "Initial DuckDB execution failed: %s",
                db_err,
            )

            try:
                sql = self._repair_sql(
                    question=question,
                    failed_sql=sql,
                    error_message=str(db_err),
                )

                result_df = self.con.execute(sql).df()

            except Exception as repair_err:
                logger.error(
                    "Gemini SQL repair failed: %s",
                    repair_err,
                    exc_info=True,
                )
                return {
                    "status": "error",
                    "sql": sql,
                    "df": pd.DataFrame(),
                    "user_msg": (
                        "I generated a query, but it could not be executed "
                        "successfully. Please try rephrasing the question."
                    ),
                    "error": str(repair_err),
                }

        # ------------------------------------------------------
        # 3. OLLAMA: SUMMARIZE ONLY THE CALCULATED RESULT
        # ------------------------------------------------------
        df_string = (
            result_df.to_markdown(index=False)
            if not result_df.empty
            else "Empty Result"
        )

        summary_prompt = f"""
You are an AWS Glue analytics assistant.

USER QUESTION:
{question}

CALCULATED RESULT:
{df_string}

Analyze the result and answer the user's question using ONLY the data provided.

Provide:
1. A direct answer to the question.
2. The most important findings and rankings.
3. Explain why the highlighted jobs/applications/business units stand out.
4. Compare important values when useful.
5. Mention cost, failure rate, runtime, DPU, or execution count only when
   those metrics are present in the result.
6. End with a short actionable observation based only on the data.

RULES:
- Never invent numbers, causes, or root causes.
- Never use information outside CALCULATED RESULT.
- Do not repeat every row mechanically.
- Focus on the most important 3-5 findings.
- Format numbers clearly.
- Keep the analysis concise but informative.
- Do not use LaTeX or mathematical formatting.
"""

        try:
            summary_resp = ollama.chat(
                model=self.ollama_model,
                messages=[
                    {
                        "role": "user",
                        "content": summary_prompt,
                    }
                ],
                options={
                    "temperature": 0,
                },
            )

            summary = summary_resp["message"]["content"]

        except Exception as summary_err:
            logger.error(
                "Ollama summary generation failed: %s",
                summary_err,
                exc_info=True,
            )

            if result_df.empty:
                summary = "The query completed successfully but returned no matching records."
            else:
                summary = (
                    "The query completed successfully. "
                    "The calculated results are shown below."
                )

        return {
            "status": "success",
            "sql": sql,
            "df": result_df,
            "user_msg": summary,
            "error": None,
        }
