# DataForge 
**DataForge** is a high-performance CLI tool designed to automate the preparation and management of machine learning datasets. It helps you transform raw and dirty data (like videos and unsorted images) into clean, balanced, and ready-to-train datasets with minimal effort.


### Key Features
* **Parallel Processing:** uses multiprocessing to handle thousands of files quickly.
* **Vectorized Calculations:** employs NumPy for ultra-fast image comparison.
* **Smart Caching:** incremental caching (MD5-based) allows working with large datasets on NAS without re-calculating everything.
* **Config:** Built with Pydantic v2 for safe and flexible settings via JSON or CLI.

---

### Available Commands

* **`move`** — move files from source to target directory based on patterns.
* **`slice`** — convert video files into sequences of images. Use `--remove` to delete the source video after a successful slice.
* **`delete`** — safely remove files matching specific patterns.
* **`dedup`** — find and remove visual duplicates using **dHash**.
    * *Threshold:* information similarity limit (0-100%).
    * *Core Size:* higher values (e.g., 32, 64) detect small changes (like a moving car), lower values (e.g., 8) ignore noise.
* **`clean-annotations`** — automatically find and delete "orphan" annotation files (XML/TXT) that no longer have a corresponding image.
* **`convert-annotations`** — convert dataset labels between formats (e.g., **Pascal VOC** to **YOLO**).

---

### Automation & Intervals
By default, commands run once. If you want to monitor a folder and process files as they appear, use the repeat flag:
* Use **`-r`** to run the command in a cycle.
* Set the delay between cycles with **`-s`** (seconds).

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
python data_forge.py --help             # See all commands
python data_forge.py {command} --help   # See arguments for a specific command
```

---

### Workflow
For multiple tasks, you can modify `start_all_tasks.sh` and run them all in the background:
```bash
bash start_all_tasks.sh
```
To stop all running DataForge processes:
```bash
pkill -f data_forge.py
```

### Configuration
You can manage all default settings in `config.json`. DataForge follows this priority:
**CLI Arguments > config.json > Internal Defaults.**
