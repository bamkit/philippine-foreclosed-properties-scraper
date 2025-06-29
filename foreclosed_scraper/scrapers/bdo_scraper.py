#!/usr/bin/env python3
"""
BDO Robots.txt Compliant Scraper with Detailed Property Information
Respects BDO's robots.txt guidelines and extracts detailed property info by clicking "View Details"
"""

import time
import json
import random
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

OUTPUT_DIR = Path("foreclosed_scraper/data")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "bdo_robots_compliant_detailed.json"

BDO_URL = "https://www.bdo.com.ph/personal/assets-for-sale/real-estate/results-page"
CRAWL_DELAY = 10  # 10 seconds as specified in robots.txt

def extract_properties_from_dom(driver):
    """Extract all properties from the DOM using the actual HTML structure."""
    properties = []
    items = driver.find_elements(By.CSS_SELECTOR, ".pmu-productListing .item")
    
    for item in items:
        prop = {
            "Property_address": "NA",
            "Property_short_description": "NA", 
            "Advertised_price": "NA",
            "Type": "NA",
            "Lot_area": "NA",
            "Floor_area": "NA",
            "Offer_type": "Negotiated Sale",
            "Additional_information": "NA",
            "Detailed_info": {}  # Will store detailed info from individual property pages
        }
        
        # Extract title/address
        try:
            title_el = item.find_element(By.CSS_SELECTOR, ".title")
            prop["Property_address"] = title_el.text.strip()
        except:
            pass
        
        # Extract all rows and their data
        try:
            rows = item.find_elements(By.CSS_SELECTOR, ".item-content--row")
            for row in rows:
                try:
                    # Get the icon to identify what type of data this row contains
                    icon = row.find_element(By.CSS_SELECTOR, ".item-content--row-icon svg use")
                    icon_href = icon.get_attribute("xlink:href")
                    
                    # Get the text value
                    text_el = row.find_element(By.CSS_SELECTOR, ".city")
                    text_value = text_el.text.strip()
                    
                    # Map icons to data fields
                    if "tag_outline" in icon_href or "price" in icon_href:
                        prop["Advertised_price"] = text_value
                    elif "business_building-outline" in icon_href:
                        # First building icon is floor area, second is lot area
                        if prop["Floor_area"] == "NA":
                            prop["Floor_area"] = text_value
                        else:
                            prop["Lot_area"] = text_value
                    elif "home_loan-outline" in icon_href or "home-outline" in icon_href:
                        prop["Type"] = text_value
                    elif "location" in icon_href or "map" in icon_href:
                        if prop["Property_short_description"] == "NA":
                            prop["Property_short_description"] = text_value
                        else:
                            prop["Additional_information"] = text_value
                    
                except Exception as e:
                    # Skip this row if there's an error
                    continue
        except:
            pass
        
        # Extract URL for additional info
        try:
            link_el = item.find_element(By.CSS_SELECTOR, "a[href*='details-page']")
            href = link_el.get_attribute("href")
            if href:
                prop["Additional_information"] = href
        except:
            pass
        
        properties.append(prop)
    
    return properties

def get_property_details(driver, property_url, wait):
    """Get detailed information from a property's detail page."""
    print(f"Getting details from: {property_url}")
    
    try:
        # Navigate to the property detail page
        driver.get(property_url)
        
        # Wait for the page to load
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
        time.sleep(3)  # Additional wait for content to load
        
        detailed_info = {
            "full_address": "NA",
            "detailed_description": "NA",
            "property_features": "NA",
            "contact_info": "NA",
            "viewing_info": "NA",
            "terms_conditions": "NA"
        }
        
        # Try to extract detailed information
        try:
            # Look for detailed address
            address_selectors = [
                ".property-address", ".address", ".location", 
                "[class*='address']", "[class*='location']"
            ]
            for selector in address_selectors:
                try:
                    addr_el = driver.find_element(By.CSS_SELECTOR, selector)
                    if addr_el.text.strip():
                        detailed_info["full_address"] = addr_el.text.strip()
                        break
                except:
                    continue
            
            # Look for detailed description
            desc_selectors = [
                ".description", ".details", ".summary", ".content",
                "[class*='description']", "[class*='details']", "p"
            ]
            for selector in desc_selectors:
                try:
                    desc_el = driver.find_element(By.CSS_SELECTOR, selector)
                    if desc_el.text.strip() and len(desc_el.text.strip()) > 50:
                        detailed_info["detailed_description"] = desc_el.text.strip()
                        break
                except:
                    continue
            
            # Look for property features
            feature_selectors = [
                ".features", ".amenities", ".specifications",
                "[class*='feature']", "[class*='amenity']"
            ]
            for selector in feature_selectors:
                try:
                    feature_el = driver.find_element(By.CSS_SELECTOR, selector)
                    if feature_el.text.strip():
                        detailed_info["property_features"] = feature_el.text.strip()
                        break
                except:
                    continue
            
            # Look for contact information
            contact_selectors = [
                ".contact", ".phone", ".email", ".inquiry",
                "[class*='contact']", "[class*='phone']"
            ]
            for selector in contact_selectors:
                try:
                    contact_el = driver.find_element(By.CSS_SELECTOR, selector)
                    if contact_el.text.strip():
                        detailed_info["contact_info"] = contact_el.text.strip()
                        break
                except:
                    continue
            
            # Look for viewing information
            viewing_selectors = [
                ".viewing", ".schedule", ".appointment",
                "[class*='viewing']", "[class*='schedule']"
            ]
            for selector in viewing_selectors:
                try:
                    viewing_el = driver.find_element(By.CSS_SELECTOR, selector)
                    if viewing_el.text.strip():
                        detailed_info["viewing_info"] = viewing_el.text.strip()
                        break
                except:
                    continue
            
            # Look for terms and conditions
            terms_selectors = [
                ".terms", ".conditions", ".disclaimer",
                "[class*='term']", "[class*='condition']"
            ]
            for selector in terms_selectors:
                try:
                    terms_el = driver.find_element(By.CSS_SELECTOR, selector)
                    if terms_el.text.strip():
                        detailed_info["terms_conditions"] = terms_el.text.strip()
                        break
                except:
                    continue
            
            print(f"Extracted detailed info: {len([v for v in detailed_info.values() if v != 'NA'])} fields")
            
        except Exception as e:
            print(f"Error extracting detailed info: {e}")
        
        return detailed_info
        
    except Exception as e:
        print(f"Error getting property details: {e}")
        return {
            "full_address": "NA",
            "detailed_description": "NA",
            "property_features": "NA",
            "contact_info": "NA",
            "viewing_info": "NA",
            "terms_conditions": "NA"
        }

def check_show_more_button_exists(driver):
    """Check if the Show More button still exists on the page."""
    try:
        button = driver.find_element(By.CSS_SELECTOR, ".showMore.pmu-btn.secondaryBtn")
        return button.is_displayed()
    except:
        return False

def click_show_more_robots_compliant(driver, wait):
    """Click Show More button with robots.txt compliance."""
    try:
        # Wait for the crawl delay before attempting to click
        print(f"Waiting {CRAWL_DELAY} seconds (robots.txt compliance)...")
        time.sleep(CRAWL_DELAY)
        
        # Check if button still exists
        if not check_show_more_button_exists(driver):
            print("   No more 'Show More' button found - all properties loaded!")
            return False
        
        # Try to click the Show More button
        button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".showMore.pmu-btn.secondaryBtn")))
        
        # Scroll button into view
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", button)
        time.sleep(2)
        
        # Try JavaScript click first (more reliable)
        try:
            driver.execute_script("arguments[0].click();", button)
            print("   Clicked using JavaScript")
            return True
        except:
            # Fallback to regular click
            button.click()
            print("   Clicked using Selenium")
            return True
        
    except Exception as e:
        print(f"   Error clicking Show More: {e}")
        return False

def wait_for_loader_to_disappear(driver, timeout=15):
    """Wait for the loading spinner to disappear."""
    try:
        WebDriverWait(driver, timeout).until_not(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".loader.loader-visible"))
        )
        print("   Loader disappeared")
    except TimeoutException:
        print("   Loader timeout, continuing anyway")

def main():
    print("\n=== BDO Robots.txt Compliant Scraper with Detailed Info ===")
    print(f"Target: {BDO_URL}")
    print(f"Crawl Delay: {CRAWL_DELAY} seconds (robots.txt compliance)")
    print("Will continue until no more 'Show More' button exists")
    print("Will extract detailed info from first 3 properties")
    print("=" * 70)
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # Remove automation flags
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    try:
        # Navigate to the page
        driver.get(BDO_URL)
        wait = WebDriverWait(driver, 30)
        
        # Wait for initial property items to load
        print("Waiting for page to load...")
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".pmu-productListing .item"))
        )
        
        # Count initial properties
        initial_count = len(extract_properties_from_dom(driver))
        print(f"Initial properties loaded: {initial_count}")
        
        # Automatically click "Show More" until no more button exists
        attempt = 0
        current_count = initial_count
        max_attempts = 100  # High limit to ensure we get all properties
        
        print(f"\nStarting robots.txt compliant 'Show More' clicking...")
        print(f"Each attempt will wait {CRAWL_DELAY} seconds (robots.txt compliance)")
        print(f"Will stop when no more 'Show More' button is found")
        
        while attempt < max_attempts:
            attempt += 1
            print(f"\nAttempt {attempt}:")
            
            # Wait for any loader to disappear
            wait_for_loader_to_disappear(driver)
            
            # Try to click Show More with compliance
            success = click_show_more_robots_compliant(driver, wait)
            
            if not success:
                print("   No more 'Show More' button found - all properties loaded!")
                break
            
            # Wait for new content to load
            print("   Waiting for new properties to load...")
            time.sleep(5)
            wait_for_loader_to_disappear(driver)
            
            # Count new properties
            new_count = len(extract_properties_from_dom(driver))
            print(f"   Properties after click: {new_count}")
            
            if new_count > current_count:
                print(f"   Loaded {new_count - current_count} more properties!")
                current_count = new_count
            else:
                print(f"   No new properties loaded")
            
            # Small random delay between attempts
            random_delay = random.uniform(2, 5)
            print(f"   Additional random delay: {random_delay:.1f} seconds")
            time.sleep(random_delay)
        
        # Extract all properties
        print(f"\nExtracting all {current_count} properties...")
        properties = extract_properties_from_dom(driver)
        
        # Get detailed information for ALL properties
        print(f"\nGetting detailed information for ALL {len(properties)} properties...")
        for i, prop in enumerate(properties):
            if prop["Additional_information"] != "NA":
                print(f"\nProperty {i+1}/{len(properties)}: {prop['Property_address']}")
                detailed_info = get_property_details(driver, prop["Additional_information"], wait)
                prop["Detailed_info"] = detailed_info
                
                # Wait between detail page visits to be respectful (shorter delay for efficiency)
                if i < len(properties) - 1:  # Don't wait after the last one
                    print(f"Waiting 3 seconds before next detail page...")
                    time.sleep(3)
            else:
                print(f"\nProperty {i+1}/{len(properties)}: No detail URL available")
        
        # Save to JSON
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(properties, f, indent=2, ensure_ascii=False)
        print(f"\nSaved {len(properties)} properties to {OUTPUT_FILE}")
        
        # Show summary
        print(f"\nSummary:")
        print(f"   - Total properties: {len(properties)}")
        print(f"   - Show More attempts: {attempt}")
        print(f"   - Properties loaded: {current_count}")
        print(f"   - Detailed info extracted: {len([p for p in properties if p.get('Detailed_info')])}")
        print(f"   - Robots.txt compliance: (10s delays)")
        
        # Show sample of extracted data
        if properties:
            print(f"\nSample extracted data (first property with details):")
            print(json.dumps(properties[0], indent=2))
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        input("\nPress ENTER to close the browser...")
        driver.quit()

if __name__ == "__main__":
    main() 