# TikTok Slideshow Analyzer

A Python workflow to analyze TikTok slideshow posts, download images, extract metadata, and upload everything to Google Drive.

## Features

- Parse JSON data from TikTok/Apify exports
- Filter and identify slideshow posts
- Download all slideshow images with organized folder structure
- Extract comprehensive metadata (author info, engagement metrics, hashtags, etc.)
- Generate CSV and JSON metadata exports
- Create analysis summaries
- Upload everything to Google Drive automatically

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd apify_tiktok_slides
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Step 1: Analyze TikTok Data

Run the analyzer on your TikTok JSON file:

```bash
python tiktok_slideshow_analyzer.py input.json
```

Or specify a custom output directory:

```bash
python tiktok_slideshow_analyzer.py input.json -o my_analysis
```

This will:
- Parse the JSON file
- Filter for slideshow posts
- Download all slideshow images to `output/images/`
- Save metadata to `output/metadata/`
- Generate a summary report

#### Output Structure

```
output/
├── images/
│   ├── username_postid1/
│   │   ├── slide_01.jpg
│   │   ├── slide_02.jpg
│   │   └── ...
│   ├── username_postid2/
│   │   └── ...
└── metadata/
    ├── slideshows_metadata.csv
    ├── slideshows_metadata.json
    └── summary.txt
```

### Step 2: Upload to Google Drive

#### Google Drive Setup

Before uploading, you need to set up Google Drive API access:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the **Google Drive API**
4. Create OAuth 2.0 credentials:
   - Go to "Credentials" → "Create Credentials" → "OAuth client ID"
   - Application type: "Desktop app"
   - Download the JSON file
5. Save the downloaded file as `credentials.json` in this directory

#### Upload Command

```bash
python gdrive_uploader.py
```

Or with custom options:

```bash
python gdrive_uploader.py -d output -n "My_TikTok_Analysis"
```

On first run, it will:
1. Open a browser window for Google authentication
2. Request permission to access Google Drive
3. Save credentials in `token.pickle` for future use

## Command-Line Options

### tiktok_slideshow_analyzer.py

```
positional arguments:
  json_file             Path to JSON file containing TikTok data

optional arguments:
  -h, --help            Show help message
  -o OUTPUT, --output OUTPUT
                        Output directory (default: output)
```

### gdrive_uploader.py

```
optional arguments:
  -h, --help            Show help message
  -d DIRECTORY, --directory DIRECTORY
                        Local output directory to upload (default: output)
  -n NAME, --name NAME  Name for Google Drive folder
  -c CREDENTIALS, --credentials CREDENTIALS
                        Path to Google OAuth credentials file
```

## Input JSON Format

The script expects JSON data in the format provided by Apify's TikTok scraper. Each entry should have:

- `isSlideshow`: Boolean indicating if it's a slideshow
- `slideshowImageLinks`: Array of image objects with `downloadLink`
- `authorMeta`: Author information
- `hashtags`: Array of hashtag objects
- Engagement metrics: `diggCount`, `shareCount`, `playCount`, etc.

Example:
```json
[
  {
    "id": "7309919649490029856",
    "isSlideshow": true,
    "slideshowImageLinks": [
      {
        "downloadLink": "https://api.apify.com/..."
      }
    ],
    "authorMeta": {
      "name": "username",
      "nickName": "Display Name"
    },
    ...
  }
]
```

## Metadata Extracted

The analyzer extracts the following metadata for each slideshow:

- Post ID and URL
- Author username, nickname, verified status, follower count
- Post text and creation time
- Location
- Hashtags
- Music information
- Engagement metrics (likes, shares, plays, comments, collects)
- Number of slides
- Ad/sponsored status

## Examples

### Complete Workflow

```bash
# 1. Analyze TikTok data
python tiktok_slideshow_analyzer.py tiktok_data.json -o analysis_results

# 2. Upload to Google Drive
python gdrive_uploader.py -d analysis_results -n "TikTok_Campaign_Analysis"
```

### Analyzing Multiple Files

```bash
# Process multiple JSON files
for file in data/*.json; do
    python tiktok_slideshow_analyzer.py "$file" -o "output_$(basename $file .json)"
done
```

## Troubleshooting

### "credentials.json not found"

Download OAuth credentials from Google Cloud Console. See "Google Drive Setup" above.

### "Authentication failed"

Delete `token.pickle` and re-run the uploader to re-authenticate.

### Download failures

The script includes retry logic with exponential backoff. If downloads still fail:
- Check your internet connection
- Verify the JSON file contains valid download URLs
- Some URLs may have expired (Apify links can expire)

### Rate limiting

The script includes small delays between requests. If you encounter rate limiting:
- Increase the delay in `tiktok_slideshow_analyzer.py` (line with `time.sleep`)
- Process smaller batches of data

## Security Notes

- `credentials.json` and `token.pickle` contain sensitive authentication data
- These files are ignored by git (see `.gitignore`)
- Never commit these files to version control
- Keep your credentials secure

## License

MIT License

## Contributing

Contributions welcome! Please open an issue or submit a pull request.
