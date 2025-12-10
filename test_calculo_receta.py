import pytest

# 1. La función Lógica (Esta SÍ recibe 'personas')
def calcular_receta(personas):
    harina = 50 * personas
    leche = 100 * personas
    return {'harina': harina, 'leche': leche}

# 2. La función de Prueba (Esta NO recibe nada en los paréntesis)
def test_calculo_receta():   # <--- ¡Déjalo vacío aquí! ()
    # El valor 10 se pone aquí abajo v
    resultado = calcular_receta(10) 
    
    assert resultado == {'harina': 500, 'leche': 1000}
    
#def test_calculo_receta():     #FALLA
#    resultado = calcular_receta(10)
#    
#    # CAMBIO AQUÍ: Puse 0 en lugar de 500 para forzar el error
#    assert resultado == {'harina': 0, 'leche': 1000}