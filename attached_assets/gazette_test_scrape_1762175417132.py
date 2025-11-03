import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep

chrome_driver_path = r"C:\chromedriver\chromedriver-win64\chromedriver.exe"
service = Service(executable_path=chrome_driver_path)
driver = webdriver.Chrome(service=service)

def scrape_millicent_jobs():
    base_url = "https://gazette.education.govt.nz/vacancies/"
    driver.get(base_url)

    wait = WebDriverWait(driver, 15)

    # Select Teaching under Position
    try:
        teaching_box = wait.until(EC.element_to_be_clickable((By.XPATH, "//label[contains(.,'Teaching')]/input")))
        driver.execute_script("arguments[0].click();", teaching_box)
    except:
        print("⚠️ Could not tick Teaching")

    # Select Early learning
    try:
        early_box = wait.until(EC.element_to_be_clickable((By.XPATH, "//label[contains(.,'Early learning')]/input")))
        driver.execute_script("arguments[0].click();", early_box)
    except:
        print("⚠️ Could not tick Early learning")

    # Select Primary
    try:
        primary_box = wait.until(EC.element_to_be_clickable((By.XPATH, "//label[contains(.,'Primary')]/input")))
        driver.execute_script("arguments[0].click();", primary_box)
    except:
        print("⚠️ Could not tick Primary")

    # Click Search
    try:
        search_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Search')]")))
        driver.execute_script("arguments[0].click();", search_btn)
        sleep(3)
    except:
        print("⚠️ Could not click Search")

    all_jobs = []
    page = 1

    while True:
        print(f"\n🔎 Page {page}")
        sleep(2)

        job_cards = driver.find_elements(By.CSS_SELECTOR, "article.vacancy-item a")
        job_links = [a.get_attribute("href") for a in job_cards if "/vacancies/" in a.get_attribute("href")]

        if not job_links:
            break

        print(f" Found {len(job_links)} job links")

        for link in job_links:
            driver.get(link)
            sleep(2)

            # Job Title
            try:
                title = driver.find_element(By.CSS_SELECTOR, "h1").text.strip()
            except:
                title = "N/A"

            # Employer
            try:
                employer = driver.find_element(By.CSS_SELECTOR, "p.meta.vacancy-meta-header span.tag.bullet").text.strip()
            except:
                employer = "N/A"

            # Employment Type
            try:
                items = driver.find_elements(By.CSS_SELECTOR, "ul.meta.vacancy-meta li")
                employment_type = ", ".join([it.text.strip() for it in items if it.text.strip()])
            except:
                employment_type = "N/A"

            # Closing Date
            try:
                closing_date = driver.find_element(
                    By.XPATH, "//dt[normalize-space()='Closes']/following-sibling::dd[1]"
                ).text.strip()
            except:
                closing_date = "N/A"

            print(f" Job: {title} | Employer: {employer} | Closing: {closing_date}")
            all_jobs.append([title, employer, employment_type, closing_date, link])

        # Try next page
        try:
            next_btn = driver.find_element(By.LINK_TEXT, "Next")
            driver.execute_script("arguments[0].click();", next_btn)
            page += 1
        except:
            break

    # Save results
    with open("millicent_jobs.csv", "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Title", "Employer", "Employment Type", "Closing Date", "URL"])
        writer.writerows(all_jobs)

    driver.quit()
    print(f"\n✅ Saved {len(all_jobs)} filtered jobs into millicent_jobs.csv")

if __name__ == "__main__":
    scrape_millicent_jobs()
