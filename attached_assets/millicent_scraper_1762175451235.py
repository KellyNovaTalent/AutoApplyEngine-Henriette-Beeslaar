import csv
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ✅ Path to your ChromeDriver
chrome_driver_path = r"C:\chromedriver\chromedriver-win64\chromedriver.exe"
service = Service(executable_path=chrome_driver_path)
driver = webdriver.Chrome(service=service)

wait = WebDriverWait(driver, 10)

def select2_add(selector, text):
    """Helper to add an item in a Select2 filter."""
    try:
        box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        box.send_keys(text)
        time.sleep(1)
        box.send_keys(Keys.ENTER)
        print(f"✅ Selected {text}")
    except Exception as e:
        print(f"⚠️ Could not select {text}: {e}")

def scrape_job_detail(url):
    """Visit job detail page and scrape extra info, including email and phone."""
    data = {}
    if not url:
        return data

    driver.execute_script("window.open(arguments[0]);", url)
    driver.switch_to.window(driver.window_handles[-1])
    time.sleep(2)

    try:
        data["employment_type"] = driver.find_element(By.CSS_SELECTOR, ".title-byline").text.strip()
    except:
        data["employment_type"] = "N/A"

    try:
        data["closing_date"] = driver.find_element(By.CSS_SELECTOR, ".closing-date").text.strip()
    except:
        data["closing_date"] = "N/A"

    try:
        desc = driver.find_element(By.CSS_SELECTOR, "div.description").text.strip()
        data["description"] = desc[:500] + "..." if len(desc) > 500 else desc
    except:
        data["description"] = "N/A"

    try:
        contact_block = driver.find_element(By.CSS_SELECTOR, "div.contact").text.strip()
        data["contact"] = contact_block
    except:
        contact_block = ""
        data["contact"] = "N/A"

    # Extract email + phone
    text_blob = data.get("description", "") + " " + contact_block
    email_match = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text_blob)
    phone_match = re.findall(r"\+?\d[\d\s-]{7,}", text_blob)

    data["email"] = email_match[0] if email_match else "N/A"
    data["phone"] = phone_match[0] if phone_match else "N/A"

    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return data

def scrape_millicent_jobs():
    base_url = "https://gazette.education.govt.nz/vacancies/"
    driver.get(base_url)

    # --- Filters ---
    select2_add("#VacancySearchForm_VacancySearchForm_SectorsAndRoles_Holder li.select2-search input", "Early learning")
    select2_add("#VacancySearchForm_VacancySearchForm_SectorsAndRoles_Holder li.select2-search input", "Primary")
    select2_add("#VacancySearchForm_VacancySearchForm_SectorsAndRoles_Holder li.select2-search input", "Teaching")
    select2_add("#VacancySearchForm_VacancySearchForm_PositionTypes_Holder li.select2-search input", "Full time")

    try:
        keyword = driver.find_element(By.CSS_SELECTOR, "#VacancySearchForm_VacancySearchForm_Keywords")
        keyword.clear()
        keyword.send_keys("ECE Primary International")
    except Exception as e:
        print(f"⚠️ Could not type keywords: {e}")

    try:
        search_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        driver.execute_script("arguments[0].click();", search_btn)
    except Exception as e:
        print(f"⚠️ Could not click search: {e}")

    time.sleep(3)

    jobs = []
    page = 1

    # ✅ Debug: only scrape 2 pages for now
    while page <= 2:
        print(f"\n🔎 Page {page}")
        cards = driver.find_elements(By.CSS_SELECTOR, "article.vacancy-item")

        for c in cards:
            try:
                link = c.find_element(By.CSS_SELECTOR, "h3 a").get_attribute("href")
                title = c.find_element(By.CSS_SELECTOR, "h3 a").text.strip()
            except:
                link, title = None, "N/A"

            try:
                employer = c.find_element(By.CSS_SELECTOR, ".meta").text.strip()
            except:
                employer = "N/A"

            # ✅ Print everything (no filtering yet)
            print(f"🔎 Found job: {title} | Employer: {employer}")

            job_detail = scrape_job_detail(link)

            jobs.append([
                title,
                employer,
                job_detail.get("employment_type", "N/A"),
                job_detail.get("closing_date", "N/A"),
                job_detail.get("description", "N/A"),
                job_detail.get("contact", "N/A"),
                job_detail.get("email", "N/A"),
                job_detail.get("phone", "N/A"),
                link
            ])

        # Next page
        try:
            next_btn = driver.find_element(By.CSS_SELECTOR, "a[title='Go to next page']")
            driver.execute_script("arguments[0].click();", next_btn)
            time.sleep(3)
            page += 1
        except:
            print("✅ No more pages.")
            break

    # --- Save CSV ---
    with open("millicent_jobs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Title", "Employer", "Employment Type", "Closing Date", "Description", "Contact", "Email", "Phone", "Link"])
        writer.writerows(jobs)

    print(f"\n✅ Saved {len(jobs)} jobs with full details into millicent_jobs.csv")

if __name__ == "__main__":
    scrape_millicent_jobs()
    driver.quit()
