def _make_driver():
    headless = os.getenv("HEADLESS", "1").strip().lower() not in ("0","false","no")
    opts = Options()
    if headless: opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--user-data-dir=C:\\temp\\selenium_profile")  # <<< this avoids profile conflict
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=opts)
        driver.set_page_load_timeout(60)
        return driver
    except WebDriverException as e:
        raise RuntimeError("❌ Failed to launch Chrome. Ensure Chrome is installed. Or set HEADLESS=0 to see the browser.") from e
