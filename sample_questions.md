# Sample Questions

Try these questions in the **AI GlueOps Intelligence Copilot** after uploading a Glue execution dataset.

The Copilot uses **Google Gemini to translate natural-language questions into DuckDB SQL**, executes the analysis locally with DuckDB, and uses **Ollama/Qwen 2.5** to summarize the calculated results.

---

## Quick Start

Start with these questions to verify the complete AI pipeline:

* How many Glue executions are there?
* What is the total execution cost?
* What is the overall failure rate?
* How many unique Glue jobs are there?
* Show the top 10 applications by total cost.
* Which business unit has the most failed executions?
* What is the total DPU consumption?
* Show the top 10 longest-running jobs.

---

## Overall Analytics

* How many executions are there?
* How many unique Glue jobs are there?
* How many executions succeeded?
* How many executions failed?
* What is the overall success rate?
* What is the overall failure rate?
* What is the total execution cost?
* What is the total runtime?
* What is the total DPU consumption?
* Give me an overall summary of Glue execution performance.
* Show total executions, successful executions, failed executions, success rate, failure rate, total cost, runtime, and DPU consumption.

---

## Cost Analytics

* What is the total cost of all Glue executions?
* What is the average cost per execution?
* Which execution has the highest cost?
* Show the top 10 most expensive Glue jobs.
* Show total cost by application.
* Show total cost by business unit.
* Show total cost by environment.
* Which application contributes the most to total cost?
* Which business unit has the highest total spend?
* Show the top 10 jobs by total cost.
* Which applications have high execution volume and high total cost?
* Show total cost and average cost per execution by application.

---

## Failure & Reliability Analytics

* How many executions failed?
* What percentage of executions failed?
* Show failed executions.
* Which job has the most failures?
* Show failed executions by application.
* Show failed executions by business unit.
* Show failed executions by environment.
* Which application has the highest number of failures?
* Which business unit has the highest failure rate?
* Show total executions, failed executions, and failure rate by application.
* Which jobs have the highest failure rate?
* Which applications appear least reliable based on execution failures?
* Show the top 10 applications with the highest failure rate and their execution counts.

---

## Waste Analytics

Unsuccessful executions are executions that did not complete with a `SUCCEEDED` status.

* What is the total cost of unsuccessful executions?
* What is the total wasted runtime?
* What is the total wasted DPU consumption?
* Show wasted cost by application.
* Show wasted cost by business unit.
* Show wasted cost by environment.
* Which application has the highest wasted cost?
* Which business unit wastes the most DPU?
* Which jobs contribute the most to unsuccessful execution cost?
* What percentage of total cost comes from unsuccessful executions?
* Compare total cost and wasted cost by application.
* Show total DPU and wasted DPU by business unit.

---

## Runtime Analytics

* What is the total runtime?
* What is the average execution runtime?
* Which execution has the longest runtime?
* Show the top 10 longest-running executions.
* Show total runtime by application.
* Show total runtime by business unit.
* Show average runtime by application.
* Which jobs have the highest average runtime?
* Which business unit consumes the most execution time?
* Compare average runtime across environments.
* Show the top 10 jobs by total runtime.
* What is the average runtime of failed executions?

---

## DPU & Compute Analytics

* What is the total DPU usage?
* What is the average DPU usage per execution?
* Which job consumes the most DPU?
* Show DPU consumption by application.
* Show DPU consumption by business unit.
* Show DPU consumption by environment.
* Which application consumes the most DPU hours?
* Which business unit consumes the most compute resources?
* Show the top 10 jobs by total DPU consumption.
* Compare total DPU and wasted DPU by application.
* Which applications have high DPU consumption but relatively low execution volume?

---

## Application Analytics

* Which applications have the highest execution volume?
* Which applications cost the most?
* Which applications fail the most?
* Which applications have the highest failure rate?
* Which applications consume the most DPU?
* Which applications have the highest total runtime?
* Compare cost, runtime, and DPU consumption by application.
* Show total executions, failed executions, failure rate, and total cost for each application.
* Which applications contribute the most to unsuccessful execution cost?

---

## Business Unit Analytics

* Show total executions by business unit.
* Which business unit has the highest total cost?
* Which business unit has the highest failure rate?
* Which business unit consumes the most DPU?
* Show wasted cost by business unit.
* Compare execution volume, failures, and cost across business units.
* Which business units have both high cost and high failure rates?
* Show total cost, wasted cost, runtime, and DPU by business unit.

---

## Environment Analytics

* Compare execution counts across environments.
* Show total cost by environment.
* Which environment has the highest failure rate?
* Compare runtime across environments.
* Compare DPU consumption across environments.
* Show total cost and wasted cost by environment.
* Which environment appears least reliable?
* Compare success rate, failure rate, cost, runtime, and DPU across all environments.

---

# Advanced Analytical Questions

These questions test Gemini's ability to translate broader operational questions into measurable SQL.

## Cost + Reliability

* Which applications are expensive and unreliable? Show the top 10 applications with total executions, failed executions, failure rate, total cost, and failed cost.

* Find the top 10 jobs that are both expensive and unreliable. Consider total cost, execution count, failed executions, failure rate, and failed cost.

* Which business units are spending a lot while also having poor reliability? Compare total cost, failure rate, failed executions, and wasted cost.

* Which applications combine high execution volume, high total cost, and frequent failures?

---

## Resource Efficiency

* Analyze which applications appear operationally inefficient. Consider execution volume, total cost, average cost per execution, runtime, DPU consumption, failure rate, and cost associated with unsuccessful executions. Show the top 10 applications that deserve investigation.

* Which applications consume significant DPU and runtime but also have high failure rates?

* Find jobs with high average runtime, high DPU consumption, and frequent failures.

* Which business units consume the most resources through unsuccessful executions?

---


## Important Note

The AI Copilot generates analytical SQL dynamically based on the uploaded dataset schema.

Questions should therefore reference information that exists in the uploaded dataset. The Copilot should not invent unavailable columns, metrics, timestamps, business dimensions, or root causes.

For important operational or financial decisions, review the generated SQL and calculated result before relying on the AI-generated explanation.
