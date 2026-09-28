# VS Code: editor, temas y vista previa

## Instalar una extensión desde la consola
```powershell
code --install-extension ahmadawais.shades-of-purple
```
`code` es la herramienta de línea de comandos de VS Code. Instala la extensión por su ID (el tema morado neón *Shades of Purple*).

## Ver las extensiones instaladas
```powershell
code --list-extensions
```

## Abrir la configuración
- **Usuario** (aplica a todos tus proyectos): `Ctrl+Shift+P` → **Preferences: Open User Settings (JSON)**. Archivo: `%APPDATA%\Code\User\settings.json`.
- **Proyecto** (solo este repositorio): `.vscode/settings.json`.

## Elegir un tema instalado
`Ctrl+K`, soltar, y luego `Ctrl+T` (o `Ctrl+Shift+P` → **Preferences: Color Theme**).
Muévete con `↑` `↓` para verlos **en vivo**; `Enter` elige, `Esc` cancela.
Variantes instaladas: `Shades of Purple` y `Shades of Purple (Super Dark)`.

## Buscar e instalar temas nuevos
- **Con vista previa sin instalar:** `Ctrl+K` → `Ctrl+T` → al final, **Browse Additional Color Themes...** → flechas para previsualizar → `Enter` instala.
- **Panel de extensiones:** `Ctrl+Shift+X` → buscar `@category:themes` (o `purple neon theme`) → **Install** → **Set Color Theme**.

Temas morados o neón para probar: **SynthWave '84**, **Shades of Purple**, **Dracula Theme Official**, **Tokyo Night**, **Night Owl**.

> ⚠️ Los ajustes de contraste de la configuración de usuario están dentro de `"[Shades of Purple]"` y **solo aplican a ese tema**. La vista previa de Markdown mantiene su estilo con cualquier tema (usa `.vscode/markdown-preview.css`).

## Vista previa de Markdown
| Atajo | Acción |
|---|---|
| `Ctrl+Shift+V` | Abrir la vista previa en una pestaña |
| `Ctrl+K` y luego `V` | Abrir la vista previa al lado del editor |

## Configuración aplicada en este proyecto
- **Usuario:** tema `Shades of Purple`, fondo más oscuro para los bloques de código, texto blanco en los bloques de los `.md`, ajuste de líneas largas en Markdown y un tamaño de letra de 15 en la vista previa.
- **Proyecto:** `.vscode/markdown-preview.css` (bloques con borde morado y colores neón), activado en `.vscode/settings.json` con `"markdown.styles"`.

## Recargar si no se ven los cambios
`Ctrl+Shift+P` → **Developer: Reload Window**
