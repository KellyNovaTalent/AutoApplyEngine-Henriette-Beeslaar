import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

# Path to ChromeDriver
chrome_driver_path = r"C:\chromedriver\chromedriver-win64\chromedriver.exe"
service = Service(executable_path=chrome_driver_path)
driver = webdriver.Chrome(service=service)

print("🌍 Opening Gazette site...")
driver.get("https://gazette.education.govt.nz/vacancies/")
time.sleep(8)  # wait longer for dynamic content

page_source = driver.page_source
print("✅ Page source length:", len(page_source))

# Save the HTML so we can inspect it
with open("gazette_page.html", "w", encoding="utf-8") as f:
    f.write(page_source)

print("✅ Saved page source to gazette_page.html")

driver.quit()
