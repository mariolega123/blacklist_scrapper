from flask import Blueprint, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from twocaptcha import TwoCaptcha
import time

cfe_bp = Blueprint('cfe', __name__)

def click_specific(driver, x, y):
    body = driver.find_element(By.TAG_NAME, 'body')
    action = webdriver.common.action_chains.ActionChains(driver)
    action.move_to_element_with_offset(body, x, y)
    action.click()
    action.perform()
    print(f"Clic en la posición específica ({x}, {y})")

@cfe_bp.route('/cfe', methods=['POST'])
def cfe():
    data = request.json
    nombre = data.get('nombre')
    rpu = data.get('rpu')
    api_key = 'ff5d680e7e3ad9a91e99cb0f27e0479e'
    
    if not nombre or not rpu:
        return jsonify({"error": "Nombre y RPU son requeridos"}), 400
    
    url = "https://app.cfe.mx/aplicaciones/CCFE/SolicitudesCFE/Solicitudes/ConsultaTuReciboLuzGmx"
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--headless")  # Modo headless
    chrome_options.add_argument("--window-size=1920x1080")  # Establecer tamaño de ventana
    chrome_options.add_argument("disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, como Gecko) Chrome/93.0.4577.82 Safari/537.36')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    service = Service(executable_path='./chromedriver')
    
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        while True:
            driver.get(url)
            print("Página cargada.")

            # Rellenar el formulario
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "ctl00_MainContent_txtNombre")))

                nombre_field = driver.find_element(By.ID, "ctl00_MainContent_txtNombre")
                nombre_field.send_keys(nombre)
                print("Campo 'Nombre' rellenado.")
                
                rpu_field = driver.find_element(By.ID, "ctl00_MainContent_txtRPU")
                rpu_field.send_keys(rpu)
                print("Campo 'RPU' rellenado.")
                
                lada_field = driver.find_element(By.ID, "ctl00_MainContent_tbLada")
                lada_field.send_keys("332")
                print("Campo 'Lada' rellenado.")
                
                tel_field = driver.find_element(By.ID, "ctl00_MainContent_txtTel")
                tel_field.send_keys("53328900")
                print("Campo 'Teléfono' rellenado.")
                
                email_field = driver.find_element(By.ID, "ctl00_MainContent_txtCorreoElectronico")
                email_field.send_keys("marioarturo1407@gmail.com")
                print("Campo 'Correo Electrónico' rellenado.")
                
                # Agregar espera adicional de 2 segundos después de escribir el correo
                print("Esperando 2 segundos después de rellenar el correo...")
                time.sleep(2)
                
                # Guardar el site key antes del clic
                original_site_key = driver.find_element(By.CLASS_NAME, "g-recaptcha").get_attribute('data-sitekey')
                print(f"Site key original: {original_site_key}")
                
                # Clic en la posición específica después de rellenar el campo de correo electrónico
                click_specific(driver, 640, 80)
                
                print("Esperando 2 segundos...")
                time.sleep(2)  # Esperar 2 segundos
                
                # Comprobar si el site key ha cambiado
                new_site_key = driver.find_element(By.CLASS_NAME, "g-recaptcha").get_attribute('data-sitekey')
                if new_site_key == original_site_key:
                    print("El site key no ha cambiado.")
                else:
                    print(f"Site key ha cambiado: {new_site_key}")

                print(f"Resolviendo CAPTCHA con site key: {new_site_key}")
                solver = TwoCaptcha(api_key)
                captcha_solution = solver.recaptcha(sitekey=new_site_key, url=driver.current_url)

                if captcha_solution.get('code'):
                    print(f"Captcha resuelto, ID del captcha: {captcha_solution['code']}")
                    driver.execute_script(f"document.getElementById('g-recaptcha-response').innerHTML = '{captcha_solution['code']}';")
                    
                    # Presionar el botón "Continuar" después de resolver el CAPTCHA
                    try:
                        continue_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "ctl00_MainContent_btnContinuar")))
                        continue_button.click()
                        print("Botón 'Continuar' presionado.")
                        
                        # Esperar a que la página recargue y obtener el HTML de la nueva página
                        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
                        new_page_url = driver.current_url
                        new_page_html = driver.page_source
                        print("Nueva página cargada. URL de la nueva página:")
                        print(new_page_url)
                        
                        # Verificar la URL y la presencia de la etiqueta de error
                        if new_page_url == "https://app.cfe.mx/aplicaciones/CCFE/SolicitudesCFE/Solicitudes/ConsultaTuReciboLuzGmx":
                            if '<span id="ctl00_MainContent_lblError">Por el momento el servicio no se encuentra disponible, favor de intentar más tarde.</span>' in new_page_html:
                                return jsonify({"status": "No validado", "link": new_page_url}), 200
                            else:
                                return jsonify({"status": "Reintenta", "link": new_page_url}), 200
                        else:
                            return jsonify({"status": "Validado correctamente", "link": new_page_url}), 200

                    except Exception as e:
                        print(f"Error al presionar el botón Continuar: {e}")
                        return jsonify({"status": "Error al presionar el botón Continuar.", "link": ""}), 200
                else:
                    print("Error al resolver el CAPTCHA.")
                    return jsonify({"status": "Error al resolver el CAPTCHA.", "link": ""}), 200
            except Exception as e:
                print(f"Error al rellenar el formulario: {e}")
                return jsonify({"status": "Error al rellenar el formulario.", "link": ""}), 200
    
    except Exception as e:
        print(f"Error durante el proceso: {e}")
        return jsonify({"status": str(e), "link": ""}), 200
    finally:
        driver.quit()
