import json
import os
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def get_failed_rules(driver):
    panel = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//mat-expansion-panel[.//strong[contains(text(),'Resultado de la validaci')]]",
            )
        )
    )
    header = panel.find_element(By.CSS_SELECTOR, "mat-expansion-panel-header")
    if header.get_attribute("aria-expanded") != "true":
        header.click()

    WebDriverWait(driver, 30).until(
        lambda _: len(panel.find_elements(By.CSS_SELECTOR, "table tbody tr")) > 0
    )

    failed = []
    for row in panel.find_elements(By.CSS_SELECTOR, "table tbody tr"):
        tds = row.find_elements(By.CSS_SELECTOR, "td")
        if len(tds) < 2:
            continue
        bg = (
            tds[0]
            .find_element(By.CSS_SELECTOR, "div.circular-signal")
            .value_of_css_property("background-color")
        )
        rgb = tuple(int(x) for x in re.findall(r"\d+", bg)[:3])
        if rgb and rgb[0] > rgb[1] and rgb[0] > rgb[2]:
            failed.append(tds[1].text.strip())

    return ", ".join(failed)


def save_results(results):
    with open("resultados.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


output_dir = "outputs"
images = [f"{output_dir}/{file}" for file in os.listdir(output_dir)]

results = {}
if os.path.exists("resultados.json"):
    with open("resultados.json", "r", encoding="utf-8") as f:
        results = json.load(f)

driver = webdriver.Chrome()

for image in images:
    basename = os.path.basename(image)
    if basename in results and results[basename].get("ESTADO"):
        print(f"[SKIP] {image} ya tiene resultado")
        continue
    results[basename] = {}
    driver.get("https://siucarne.sunedu.gob.pe/carne/validacion")
    file_input = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="file"]'))
    )
    file_input.send_keys(os.path.abspath(image))
    print(f"[OK] uploaded {image}")

    WebDriverWait(driver, 120).until(
        lambda d: d.execute_script(
            "return (document.getElementById('g-recaptcha-response')?.value || '').length > 0"
        )
    )
    print("[OK] captcha resuelto")

    upload_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'SUBIR ARCHIVO')]"))
    )
    upload_button.click()

    WebDriverWait(driver, 30).until(
        lambda d: any(
            estado in d.find_element(By.CLASS_NAME, "estado-container").text
            for estado in ("INVALIDO", "VALIDO")
        )
    )
    estado_container = driver.find_element(By.CLASS_NAME, "estado-container")
    results[basename]["ESTADO"] = estado_container.text
    results[basename]["FALLAS"] = get_failed_rules(driver)
    save_results(results)

driver.quit()

print(results)
