import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select 

def probar_creacion_completa():
    print("Iniciando navegador...")
    driver = webdriver.Chrome()

    try:
        # --- PASO 1: LOGIN ---
        driver.get("http://127.0.0.1:8000/")
        time.sleep(1)
        driver.find_element(By.NAME, "correo").send_keys("xxx@coanil.cl") 
        driver.find_element(By.NAME, "password").send_keys("xxx")         
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(2)

        # --- PASO 2: LLENAR RECETA ---
        if "creacion-recetas" in driver.current_url:
            print("Login OK. Llenando formulario de receta...")
            
            # 1. Nombre de la Receta (Texto normal)
            driver.find_element(By.NAME, "nombre_receta").send_keys("Receta Automática Selenium")

            # 2. Tipo de Comida (Menú Desplegable)
            select_elemento = driver.find_element(By.NAME, "tipo_comida")
            select_objeto = Select(select_elemento)
            select_objeto.select_by_index(1) 

            # 3. Ingrediente (Menú Desplegable)
            select_ing = Select(driver.find_element(By.NAME, "ingrediente"))
            select_ing.select_by_index(1) 

            # 4. Cantidad (Texto/Número)
            driver.find_element(By.NAME, "cantidad").send_keys("1.5")

            # 5. Unidad (Menú Desplegable)
            select_unidad = Select(driver.find_element(By.NAME, "unidad"))
            select_unidad.select_by_index(1) 

            # 6. Enviar Formulario
            print("Enviando formulario...")
            driver.find_element(By.XPATH, "//button[@type='submit']").click()
            
            time.sleep(2)

            # --- PASO 3: VERIFICAR ÉXITO ---  
            codigo_fuente = driver.page_source
            if "Receta agregada correctamente" in codigo_fuente:
                print("PRUEBA EXITOSA: La receta se guardó y apareció el mensaje de éxito.")
            elif "creacion-recetas" in driver.current_url:
                print("Formulario enviado. Verificando si hay errores...")
                if "error" in codigo_fuente or "inválido" in codigo_fuente:
                    print("FALLO: El sistema devolvió un error de validación.")
                else:
                    print("APROBADO (Probable): Seguimos en el formulario (reinicio) sin errores visibles.")
            else:
                 print(f"Redirección detectada a: {driver.current_url}")

        else:
            print("No se pudo entrar al formulario de recetas.")

    except Exception as e:
        print(f"ERROR TÉCNICO: {e}")

    finally:
        print("Cerrando en 5 segundos...")
        time.sleep(5)
        driver.quit()

if __name__ == "__main__":
    probar_creacion_completa()