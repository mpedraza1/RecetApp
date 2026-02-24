from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from .models import RecetaIngredientes, Recetas

def formatear_cantidad_inteligente(cantidad, unidad):
    """
    Convierte unidades y mantiene decimales para evitar subestimar cantidades.
    """
    # 1. Conversión de unidades (mantiene decimales)
    if unidad.lower() == "gr" and cantidad >= 1000:
        return f"{cantidad / 1000:.2f}".replace(".", ","), "Kg"
    if unidad.lower() == "ml" and cantidad >= 1000:
        return f"{cantidad / 1000:.2f}".replace(".", ","), "L"
    
    # 2. Formateo por defecto
    # Si el número tiene decimales (ej: 1.5), los mostramos con coma.
    # Si es un número redondo (ej: 2.0), lo mostramos sin decimales.
    if cantidad % 1 == 0:
        cant_fmt = f"{int(cantidad):_}".replace("_", ".")
    else:
        # Usamos 2 decimales, cambiamos punto por coma y agregamos separador de miles
        cant_fmt = f"{cantidad:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
    return cant_fmt, unidad

def obtener_calculo_receta(id_receta, comensales):
    """
    Busca una receta y procesa sus ingredientes multiplicados por los comensales.
    """
    if not id_receta:
        return None
    comensales = int(comensales)
        
    try:
        receta = Recetas.objects.get(id_receta=id_receta)
        items = RecetaIngredientes.objects.filter(id_receta=receta)
        if not items.exists():
            print(f" Alerta: La receta '{receta.nombre}' (ID: {id_receta}) no tiene ingredientes configurados.")
            return [] 

        
        
        lista_final = []
        for item in items:
            cantidad_total = item.cantidad * comensales
            unidad_orig = str(item.unidad) if item.unidad else ""

            # Aplicamos el formateo inteligente una sola vez aquí
            cant_fmt, unidad_fmt = formatear_cantidad_inteligente(cantidad_total, unidad_orig)
            
            # Formateo de la base teórica (para la tabla)
            base_fmt = f"{int(item.cantidad):_}".replace("_", ".")

            lista_final.append({
                "ingrediente": item.id_ingrediente.nombre,
                "cantidad_base": f"{base_fmt} {unidad_orig}",
                "unidad": unidad_fmt,
                "cantidad_total": cant_fmt
            })
        
        # Opcional: Ordenar por nombre de ingrediente
        lista_final.sort(key=lambda x: x['ingrediente'])
        return lista_final
        
    except Recetas.DoesNotExist:
        return None

def render_to_pdf(template_src, context_dict={}):
    try:
        template = get_template(template_src)
        html  = template.render(context_dict)
        result = BytesIO()
        
        # Convertimos HTML a PDF
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
        
        if not pdf.err:
            return HttpResponse(result.getvalue(), content_type='application/pdf')
        
        # Si xhtml2pdf reporta un error interno
        print("⚠️ xhtml2pdf reportó un error en la generación.")
        return HttpResponse(f"Error generando el PDF: {html}", status=500)

    except Exception as e:
        # Si explota el código por cualquier otra razón
        print(f"❌ Error fatal en render_to_pdf: {e}")
        return HttpResponse(f"Excepción: {e}", status=500)