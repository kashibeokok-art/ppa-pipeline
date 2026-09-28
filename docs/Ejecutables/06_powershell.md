# PowerShell: atajos del sistema

## Crear la estructura de módulos por capa (Medallion)
```powershell
"extract","bronze","silver","domain","quality","load" | % { New-Item -ItemType File -Force "src/ppa_pipeline/$_/__init__.py" }
```
Cómo se lee:
- `"a","b",...` es una lista de nombres.
- `|` pasa cada nombre al comando siguiente (*pipeline*).
- `%` es un alias de `ForEach-Object`: "para cada elemento, haz…".
- `$_` es el elemento actual.
- `New-Item -ItemType File -Force` crea el archivo y las carpetas que falten.

## Ver archivos, incluidos los ocultos (como `.git`)
```powershell
Get-ChildItem -Force
```

## Ver una carpeta y todo su contenido (para verificar rutas)
```powershell
Get-ChildItem -Recurse .github
```
`-Recurse` entra en todas las subcarpetas. Sirve para confirmar que un archivo quedó donde debe.

## Borrar una carpeta con su contenido
```powershell
Remove-Item -Recurse -Force <carpeta>
```
`-Recurse` borra también lo que hay dentro y `-Force` no pide confirmación. ⚠️ Revisa la ruta antes de ejecutarlo: no hay papelera.
