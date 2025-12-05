# A/B Test Sample Size Calculator

## Overview
A Streamlit web application that helps users calculate the required sample size for A/B tests based on statistical parameters. The calculator ensures statistically valid experimental design and includes an AI-powered assistant for guidance.

## Features

### Core Calculator
- **Input Parameters:**
  - Baseline conversion rate (%)
  - Minimum detectable effect (MDE) (%)
  - Statistical power (%)
  - Significance level (%)
  - Test type (one-tailed or two-tailed)
  - Expected daily traffic (optional)

- **Outputs:**
  - Sample size per variant
  - Total sample size
  - Estimated test duration (when traffic provided)
  - Power curve visualization
  - Exportable results (JSON)

### Comparison Mode
- Add multiple test scenarios
- Compare sample sizes and durations side-by-side
- Visual bar charts for comparison
- Export all scenarios to JSON

### AI Assistant
- Ask questions about A/B testing best practices
- Get advice on experiment design
- Understand statistical concepts
- Context-aware responses based on current test parameters
- Powered by OpenAI GPT-5

### PWA Support
- Installable as a Progressive Web App
- Works on mobile and desktop

## Technical Details

### Stack
- Python 3.11
- Streamlit (web framework)
- SciPy (statistical calculations)
- NumPy (numerical operations)
- Pandas (data manipulation)
- Altair (visualizations)
- OpenAI API (AI assistant)

### Statistical Method
Uses the two-proportion z-test formula for sample size calculation:
- Calculates pooled variance
- Applies z-scores for alpha (significance) and beta (power)
- Supports both one-tailed and two-tailed tests

### File Structure
```
├── app.py              # Main Streamlit application
├── .streamlit/
│   └── config.toml     # Streamlit server configuration
├── static/
│   ├── manifest.json   # PWA manifest
│   └── sw.js           # Service worker
├── pyproject.toml      # Python dependencies
└── replit.md           # This file
```

### Environment Variables
- `OPENAI_API_KEY` - Required for AI assistant functionality

## Running the Application
```bash
streamlit run app.py --server.port 5000
```

The app runs on port 5000 and is accessible via the Replit webview.

## Recent Changes
- 2024-12-05: Added AI assistant tab with OpenAI integration
- 2024-12-05: Added PWA support for installation
- 2024-12-04: Initial build with all MVP features
- Added one-tailed vs two-tailed test support
- Added duration estimator based on daily traffic
- Added power curve visualization
- Added JSON export functionality
- Added comparison mode for multiple scenarios
