from django import forms
from .models import Usuarios

# Formulario LOGIN normal (para usuarios ya registrados)
class LoginForm(forms.Form):
    correo = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

# Formulario SOLO CORREO (Para validar Primer Ingreso o Recuperación)
class ValidarCorreoForm(forms.Form):
    correo = forms.EmailField(
        label="Ingresa tu correo autorizado",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ejemplo@correo.com'})
    )

# Formulario NUEVA CONTRASEÑA
class NuevaPasswordForm(forms.Form):
    password = forms.CharField(
        label="Crea tu contraseña", 
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    confirmar = forms.CharField(
        label="Repite la contraseña", 
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("confirmar")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data