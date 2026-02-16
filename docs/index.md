# DataForge 

**DataForge** is a high-performance CLI tool designed to automate the preparation and management of machine learning datasets. It helps you transform raw data (like videos and unsorted images) into clean, balanced, and ready-to-train datasets with minimal effort.

[Read the full documentation here](https://seregacodit.github.io/DataForge)

### Key Features
* **Parallel Processing:** Uses multiprocessing to handle thousands of files quickly.
* **Vectorized Calculations:** Employs NumPy for ultra-fast image comparison and hashing.
* **Smart Caching:** Incremental caching (MD5-based) allows working with large datasets on NAS or local storage without re-calculating existing data.
* **Flexible Configuration:** Built with Pydantic v2 for safe settings via `config.json` or CLI arguments.

---

### Available Commands

* **`move`** — Move files from source to target directory based on specific patterns.
* **`slice`** — Convert video files into sequences of images. Use `--remove` to delete the source video after a successful slice.
* **`delete`** — Safely remove files matching specific patterns.
* **`dedup`** — Find and remove visual duplicates using **dHash**.
    * *Threshold:* Similarity limit (0-100%).
    * *Core Size:* Higher values (e.g., 32) detect small changes; lower values (e.g., 8) ignore noise.
* **`clean-annotations`** — Automatically find and delete "orphan" annotation files (XML/TXT) that do not have a corresponding image.
* **`convert-annotations`** — Convert dataset labels between formats (e.g., **Pascal VOC** to **YOLO**).
* **`stats` — Advanced Dataset Analytics & Health Check**
This command performs a deep-dive into your dataset to identify biases and feature correlations before you start training.
    * **Analytics Highlights:**
        * **Class Distribution:** Visualizes object counts to detect imbalances.
        * **Spatial Density Heatmaps:** Identifies "positional bias" for each class using 3x3 grids.
        * **Correlation Analysis:** Global and per-class matrices showing relationships between features.
        * **Dataset Manifold (UMAP):** 2D projection to identify "representation gaps" and object clusters.
        * **Quality Metrics:** Analysis of object areas, aspect ratios, brightness, contrast, and blur.
        * **Outlier Detection:** Automatically marks extreme data points using the IQR method.
    * **Outputs:** Technical console summary, high-resolution PNG plots, and unified PDF reports.

**Usage Example:**
```bash
python data_forge.py stats --src ./data/train --target_format yolo --report_path ./reports/v1
```

---

### Automation & Intervals
By default, commands run once. To monitor a folder and process files as they appear, use these flags:
* **`-r`**: Run the command in a continuous cycle.
* **`-s`**: Set the delay (in seconds) between cycles.

---

### Quick Start

1. **Clone the repository:**
```bash
git clone https://github.com/SeregaCodit/DataForge.git
cd DataForge
```

2. **Setup environment:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. **Check usage:**
```bash
python data_forge.py --help             # See all available commands
python data_forge.py {command} --help   # See arguments for a specific command
```

---

### Workflow Optimization
For multiple tasks, you can modify `start_all_tasks.sh` and run them in the background:
```bash
bash start_all_tasks.sh
```
To stop all running DataForge processes:
```bash
pkill -f data_forge.py
```

### Configuration Priority
You can manage default settings in `config.json`. DataForge follows this priority:
**CLI Arguments > config.json > Internal Defaults.**
