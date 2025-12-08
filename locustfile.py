from locust import HttpUser, task, between

class UsuarioRecetApp(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        """
        Esto se ejecuta UNA vez cuando 'nace' un usuario simulado.
        Lo usamos para loguearnos.
        """
        response = self.client.post("", {
            "correo": "xxx@coanil.cl",  
            "password": "xxx"               
        })
        
        if response.status_code == 200 or response.status_code == 302:
            print("Login exitoso (Usuario simulado creado)")
        else:
            print("Falló el login")

    @task(2)
    def ver_formulario_receta(self):
        """
        Tarea: Entrar a ver el formulario de crear receta.
        El (2) significa que es el doble de probable que haga esto.
        """
        self.client.get("/creacion-recetas/")

    @task(1)
    def ver_usuarios(self):
        """
        Tarea: Intentar ver la lista de usuarios (si tiene permisos).
        """
        self.client.get("/usuarios/")