# HydroMaterials Decision Intelligence

Professional Streamlit application for multi-criteria, methodology-driven optimization of materials in small hydropower plants, integrating hydraulic, energy, reliability, and life-cycle cost analysis.

## Overview

This repository contains an end-to-end decision platform that executes a six-stage computational pipeline:

1. Hydraulic modeling  
2. Sediment abrasion and material durability  
3. Reliability indicators  
4. Life-cycle cost (LCC) economics  
5. MCDA-AHP ranking  
6. EGK robustness validation

The app is interactive and web-based, with traceable inputs and outputs across all stages.

## Key Features

- Interactive inputs for Stage 1 to Stage 6.
- `Load default data` action to restore original input values.
- Numeric spinner steps set to 10% of each original default value.
- Fixed internal gravitational constant `g` (not user-editable).
- Professional dashboard views:
  - Overview and methodology
  - Executive summary
  - Stage-by-stage outputs
  - App_MHS-style visuals
  - Sensitivity and robustness analytics
  - JSON export snapshot
- Dynamic charts recomputed from current stage outputs.

## Repository Structure

- `streamlit_app.py`: Main web application (UI + orchestration).
- `stage1.py` ... `stage6.py`: Computational pipeline modules.
- `requirements.txt`: Python dependencies.
- `run_app.bat`: Windows launcher using local virtual environment.
- `colab_streamlit_runner.ipynb`: Colab launcher notebook.
- `App_MHS.ipynb`, `MicroHydropowerSystems.ipynb`: Supporting notebooks.

## Methodology Pipeline

- **Stage 1 - Hydraulic Foundation**: Computes velocity, head losses, net head, and hydraulic power.
- **Stage 2 - Sediment and Abrasion**: Quantifies abrasion intensity and durability effects by material.
- **Stage 3 - Reliability Layer**: Estimates SAIFI, SAIDI, ENS, and normalized reliability metrics.
- **Stage 4 - Life-Cycle Economics**: Builds discounted LCC decomposition (CAPEX, maintenance, interruptions, replacement).
- **Stage 5 - MCDA-AHP Decision Core**: Produces weighted ranking with AHP consistency controls.
- **Stage 6 - EGK Robustness Validation**: Uses fuzzy clustering and consensus analysis to assess ranking robustness.

## Quick Start (Local, Windows)

1. Create virtual environment:

```powershell
python -m venv .venv
```

2. Activate environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```powershell
pip install -r requirements.txt
```

4. Run the app:

```powershell
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

Or use:

```powershell
run_app.bat
```


