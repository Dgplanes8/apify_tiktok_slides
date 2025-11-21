#!/bin/bash
#
# TikTok Slideshow Analyzer - Complete Workflow
# This script runs the complete analysis and upload workflow
#

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}TikTok Slideshow Analyzer${NC}"
echo -e "${BLUE}================================${NC}"
echo

# Check if input file provided
if [ $# -eq 0 ]; then
    echo -e "${RED}Error: No input file specified${NC}"
    echo "Usage: $0 <input.json> [output_directory] [drive_folder_name]"
    echo
    echo "Examples:"
    echo "  $0 data.json"
    echo "  $0 data.json my_analysis"
    echo "  $0 data.json my_analysis 'TikTok Campaign 2024'"
    exit 1
fi

INPUT_FILE="$1"
OUTPUT_DIR="${2:-output}"
DRIVE_FOLDER="${3:-}"

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo -e "${RED}Error: Input file '$INPUT_FILE' not found${NC}"
    exit 1
fi

# Step 1: Run analyzer
echo -e "${GREEN}Step 1: Analyzing TikTok data...${NC}"
python3 tiktok_slideshow_analyzer.py "$INPUT_FILE" -o "$OUTPUT_DIR"

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Analysis failed${NC}"
    exit 1
fi

echo
echo -e "${GREEN}Analysis complete!${NC}"
echo

# Ask user if they want to upload to Google Drive
read -p "Upload to Google Drive? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Step 2: Upload to Google Drive
    echo
    echo -e "${GREEN}Step 2: Uploading to Google Drive...${NC}"

    if [ -z "$DRIVE_FOLDER" ]; then
        python3 gdrive_uploader.py -d "$OUTPUT_DIR"
    else
        python3 gdrive_uploader.py -d "$OUTPUT_DIR" -n "$DRIVE_FOLDER"
    fi

    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Upload failed${NC}"
        exit 1
    fi

    echo
    echo -e "${GREEN}Upload complete!${NC}"
fi

echo
echo -e "${BLUE}================================${NC}"
echo -e "${GREEN}Workflow complete!${NC}"
echo -e "${BLUE}================================${NC}"
echo
echo "Output location: $OUTPUT_DIR"
echo
