# Quick Start Guide

## Installation

1. **Install dependencies:**
```bash
cd flight_dashboard_web
pip install -r requirements.txt
```

2. **Run the application:**
```bash
python app.py
```

3. **Access the dashboard:**
Open your browser to `http://localhost:5000`

## First Steps

1. **Upload an Excel file:**
   - Click "Choose File" in the upload section
   - Select your flight data Excel file
   - Click "Upload e Processar"
   - Wait for processing to complete

2. **View Dashboard:**
   - After upload, the dashboard tab will show:
     - KPI cards (Total Flights, Revenue, Passengers)
     - Monthly revenue chart
     - Flight type distribution chart

3. **Navigate Tabs:**
   - Use the tab navigation to switch between views
   - Currently implemented: Dashboard, Filters (placeholder)

## External Access (ngrok)

To share your dashboard with others:

1. **Install ngrok:**
   - Download from https://ngrok.com/download
   - Or use: `choco install ngrok` (Windows) / `brew install ngrok` (Mac)

2. **Start Flask app:**
```bash
python app.py
```

3. **Start ngrok (in another terminal):**
```bash
ngrok http 5000
```

4. **Share the URL:**
   - ngrok will display a public URL like `https://abc123.ngrok.io`
   - Share this URL with others
   - They can access your dashboard from anywhere

## API Endpoints

Test the API directly:

```bash
# Check data status
curl http://localhost:5000/api/data/status

# Get dashboard summary
curl http://localhost:5000/api/dashboard/summary

# Get monthly revenue
curl http://localhost:5000/api/charts/monthly-revenue
```

## Troubleshooting

**Port already in use:**
- Change port in `app.py`: `app.run(port=5001)`

**File upload fails:**
- Check file is .xlsx or .xls format
- Ensure file follows naming convention: `Model - Prefix - Month-Year`

**Charts not loading:**
- Check browser console for errors
- Ensure Plotly.js is loaded (check Network tab)

**Data not processing:**
- Check server logs for error messages
- Verify Excel file structure matches expected format

## Next Steps

The foundation is complete! Remaining work:

- [ ] Complete filter system UI
- [ ] Implement all 14 consolidated tabs
- [ ] Add export functionality
- [ ] Migrate Manifesto processing
- [ ] Migrate Salesforce dashboard
- [ ] Add more analysis endpoints

See `README.md` for full feature list.










