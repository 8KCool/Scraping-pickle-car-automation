import json
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Set up logging
logging.basicConfig(
    filename="scraper.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# JSON File name to save the previous scraped data into local storage
STORE_JSON_FILE = "filter1.json"

# Filter URL to scrap the cars data
URL = "https://www.pickles.com.au/used/search/lob/cars-motorcycles/cars/state/qld?contentkey=all-cars&filter=and%255B0%255D%255Bprice%255D%255Ble%255D%3D30000%26and%255B1%255D%255Bor%255D%255B0%255D%255BbuyMethod%255D%3DBuy%2520Now%26and%255B1%255D%255Bor%255D%255B1%255D%255BbuyMethod%255D%3DEOI%26and%255B1%255D%255Bor%255D%255B2%255D%255BbuyMethod%255D%3DPickles%2520Online"


# Email credentials (use your actual email and password)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "vharbarynin@gmail.com"  # Update with your sender email
SENDER_PASSWORD = "tdao tbew tmya bizf"  # Update with your sender email password
RECEIVER_EMAIL = "vharbarynin@gmail.com"


# Function to send the email
def send_email(subject, body):
    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Secure the connection
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.close()
        logging.info(f"Email sent to {RECEIVER_EMAIL}")
        print(f"✅ Email sent to {RECEIVER_EMAIL}")
    except Exception as e:
        logging.error(f"Error sending email: {e}")
        print(f"❌ Error sending email: {e}")


# Function to load previous scraped data
def load_previous_data(filename=STORE_JSON_FILE):
    try:
        with open(filename, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


# Function to save the current scrape to a file
def save_scraped_data(data, filename=STORE_JSON_FILE):
    with open(filename, "w") as file:
        json.dump(data, file)


# Set up Selenium WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()), options=options
)

# Open Pickles website
driver.get(URL)

# Wait for the page to load
wait = WebDriverWait(driver, 10)
wait.until(
    EC.presence_of_element_located((By.CSS_SELECTOR, ".content-grid_gridCard__vWoIs"))
)

# Load previous data
previous_data = load_previous_data()


print(f"Saved Cars Count - {len(previous_data)} ")

car_data = []

# Scrape current data
print("Scraping start...")
while True:

    # Find all car listings on the current page
    cars = driver.find_elements(By.CSS_SELECTOR, ".content-grid_gridCard__vWoIs")

    for car in cars:
        try:
            title = car.find_element(
                By.CSS_SELECTOR, ".content-title_title__0QJcW span"
            ).text
            subtitle = car.find_element(
                By.CSS_SELECTOR, ".content-title_subtitle__cTjkK span"
            ).text
            price_element = car.find_element(By.CSS_SELECTOR, ".pds-button-label")
            price = price_element.text.strip() if price_element.text.strip() else "N/A"
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
            print("Scraping finished.")
            break
    except Exception as e:
        print(f"No more pages or error finding next button: {e}")
        break

# Close the browser
driver.quit()

print(f"Found {len(car_data)} cars this filter.")

# Compare current data with previous data to find new listings
new_data = [car for car in car_data if car not in previous_data]

# If there are new listings, send an email
if new_data:
    email_body = ""
    for car in new_data:
        email_body += f"Title: {car['Title']}\nSubTitle: {car['SubTitle']}\nPrice: {car['Price']}\nLocation: {car['Location']}\nURL: {car['URL']}\n\n"

    print(f"email-content {email_body} ")

    send_email("New Car Found", email_body)

    # Update the stored data with the new list
    save_scraped_data(car_data)

# Optionally log and print how many new items were scraped
logging.info(f"Found {len(new_data)} new car listings.")
print(f"Found {len(new_data)} new car listings.")
