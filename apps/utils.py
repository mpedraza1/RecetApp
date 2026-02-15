from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from .models import RecetaIngredientes, Recetas

def formatear_cantidad_inteligente(cantidad, unidad):
    """
    Tu función lógica para convertir gr a Kg, ml a L, etc.
    (Asegúrate de tener esta lógica definida aquí o importarla)
    """
    # Ejemplo rápido de lógica (ajusta según la tuya):
    if unidad.lower() == "gr" and cantidad >= 1000:
        return f"{cantidad / 1000:.2f}".replace(".", ","), "Kg"
    if unidad.lower() == "ml" and cantidad >= 1000:
        return f"{cantidad / 1000:.2f}".replace(".", ","), "L"
    
    # Formateo por defecto (con puntos para miles)
    cant_fmt = f"{int(cantidad):_}".replace("_", ".")
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
        total_en_bd = RecetaIngredientes.objects.count()
        print(f"--- DEBUG GLOBAL ---")
        print(f"Total de filas en la tabla RecetaIngredientes: {total_en_bd}")
        
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