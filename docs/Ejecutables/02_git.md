# git: control de versiones

## Verificar la instalación
```powershell
git --version
```

## Iniciar el repositorio (una vez)
```powershell
git init
git branch -m main          # renombra la rama a "main" (estándar actual)
```

## Ver el estado (usar SIEMPRE antes de commitear)
```powershell
git status                  # detallado
git status --short          # resumido
```

## Commit de todo el proyecto
```powershell
git add .                   # ojo: con espacio entre "add" y "."
git status                  # revisar que no entren datos ni secretos
git commit -m "chore: ..."
```

## Commit de un archivo o carpeta específica
```powershell
git add <archivo_o_carpeta>
git commit -m "docs: ..."
```

## Ver el historial
```powershell
git log --oneline           # un commit por línea
git log --oneline -5        # solo los últimos 5
```

## Verificar qué regla del .gitignore ignora un archivo
```powershell
git check-ignore -v OLD/funciones.py .env
```
Muestra el archivo y la línea del `.gitignore` que lo excluye. Si un archivo **no aparece** en la salida, **no** está ignorado.

## Verificar que una carpeta NUNCA entró al historial (antes de publicar)
```powershell
git log --all --oneline -- OLD
```
Lista los commits que tocaron `OLD/`. Si no muestra nada, esa carpeta nunca se subió.

## Buscar texto sensible en los archivos versionados
```powershell
git grep -n -i "password" HEAD
```
Busca el texto en todo lo que está en el último commit. Úsalo antes de hacer público el repositorio.

## Conectar con GitHub y subir (primera vez)
```powershell
git remote add origin https://github.com/<usuario>/ppa-pipeline.git
git push -u origin main
```
`remote add` registra la dirección del repositorio en GitHub con el nombre `origin`. `push -u` sube la rama `main` y la deja vinculada, así que después basta con `git push`.

> 💡 Repositorio **privado** o **público** se elige al crearlo en GitHub. Para cambiarlo después: **Settings → General → Danger Zone → Change visibility**. Antes de hacerlo público, ejecuta las dos verificaciones de arriba.

## Subir cambios (después de la primera vez)
```powershell
git push
```
Envía a GitHub los commits locales que todavía no están allá.

## Ver a qué repositorio remoto está conectado
```powershell
git remote -v
```

## Ver qué archivos entraron realmente en el último commit
```powershell
git show --stat HEAD
```
Lista los archivos del último commit, con cuántas líneas cambiaron en cada uno. Sirve para confirmar que el commit contiene lo que dice su mensaje.

## Si la terminal queda en `(END)` o con `:` abajo
Es el **paginador** (`less`): git muestra la salida larga por páginas. Presiona **`q`** para salir. (`Espacio` baja una página; `/texto` busca.)

## Ver la salida sin paginador (una vez)
```powershell
git --no-pager show --stat HEAD
```
`--no-pager` va justo después de `git` e imprime todo directo en la terminal.

## Desactivar el paginador para siempre en `show` y `log`
```powershell
git config --global pager.show false
git config --global pager.log false
```
`--global` guarda la preferencia para todos tus repositorios.

## Mover o renombrar un archivo versionado
```powershell
git mv <ruta_actual> <ruta_nueva>
```
Mueve el archivo y deja el cambio en *staging*. Git lo registra como un movimiento, no como "borrado + archivo nuevo", y se conserva su historial.

## Probar varias rutas contra el .gitignore de una vez
```powershell
git check-ignore -v data/bronze/cmg.json logs/pipeline.log reporte.pbix .env.local
```
Muestra cada ruta ignorada junto con la regla que la ignora. Las que no aparecen **no** están ignoradas.

## Excepciones en el .gitignore
```gitignore
.env.*
!.env.example
```
El `!` crea una **excepción**: ignora `.env.local`, `.env.prod`, etc., pero **no** la plantilla `.env.example`.

## Tipos de mensaje (Conventional Commits)
| Prefijo | Uso |
|---|---|
| `feat:` | Funcionalidad nueva |
| `fix:` | Corrección de un error |
| `docs:` | Documentación |
| `chore:` | Mantenimiento o configuración |
| `test:` | Tests |
| `refactor:` | Mejora sin cambiar el comportamiento (ej. limpiar `noqa` y `TODO` resueltos); los tests deben seguir pasando igual |

Con ámbito opcional: `feat(domain): asigna bloque horario según RN-01`

**Estilo recomendado para la descripción:** en minúscula y en **imperativo** (como una orden): `feat(logging): agrega logging estructurado con run_id`, no `Se Añade...`.

## pull vs. push: ¿en qué dirección va?
| Comando | Dirección | Para qué |
|---|---|---|
| `git pull` | GitHub → tu PC | Traer cambios que se subieron desde otro lugar |
| `git push` | tu PC → GitHub | Subir tus commits |

Si GitHub "no está actualizado", casi siempre falta un **push**, no un pull.

## Comparar tu PC con GitHub (sin cambiar nada)
```powershell
git fetch origin
git status -sb
```
`fetch` descarga la información de GitHub **sin modificar tus archivos**. `status -sb` muestra si estás `ahead` (tienes commits sin subir) o `behind` (te faltan commits de GitHub).

## Revisar secretos en lo que vas a subir (antes de cada push)
```powershell
git --no-pager diff origin/main..HEAD | Select-String -Pattern "password|PWD=|secret|api_key"
```
Busca palabras peligrosas en **todo lo que el push publicaría**. Si aparece algo, no hagas push: corrígelo primero. En un repositorio público, un secreto publicado queda para siempre en el historial.

## Buscar un secreto en TODOS los archivos que se publicarían (versionados + nuevos no ignorados)
```powershell
git ls-files; git ls-files --others --exclude-standard
```
El primero lista los archivos versionados; el segundo, los archivos nuevos que **no** están ignorados (los que un `git add .` agregaría). Combinados con `Select-String` sirven para buscar una contraseña antes de publicar.

## Respaldar una carpeta y comprobar que la copia es idéntica
```powershell
Copy-Item -Recurse OLD Archivos\OLD_original
(Get-FileHash OLD\funciones.py).Hash -eq (Get-FileHash Archivos\OLD_original\funciones.py).Hash
```
`Get-FileHash` calcula la huella SHA-256 de un archivo. Si las huellas son iguales, el contenido es idéntico. Respaldar **antes** de modificar algo es un buen hábito.

## Agregar al commit solo archivos específicos (no todo)
```powershell
git add .gitignore docs/bitacora_aprendizaje.md
```
En vez de `git add .`, nombra los archivos. Así no entran por error carpetas como `OLD/` o archivos a medio terminar.

## Ver cuántos commits faltan por subir a GitHub
```powershell
git --no-pager log --oneline origin/main..HEAD
```
Lista los commits que están en tu PC pero todavía no en GitHub. Si no muestra nada, está todo subido.

## Finales de línea (LF): `.gitattributes`
Crear `.gitattributes` en la raíz:
```gitattributes
# Normaliza todo archivo de texto a LF en el repositorio y en disco
* text=auto eol=lf

# Excepciones: scripts propios de Windows necesitan CRLF
*.ps1 text eol=crlf
*.bat text eol=crlf

# Binarios: nunca convertir
*.parquet binary
*.pbix binary
*.xlsx binary
```
Aplicar la regla a los archivos existentes:
```powershell
git add --renormalize .
git status
git commit -m "chore: normaliza finales de línea a LF con .gitattributes"
```

> 📌 `.gitignore` = qué **no** entra a git · `.gitattributes` = **cómo** tratar lo que sí entra.
