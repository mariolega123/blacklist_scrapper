from flask import Blueprint, request, jsonify, send_file
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import requests
from bs4 import BeautifulSoup
import re

search_bp = Blueprint('search', __name__)

@search_bp.route('/search', methods=['POST'])
def search():
    nombre_completo = request.json['nombre'].lower()

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("start-maximized")
    options.add_argument("disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    service = Service(executable_path='./chromedriver')
    driver = webdriver.Chrome(service=service, options=options)

    try:
        target_url = f"https://www.opensanctions.org/search/?q={'+'.join(nombre_completo.split())}"
        driver.get(target_url)
        time.sleep(random.uniform(1, 3))

        found = False
        links = driver.find_elements(By.XPATH, f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{nombre_completo}')]")
        for link in links:
            if link.text.lower() == nombre_completo:
                found = True
                href = link.get_attribute('href')
                
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36"
                }

                response = requests.get(href, headers=headers)
                
                if response.status_code == 200:
                    html_content = response.text
                    
                    with open("info.txt", "w", encoding="utf-8") as file:
                        file.write(html_content)
                    
                    soup = BeautifulSoup(html_content, 'html.parser')

                    name = request.json['nombre']
                    birth_date = soup.find('time', {'datetime': True}).text.strip() if soup.find('time', {'datetime': True}) else "No disponible"
                    nationality = soup.find('span', string=re.compile("Nationality", re.IGNORECASE)).text.strip() if soup.find('span', string=re.compile("Nationality", re.IGNORECASE)) else "No disponible"
                    country = soup.find('th', string='Country').find_next_sibling('td').text.strip() if soup.find('th', string='Country') else "No disponible"
                    positions = [span.text.strip() for span in soup.select('td span') if 'government' in span.text] or ["No disponible"]
                    positions_occupied = [span.text.strip() for span in soup.select('td span') if '(' in span.text and ')' in span.text] or ["No disponible"]
                    relationships = [span.text.strip() for span in soup.select('td span') if '(' in span.text and ')' not in span.text] or ["No disponible"]

                    family_members = []
                    family_table = soup.find('table', class_='table table-sm table-bordered')
                    if family_table and 'Family members' in family_table.get_text():
                        for row in family_table.find_all('tr')[1:]:
                            cells = row.find_all('td')
                            if len(cells) >= 2:
                                member_name = cells[0].get_text(strip=True)
                                relationship = cells[1].get_text(strip=True)
                                family_members.append(f"{member_name} ({relationship})")

                    if not family_members:
                        family_members = ["No disponible"]

                    data = {
                        "Name": name,
                        "Birth_date": birth_date,
                        "Nationality": nationality,
                        "Country": country,
                        "Position": positions,
                        "Position_occupied": positions_occupied,
                        "Last_changed": "2024-04-11",
                        "Family_members": family_members
                    }

                    return jsonify(data)
                else:
                    return jsonify({"message": "Error al hacer la solicitud. Código de estado: " + str(response.status_code)})

        if not found:
            return jsonify({"message": "No se ha encontrado información."})

    finally:
        driver.quit()

