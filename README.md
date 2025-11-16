# MAPLE: Multi-Agent Adaptive Planning with Long-Term Memory for Table Reasoning

This repository contains the official implementation of [**MAPLE**](https://arxiv.org/abs/2506.05813), a multi-agent framework designed to improve table-based question answering through **feedback-driven reasoning**, **verification**, **reflection**, and **long-term memory evolution**.


---

## 🔍 MAPLE Framework Overview

<p align="center">
  <img src="images/overview.png" alt="Overview Illustration" width="500">
</p>

MAPLE mimics human-style problem solving by decomposing the reasoning process into **four cooperating agents**:

### **1. Solver — Progressive Reasoning (ReAct)**

* Performs iterative reasoning over the table.
* Interacts with the environment and updates intermediate tables.
* Uses both **working memory** (Reflector feedback) and **long-term memory** (retrieved notes).

### **2. Checker — Verification**

* Validates:

  * **Answer type**
  * **Format**
  * **Evidence grounding**
* Outputs structured feedback scores and comments.

### **3. Reflector — Error Diagnosis & Repair**

* Analyzes reasoning trace + Checker feedback.
* Identifies root causes of the error.
* Generates an **improvement plan** for the next reasoning attempt.

### **4. Archiver — Long-Term Memory System**

* Creates structured memory notes.
* Retrieves similar past experiences.
* Performs memory evolution (semantic clustering, connection strengthening).

---

## 📦 Installation

```bash
git clone https://github.com/bettyandv/MAPLE-table-reasoning.git
cd MAPLE-table-reasoning
```

---

## 📚 Datasets

We support two benchmarks:

* [**WikiTableQuestions (WIKITQ)**](https://github.com/ppasupat/WikiTableQuestions)
* [**TabFact**](https://github.com/wenhuchen/Table-Fact-Checking)

Both should be placed under the `./data/` directory.

---

## 🚀 Running MAPLE

### **1. Multi-round MAPLE inference**

This runs the full Solver → Checker → Reflector loop.

```bash
bash run_batch.sh
```

Internally calls `run_batch.py`  which:

* loads dataset
* initializes agents
* repeatedly processes messages until all questions reach a final answer
* saves intermediate results every round

---

### **2. Building Long-Term Memory**

After finishing inference:

```bash
bash run_memory.sh
```

Uses `run_memory.py`  to:

* parse reasoning traces
* extract key fields (question type, steps, errors)
* add into memory system
* evolve memory clusters

---

### **3. Memory-Augmented Solver**

To run the solver again with retrieved memory injected:

```bash
bash mem_to_solver.sh
```

Uses `mem_to_solver.py`  to:

* load memory JSON
* rebuild vector index
* attach top-k memories to each question before solving


---

### **4. Running with OpenAI Batch**

```bash
python run_openai_batch.py
```

Supports efficient large-scale evaluation.


---

## 📜 Citation

If you use MAPLE, please cite:

```
@misc{bai2025maplemultiagentadaptiveplanning,
      title={MAPLE: Multi-Agent Adaptive Planning with Long-Term Memory for Table Reasoning}, 
      author={Ye Bai and Minghan Wang and Thuy-Trang Vu},
      year={2025},
      eprint={2506.05813},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2506.05813}, 
}
```

---
