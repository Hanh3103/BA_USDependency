# BA_USDependency

This project contains a pipeline for analyzing dependencies between user stories.  
The main implementation is located in `src/`, while evaluation and Colab notebooks are stored in `eval_with_colab/`.

---

## Project Structure

```text
BA_USDependency/
├── src/
│   ├── config.py
│   ├── connectionsHandle/
│   │   └── ollama_connection.py
│   ├── errors/
│   ├── prompts/
│   ├── schemas/
│   ├── stages/
│   │   ├── annotation.py
│   │   ├── dependency_analysis_annotated.py
│   │   ├── dependency_analysis_text.py
│   │   ├── dependency_pipeline_annotated.py
│   │   ├── dependency_pipeline_text.py
│   │   └── well_formulated_extractor.py
│   └── utils/
│       ├── file_parser.py
│       ├── file_writer.py
│       └── llm_client_helpers.py
│
├── eval_with_colab/
│   ├── annotation/
│   └── dependency_analysis/
│       ├── stage1_evaluation.ipynb
│       ├── stage2_evaluation.ipynb
│       ├── final_evaluation.ipynb
│       └── run_pipeline_save_results.ipynb
│
├── requirements.txt
└── README.md
```

## Installation

To install the required dependencies, run:

```bash
pip install -r requirements.txt
```

## Run the pipeline on Google Colab
Use the provided Colab notebooks in `eval_with_colab/` to run the pipeline and evaluate the results. The notebooks are organized into stages for easier understanding and execution.

Use script `run_pipeline_save_results.ipynb` to run the dependency pipeline and save the results for further analysis.

Use the script evaluation_framework_annotation.ipynb to run the annotation and evaluation framework for the user stories. 
