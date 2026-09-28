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

## Tipos de mensaje (Conventional Commits)
| Prefijo | Uso |
|---|---|
| `feat:` | Funcionalidad nueva |
| `fix:` | Corrección de un error |
| `docs:` | Documentación |
| `chore:` | Mantenimiento o configuración |
| `test:` | Tests |
| `refactor:` | Mejora sin cambiar el comportamiento |

Con ámbito opcional: `feat(domain): asigna bloque horario según RN-01`

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
