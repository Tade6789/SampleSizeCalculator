# A/B Test Calculator Pro

Professional A/B testing sample size calculator with AI-powered insights, test history tracking, and advanced analytics.

## Version 2.0 - What's New

### Core Features
- **Supabase Integration**: Secure authentication and data persistence
- **Test History**: Save and manage all your test calculations
- **Modern UI**: Clean, professional interface with smooth animations
- **AI Assistant**: GPT-5 powered consultant for A/B testing questions
- **Comparison Mode**: Compare multiple test scenarios side-by-side
- **PWA Support**: Install as a mobile or desktop app

### Technical Improvements
- **Database**: Migrated from local SQLAlchemy to Supabase PostgreSQL
- **Authentication**: Supabase Auth with email/password
- **Performance**: Optimized queries and reduced bundle size
- **Security**: Row Level Security policies on all tables
- **Design**: Modern blue color scheme (no more purple)

## Features

### 1. Calculator
Calculate required sample sizes with:
- Baseline conversion rate input
- Minimum detectable effect (MDE)
- Statistical power and significance levels
- One-tailed or two-tailed test support
- Duration estimation based on daily traffic
- Real-time power curve visualization
- Save calculations for later reference
- Export results to JSON

### 2. Test History
- View all saved calculations
- Filter and search tests
- Track total samples calculated
- Delete old calculations
- Quick stats in sidebar

### 3. Comparison Mode
- Add multiple test scenarios
- Side-by-side comparison tables
- Visual bar charts for:
  - Sample size comparison
  - Duration comparison
- Export comparison data
- Clear all scenarios

### 4. AI Assistant
- Ask questions about A/B testing
- Get personalized advice based on your test parameters
- Quick question buttons for common topics
- Chat history with clear option
- Powered by GPT-5

## Database Schema

### Tables
- **profiles**: User profiles extending Supabase auth
- **test_calculations**: Saved A/B test calculations
- **saved_scenarios**: Saved comparison scenarios
- **test_templates**: Reusable test templates

All tables have:
- Row Level Security (RLS) enabled
- User-scoped access policies
- Automatic timestamps
- Proper indexes for performance

## Installation

### Prerequisites
- Python 3.11+
- Supabase account
- OpenAI API key (optional, for AI assistant)

### Setup

1. Clone the repository
```bash
git clone <your-repo-url>
cd ab-test-calculator-pro
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Configure environment variables
```bash
VITE_SUPABASE_URL=your-supabase-url
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
OPENAI_API_KEY=your-openai-key  # Optional
```

4. Run the application
```bash
streamlit run app.py --server.port 5000
```

## Usage

### Sign Up / Sign In
1. Create an account with email and password
2. Password must be at least 6 characters
3. Sign in with your credentials

### Calculate Sample Size
1. Enter your baseline conversion rate
2. Set the minimum detectable effect you want to detect
3. Choose power and significance levels (defaults: 80% and 5%)
4. Select test type (two-tailed recommended)
5. Optionally add daily traffic for duration estimate
6. View results and power curve
7. Save calculation for later reference

### Compare Scenarios
1. Go to "Comparison" tab
2. Add multiple scenarios with different parameters
3. View comparison table and charts
4. Export comparison data
5. Clear when done

### Ask AI Assistant
1. Go to "AI Assistant" tab
2. Click a quick question or type your own
3. Get expert advice on A/B testing
4. Continue conversation as needed
5. Clear chat history when done

## Statistical Methodology

The calculator uses the **two-proportion z-test** formula:

```
n = [(Zα√(2p̄(1-p̄)) + Zβ√(p₁(1-p₁) + p₂(1-p₂)))]² / (p₂ - p₁)²
```

Where:
- `n` = sample size per variant
- `Zα` = z-score for significance level (α)
- `Zβ` = z-score for power (1-β)
- `p₁` = baseline conversion rate
- `p₂` = expected variant conversion rate
- `p̄` = pooled proportion

### Two-Tailed vs One-Tailed
- **Two-tailed**: Detects effects in both directions (increase OR decrease)
  - More conservative
  - Requires larger sample size
  - Recommended for most cases

- **One-tailed**: Only detects effects in one direction
  - Requires ~20% fewer samples
  - Use only when you're certain about effect direction

## Architecture

### Frontend
- **Framework**: Streamlit
- **Visualizations**: Altair
- **PWA**: Service Worker + Manifest

### Backend
- **Database**: Supabase (PostgreSQL)
- **Auth**: Supabase Auth
- **AI**: OpenAI GPT-5

### Security
- Row Level Security on all tables
- Authenticated-only access
- User-scoped data policies
- Secure session management

## Development

### Project Structure
```
├── app.py                  # Main application
├── pyproject.toml          # Python dependencies
├── .streamlit/
│   └── config.toml        # Streamlit configuration
├── static/
│   ├── manifest.json      # PWA manifest
│   └── sw.js              # Service worker
└── README.md              # This file
```

### Adding Features
1. Update `app.py` with new functionality
2. Add database migrations if needed
3. Update UI components
4. Test authentication and data access
5. Update documentation

### Database Migrations
Use Supabase migration tools:
```sql
-- Example migration
CREATE TABLE new_table (...);
ALTER TABLE new_table ENABLE ROW LEVEL SECURITY;
CREATE POLICY "..." ON new_table ...;
```

## Best Practices

### A/B Testing
1. Run tests for at least 1-2 weeks
2. Wait for full business cycles
3. Don't stop tests early
4. Consider external factors (seasonality, marketing campaigns)
5. Use 80% power and 5% significance as defaults
6. Choose MDE based on business impact, not traffic limitations

### Using the Calculator
1. Be realistic with baseline rates
2. Choose smallest MDE that matters to your business
3. Account for novelty effects
4. Plan for longer tests when possible
5. Save calculations for documentation
6. Compare different scenarios before deciding

## Troubleshooting

### Authentication Issues
- Check Supabase credentials
- Verify email confirmation settings
- Clear browser cache and cookies
- Check browser console for errors

### Calculation Errors
- Ensure baseline rate < 100%
- Check that MDE doesn't result in >100% conversion rate
- Verify all inputs are positive numbers
- Try different parameter combinations

### AI Assistant Not Working
- Verify OPENAI_API_KEY is set
- Check API key has sufficient credits
- Check console for specific error messages
- Try refreshing the page

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

## Credits

Built with:
- [Streamlit](https://streamlit.io/)
- [Supabase](https://supabase.com/)
- [OpenAI](https://openai.com/)
- [Altair](https://altair-viz.github.io/)
- [SciPy](https://scipy.org/)

## Changelog

### Version 2.0.0 (2024-12-05)
- Complete rewrite with Supabase integration
- Added test history tracking
- Modern UI with blue color scheme
- AI assistant with GPT-5
- Improved power curve visualization
- PWA enhancements
- Better mobile support

### Version 1.0.0 (2024-12-04)
- Initial release
- Basic calculator functionality
- Comparison mode
- Export to JSON
