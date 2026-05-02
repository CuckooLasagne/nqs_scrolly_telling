# NQS  Scrollytelling

This project provides a data-driven "scrollytelling" report analyzing National Quality Standard (NQS) ratings for Early Childhood Education and Care (ECEC) services in Victoria. It uses data from the **ACECQA NQF Snapshots** to visualise performance trends, socio-economic distributions, and provider management type splits.


## 📁 Project Structure

The project uses the the `closeread` extension in Quarto. All other code is in python.

```
├── scrolly.qmd            # Main Quarto document
├── script/
│   └── plotting.py        # Refactored Plotly functions (the engine)
│   └── NQAITS_Quarterly_Data.csv    # Cleaned data from below (removed due to size)
│   └── Data Cleaning.ipynb    # Jupyter notebook used to clean raw data from ACECQA
│   └── NQAITS Quarterly Data Splits (Q3 2013 - Q4 2025).xlsx    # Raw data from ACECQA (removed due to size)
└── README.md              # Project documentation
```

## 🔗 Resources
- **Data Source**: [ACECQA NQF Snapshots](https://www.acecqa.gov.au/resources/snapshot-and-reports/nqf-snapshots)
