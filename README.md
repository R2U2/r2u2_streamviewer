# R2U2 Streamviewer

## About
The R2U2 Streamviewer is a PyQt5-based GUI for visualizing timeline output data from R2U2. This application provides interactive heatmaps for visualization of timeline data, data filtering for statistical analysis, and automated PDF report generation.

## Structure
```
.
├── demos/
│   ├── data/
│   │   ├── contracts.txt
│   │   ├── output_iter1.txt
│   │   └── ...
│   │
│   ├── images/
│   │   ├── task_heatmap.png
│   │   └── contract_heatmap.png
│   │
│   └── statistical_analysis_report/
│       ├── statistical_analysis_report.html
│       └── html_output_file.html
│
├── r2u2_streamviewer.py
└── README.md
```

## Requirements
* PyQt5
* jinja2
* weasyprint

## Demos
To run the Stream Viewer, you will need:

- A contracts list (`contracts.txt`)
- Output data files (`output_iter*.txt`)

### Demo Data

Sample data is provided in the `demos/` folder to provide a demo of the application.

### Run the Application

From the project root directory, run:
>```
> ./r2u2_streamviewer.py
>```
