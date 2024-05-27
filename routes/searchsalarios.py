from flask import Blueprint, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time

searchsalarios_bp = Blueprint('searchsalarios', __name__)

@searchsalarios_bp.route('/searchsalarios', methods=['POST'])
def buscar():
    nombre = request.json['nombre']
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("start-maximized")
    chrome_options.add_argument("disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(executable_path='./chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        driver.get("https://nominatransparente.rhnet.gob.mx/nomina-APF")
        time.sleep(5)
        boton_continuar = WebDriverWait(driver, 6).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.waves-effect.btn-flat.fadeIn2"))
        )
        boton_continuar.click()
        body_element = driver.find_element(By.CSS_SELECTOR, 'body')
        ActionChains(driver).move_to_element(body_element).click().perform()
        input_nombre = WebDriverWait(driver, 6).until(
            EC.visibility_of_element_located((By.ID, "apfName"))
        )
        input_nombre.click()
        input_nombre.send_keys(nombre)
        input_nombre.send_keys(Keys.TAB)
        boton_buscar = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn.btn-custom"))
        )
        boton_buscar.click()
        time.sleep(4)
        tabla_resultados = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table"))
        )
        filas = tabla_resultados.find_elements(By.TAG_NAME, "tr")
        if not filas:
            return jsonify({"message": "No se ha encontrado información"})
        resultados = []
        encabezados = ["#", "Nombre", "Institución", "Puesto", "Sueldo_bruto_mensual", "Sueldo_neto_estimado"]
        for fila in filas[1:]:  # Ignorar la primera fila de encabezados
            columnas = fila.find_elements(By.TAG_NAME, "td")
            datos_fila = {}
            for i in range(len(columnas)):
                datos_fila[encabezados[i]] = columnas[i].text
            resultados.append(datos_fila)
        return jsonify(resultados)
    except Exception as e:
        return jsonify({"error": "No se ha encontrado información debido a: " + str(e)})
    finally:
        driver.quit()
