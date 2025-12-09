from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

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