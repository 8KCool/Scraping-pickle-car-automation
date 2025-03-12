from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd

# Set up Selenium WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()), options=options
)

# Open Pickles website
URL = "https://www.pickles.com.au/used/search/lob/cars-motorcycles/cars?contentkey=all-cars"
driver.get(URL)

# Wait for the page to load
wait = WebDriverWait(driver, 10)
wait.until(
    EC.presence_of_element_located((By.CSS_SELECTOR, ".content-grid_gridCard__vWoIs"))
)

car_data = []

while True:
    print("Scraping current page...")

    # Find all car listings on the current page
    cars = driver.find_elements(By.CSS_SELECTOR, ".content-grid_gridCard__vWoIs")
    print(cars.__len__())
    for car in cars:
        try:
            title = car.find_element(
                By.CSS_SELECTOR, ".content-title_title__0QJcW span"
            ).text
            subtitle = car.find_element(
                By.CSS_SELECTOR, ".content-title_subtitle__cTjkK span"
            ).text
            # Updated price extraction
            try:
                price_element = car.find_element(By.CSS_SELECTOR, ".pds-button-label")
                price = price_element.text.strip()
                if not price or price.lower() == "enquire" or "buy" in price.lower() or price.lower() == "proposed" or price.lower().startswith("lot"):
                    price = price if price else "N/A"
            except:
                price = "N/A"
            location = car.find_element(
                By.CSS_SELECTOR, ".content-utility_textclamp1__CaxUr"
            ).text
            link = car.find_element(
                By.CSS_SELECTOR, "a[id^='ps-ccg-product-card-link']"
            ).get_attribute("href")

            car_data.append(
                {
                    "Title": title,
                    "SubTitle": subtitle,
                    "Price": price,
                    "Location": location,
                    "URL": link,
                }
            )

        except Exception as e:
            print(f"Error extracting data: {e}")

    # Find and click the "Next" button (if available)
    try:
        next_button = driver.find_element(
            By.CSS_SELECTOR,
            "button.content-footer_buttonmedium__6NPt9:has(span.pds-icon-chevron--right)",
        )
        if next_button.is_enabled() and next_button.is_displayed():
            driver.execute_script("arguments[0].click();", next_button)
            time.sleep(3)  # Wait for new page to load
        else:
            print("Next button is not clickable. Exiting...")
            break
    except Exception as e:
        print(f"No more pages or error finding next button: {e}")
        break

# Close the browser
driver.quit()

# Save data to an Excel file

print(f"car_data length: {len(car_data)}")
df = pd.DataFrame(car_data)
df.to_excel("repairable_writeoff_cars.xlsx", index=False)

print("✅ Data successfully scraped and saved!")
