<!-- # SWOT -->
# 📡 SWOT Downloading and Processing Automation Scripts

This repository contains automated scripts for downloading and processing Surface Water and Ocean Topography (SWOT) satellite data. This tool aims to help researchers and practitioners streamline data access and analysis workflows, specifically supporting the water managers in **Tripura state of India and in Bangladesh**.

🔗 More information: [SWOT Project - SASWE, University of Washington](https://depts.washington.edu/saswe/tripura/SWOT.html)

---

## 📦 Features

- ✅ Automated download of SWOT overpass data for selected locations
- 🔄 Processing of SWOT Water Surface Elevation (WSE) raster data
- 📊 Quick visualization for the water bodies in the selected region

---

## 🛠️ Getting Started

### 🔧 Prerequisites

- [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/)
- SWOT data access via [NASA Earthdata Login](https://urs.earthdata.nasa.gov/)

---

## ⚙️ Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/shahzaib1007/SWOT.git
   cd SWOT
    ```
2. **Create and activate Conda environment**

   ```bash
   conda env create -f environment.yml
   conda activate swot_env
---
## 🚀 Usage

### 1. Update Download_SWOT_Data.py with:
* data_path
* earthdata access, via netrc (check steps here) [https://urs.earthdata.nasa.gov/documentation/for_users/data_access/curl_and_wget]
* bounding_box
* geojson_file and UTM info based on the geojson file

### 2. Run the script:
```bash
   SWOT_Automated.sh
```
OR (if you just want to download the raster data, and do some other processing)

```bash
   python Download_SWOT_Data.py
```
---

## 📚 References
* [Operationalized Tool for Bangladesh](https://depts.washington.edu/saswe/tripura/SWOT.html)

* [NASA SWOT Mission](https://swot.jpl.nasa.gov/)

* [LOCSS Project](https://www.locss.org/)

---
