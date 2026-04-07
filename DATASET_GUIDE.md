# 📑 Data Dictionary: Agri-Insight Final Dataset

This guide provides a comprehensive overview of the finalized dataset used for **Agri-Insight** agricultural price forecasting. This dataset is specifically engineered to fine-tune the **Chronos-2** (Time-Series Transformer) model.

---

## 📈 Dataset Overview

- **Dataset Name**: `Agri-Insight_Chronos2_v2.csv`
- **Format**: Long-format Panel Data (Multi-series)
- **Total Records**: 369,602
- **Unique Series (Item IDs)**: 93
- **Temporal Resolution**: Daily
- **Observation Period**: 2015-11-16 to 2025-12-31

---

## 🧩 Data Structure (Multi-series)

The dataset uses a **Long-Format** structure, where multiple time series are stacked on top of each other. This allows models with **Group Attention** (like Chronos-2) to learn cross-series patterns.

- **Primary Key**: `(item_id, date)`
- **Target Variable**: `target` (Arcsinh-transformed Price)

---

## 📖 Column Dictionary

### 1. Core Identification & Target
| Column | Type | Description | Transformation |
| :--- | :--- | :--- | :--- |
| `item_id` | String | English name of the crop/grade/size | Cleaned & Mapped |
| `date` | Datetime | Observation date (YYYY-MM-DD) | - |
| `price` | Float | Raw average price of the item | - |
| `target` | Float | Price scale stabilized for model training | `arcsinh(price)` |

### 2. Autoregressive Features (Self-Lags)
*These capture the historical momentum of price movements.*
- `price_lag_[1, 3, 7, 14, 28]`: Historical prices from the past.
- `price_diff`: Daily price change (1st difference).
- `price_ma7`: 7-day Moving Average of the price.

### 3. Future-Known Covariates
*Features that are available or predictable for future horizons.*
| Category | Columns | Description |
| :--- | :--- | :--- |
| **Temporal** | `dayofweek`, `month`, `weekofyear` | Calendar features |
| **Cyclic** | `month_sin/cos`, `dow_sin/cos` | Sine/Cosine seasonal encodings |
| **Weather** | `temp_avg`, `rain_sum`, `humid_avg`, `sunshine_sum` | Global weather metrics |
| **Refined Weather**| `temp_rolling_mean_7`, `weather_index`, `rain_impact` | Interaction & Rolling features |

### 4. Past-Only Covariates (External Indicators)
*Economic data used to provide macro-economic context.*
- `oil_diesel` / `oil_diesel_lag_1/3`: Diesel fuel price (Tax-exempt).
- `cpi_total`: Total Consumer Price Index.
- `gov_bond_3y`: 3-Year Government Bond Yield (Interest Rate).
- `epu`: Economic Policy Uncertainty Index.
- `m2_sa`: Broad Money Supply (Seasonally Adjusted).

---

## ⚙️ Data Preprocessing Pipeline

### 1. Target Normalization
We apply the **Inverse Hyperbolic Sine (Arcsinh)** transformation to the price. This is similar to log-transformation but handles zeros/negatives better and compresses extreme price spikes (spikes are common in agricultural data).
$$target = \text{arcsinh}(price) = \ln(price + \sqrt{price^2 + 1})$$

### 2. Global Scaling
All numerical covariates (excluding `target` and `price`) are normalized using `StandardScaler`:
- **Mean**: 0.0
- **Standard Deviation**: 1.0
This ensures that variables with large magnitudes (like M2 supply) do not dominate the optimization process during training.

### 3. Causal Feature Engineering
All rolling and lag features are generated using a **Strictly Causal** approach. For any record at time $T$, no information from time $T+1$ or beyond was used in its calculation, preventing data leakage.

---

## 📊 Exploratory Analysis: Feature Correlations

To ensure the independence and relevance of our features, we analyzed the **Pearson Correlation** across all 93 series.

![Average Correlation Heatmap](file:///c:/Users/minsoo/Desktop/capstone/data/visuals/average_correlation_heatmap.png)

> [!TIP]
> Use the [average_correlation_heatmap.png](file:///c:/Users/minsoo/Desktop/capstone/data/visuals/average_correlation_heatmap.png) to explain the influence of weather and self-lags to stakeholders.

---

## 🛠️ Maintenance & Recreation
The dataset can be regenerated using the following scripts in the `scripts/` directory:
1. `prepare_chronos2_dataset.py`: Core preprocessing and English mapping.
2. `analyze_correlation.py`: Correlation visualization.
3. `summarize_dataset.py`: Statistical summary generation.
