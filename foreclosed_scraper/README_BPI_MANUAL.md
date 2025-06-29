# BPI Manual HTML Download & Parsing Guide

This guide explains how to manually download BPI/Buena Mano property listings as HTML files and extract the data using the provided parser.

---

## Step 1: Open the BPI/Buena Mano Website
- Go to: [https://www.buenamano.ph/search/result](https://www.buenamano.ph/search/result)
- Use the search filters (location, property type, price, etc.) to narrow down the results if you want.

---

## Step 2: Download Search Results Pages
- For each page you want to save:
  1. Navigate to the page (e.g., page 1, 2, 3, ...).
  2. Right-click anywhere on the page (not on an image or link).
  3. Select **"Save As..."** or **"Save page as..."** from your browser menu.
  4. In the dialog:
     - **Save as type:** "Webpage, Complete"
     - **File name:** Use a descriptive name, e.g., `bpi_page_1.html`, `bpi_page_2.html`, etc.
  5. Save the file to your computer.

---

## Step 3: Copy the Downloaded HTML Files
- Move or copy all the `.html` files you downloaded into this folder:
  ```
  foreclosed_scraper/data/bpi_manual_html/
  ```
- (Create this folder if it doesn't exist.)

---

## Step 4: (Optional) Download Property Detail Pages
- For more detailed info:
  1. Click a property link to open its detail page.
  2. Save the detail page as above (e.g., `bpi_detail_123.html`).
  3. Place it in the same `bpi_manual_html` folder.

---

## Step 5: Run the Manual HTML Parser
- In your terminal, run:
  ```
  python foreclosed_scraper/bpi_manual_html_parser.py
  ```
- The script will:
  - Parse all `.html` files in `foreclosed_scraper/data/bpi_manual_html/`
  - Extract property data
  - Save the results to:
    ```
    foreclosed_scraper/data/bpi_manual_parsed.json
    ```

---

## Step 6: Check Your Results
- Open `foreclosed_scraper/data/bpi_manual_parsed.json` to see the extracted property data (in JSON format).

---

## Tips
- You do **not** need to download all 86 pages. Use filters or sample a few pages.
- The parser will skip files it doesn't recognize as search results or property detail pages.
- If you add more HTML files later, just re-run the parser.

---

## Troubleshooting
- If you see "No HTML files found," make sure your files are in the correct folder and have a `.html` extension.
- If you see "Unknown page type," the file may not be a search results or property detail page. 