from django.shortcuts import redirect
from functools import wraps
from .models import Usuarios 

def login_personalizado_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        usuario_id = request.session.get('usuario_id')
        
        if not usuario_id:
            return redirect('login') 
            
        try:
            usuario = Usuarios.objects.get(pk=usuario_id)

            request.custom_user = usuario 
            
            return view_func(request, *args, **kwargs)
            
        except Usuarios.DoesNotExist:
            request.session.flush() 
            return redirect('login')
    
    return _wrapped_view