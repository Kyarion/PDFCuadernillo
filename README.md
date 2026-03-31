PDF A CUADERNILLO PARA IMPRIMIR
===============================

Este archivo explica cómo usar el script `pdf_a_cuadernillo.py` para convertir un PDF normal en un PDF reorganizado en formato cuadernillo, listo para imprimir en papel carta, con 2 páginas por cara y doble cara.


1. QUÉ HACE EL SCRIPT
---------------------

El script:
- lee todas las páginas del PDF original
- agrega páginas en blanco si hace falta para completar múltiplos de 4
- reordena las páginas en secuencia de cuadernillo
- genera una salida en hoja carta horizontal
- coloca 2 páginas por cara
- deja el PDF listo para imprimir a doble cara

Está pensado para libros escaneados, apuntes, guías, partituras y documentos similares.


2. REQUISITOS
-------------

Necesitas:
- Python 3.10 o superior
- la librería `pypdf`


3. INSTALACIÓN
--------------

Instala la dependencia necesaria con:

pip install pypdf


4. ARCHIVOS DEL PROYECTO
------------------------

Normalmente tendrás:
- pdf_a_cuadernillo.py
- README.txt


5. USO RÁPIDO
-------------

Ejecuta el script indicando el PDF de entrada:

python pdf_a_cuadernillo.py "mi_libro.pdf"

Eso generará automáticamente un archivo llamado:

mi_libro_cuadernillo.pdf

El archivo de salida se guarda en la misma carpeta del PDF original si no indicas otra ruta.


6. SINTAXIS GENERAL
-------------------

python pdf_a_cuadernillo.py <archivo_entrada.pdf> [-o <archivo_salida.pdf>] [--margin <valor>]

Ejemplo:

python pdf_a_cuadernillo.py "archivo.pdf" -o "archivo_cuadernillo.pdf" --margin 12


7. PARÁMETROS DISPONIBLES
-------------------------

Parámetro obligatorio:
- input_pdf
  Ruta del archivo PDF de entrada.

Parámetros opcionales:
- -o, --output
  Permite definir el nombre o la ruta del archivo PDF de salida.

- --margin
  Permite definir el margen interior en puntos PDF alrededor de cada página dentro de la hoja final.
  Valor por defecto: 12


8. COMANDOS DE USO
------------------

8.1. Conversión básica

python pdf_a_cuadernillo.py "mi_libro.pdf"

Resultado esperado:
- se crea `mi_libro_cuadernillo.pdf`
- se guarda junto al archivo original


8.2. Nombre de salida personalizado

python pdf_a_cuadernillo.py "mi_libro.pdf" -o "salida_cuadernillo.pdf"

También puedes usar:

python pdf_a_cuadernillo.py "mi_libro.pdf" --output "salida_cuadernillo.pdf"

Esto permite elegir exactamente cómo se llamará el archivo final.


8.3. Definir ruta de salida

Windows:
python pdf_a_cuadernillo.py "C:\Documentos\libro.pdf" -o "C:\Documentos\Salida\libro_cuadernillo.pdf"

Linux / macOS:
python3 pdf_a_cuadernillo.py "/home/usuario/documentos/libro.pdf" -o "/home/usuario/salida/libro_cuadernillo.pdf"

Esto permite guardar el archivo final en otra carpeta.


8.4. Cambiar margen

python pdf_a_cuadernillo.py "mi_libro.pdf" --margin 18

Esto aumenta el margen interior alrededor de cada página.

Ejemplos útiles:
- margen menor: 8
- margen estándar: 12
- margen amplio: 18 o 20


8.5. Combinar nombre de salida y margen

python pdf_a_cuadernillo.py "mi_libro.pdf" -o "mi_libro_final.pdf" --margin 18


9. COMANDOS ÚTILES SEGÚN SISTEMA
--------------------------------

9.1. Windows

Conversión básica:
python pdf_a_cuadernillo.py "archivo.pdf"

Si `python` no funciona:
py pdf_a_cuadernillo.py "archivo.pdf"

Salida personalizada:
py pdf_a_cuadernillo.py "archivo.pdf" -o "archivo_cuadernillo.pdf"

Con margen personalizado:
py pdf_a_cuadernillo.py "archivo.pdf" -o "archivo_cuadernillo.pdf" --margin 16


9.2. Linux / macOS

Conversión básica:
python3 pdf_a_cuadernillo.py "archivo.pdf"

Salida personalizada:
python3 pdf_a_cuadernillo.py "archivo.pdf" -o "archivo_cuadernillo.pdf"

Con margen personalizado:
python3 pdf_a_cuadernillo.py "archivo.pdf" --margin 16


10. EJEMPLOS COMPLETOS
----------------------

Ejemplo 1: conversión simple
python pdf_a_cuadernillo.py "solfeo.pdf"

Salida esperada:
solfeo_cuadernillo.pdf


Ejemplo 2: salida personalizada
python pdf_a_cuadernillo.py "partituras.pdf" -o "partituras_lista_para_imprimir.pdf"


Ejemplo 3: más margen
python pdf_a_cuadernillo.py "libro.pdf" --margin 24


Ejemplo 4: ruta absoluta en Windows
py pdf_a_cuadernillo.py "C:\Users\Paola\Documents\LAZ 1.pdf" -o "C:\Users\Paola\Documents\LAZ 1_cuadernillo.pdf"


Ejemplo 5: ruta absoluta con margen
py pdf_a_cuadernillo.py "C:\Users\Paola\Documents\LAZ 1.pdf" -o "C:\Users\Paola\Documents\LAZ 1_cuadernillo.pdf" --margin 18


Ejemplo 6: Linux o macOS con salida en otra carpeta
python3 pdf_a_cuadernillo.py "/home/usuario/libros/teoria.pdf" -o "/home/usuario/cuadernillos/teoria_cuadernillo.pdf" --margin 14


11. NOMBRE DE SALIDA AUTOMÁTICO
-------------------------------

Si no usas `-o` ni `--output`, el script crea automáticamente un nombre basado en el archivo original.

Ejemplo:
Entrada:
mi_libro.pdf

Salida automática:
mi_libro_cuadernillo.pdf


12. CÓMO FUNCIONA EL CUADERNILLO
--------------------------------

Un cuadernillo necesita que el número total de páginas sea múltiplo de 4.

Ejemplos:
- 8 páginas  -> correcto
- 12 páginas -> correcto
- 20 páginas -> correcto
- 82 páginas -> no correcto

Si el total no es múltiplo de 4, el script agrega páginas en blanco al final hasta completar el número necesario.

Ejemplo:
- PDF original: 82 páginas
- PDF ajustado: 84 páginas
- páginas en blanco agregadas: 2

Esto es normal y necesario para que el cuadernillo quede correctamente impuesto.


13. SALIDA ESPERADA EN CONSOLA
------------------------------

Al ejecutar el script, verás algo parecido a esto:

PDF original: mi_libro.pdf
Páginas originales: 82
Páginas finales ajustadas a cuadernillo: 84
Páginas en blanco agregadas: 2
Salida: mi_libro_cuadernillo.pdf

Imprimir así:
- Tamaño carta
- Doble cara
- Voltear por borde corto
- Escala 100% o tamaño real


14. CONFIGURACIÓN DE IMPRESIÓN
------------------------------

Para imprimir correctamente el PDF generado, usa estas opciones:

- tamaño de papel: Carta
- impresión: Doble cara
- volteo: Por borde corto
- escala: 100% o Tamaño real

Muy importante:
Si eliges “voltear por borde largo”, el reverso quedará invertido.

La opción correcta es:
VOLTEAR POR BORDE CORTO


15. RECOMENDACIÓN ANTES DE IMPRIMIR TODO
----------------------------------------

Haz una prueba con pocas hojas antes de imprimir el documento completo.

Revisa:
- que el orden de páginas sea correcto
- que ambas caras queden bien orientadas
- que el tamaño se vea bien
- que no haya recortes no deseados


16. RESULTADO ESPERADO DESPUÉS DE IMPRIMIR
------------------------------------------

Una vez impreso:
1. apila las hojas en orden
2. dóblalas por la mitad
3. engrápalas al centro

Y tendrás un cuadernillo físico listo para usar.


17. SOLUCIÓN DE PROBLEMAS
-------------------------

17.1. El PDF sale en desorden
Causa probable:
- configuración incorrecta de impresión

Revisa:
- que esté en doble cara
- que el volteo sea por borde corto


17.2. El reverso sale al revés
Causa probable:
- elegiste borde largo

Solución:
- cambia a “voltear por borde corto”


17.3. El contenido sale muy pequeño
Causa probable:
- margen demasiado alto

Prueba con un margen menor:
python pdf_a_cuadernillo.py "archivo.pdf" --margin 8


17.4. La impresora corta parte del contenido
Causa probable:
- el área imprimible de la impresora es reducida

Prueba con un margen mayor:
python pdf_a_cuadernillo.py "archivo.pdf" --margin 18


17.5. El comando `python` no funciona
Soluciones posibles:
- en Windows prueba con `py`
- en Linux/macOS prueba con `python3`
- verifica si Python está instalado con `python --version` o `python3 --version`


17.6. `pypdf` no está instalado
Error típico:
- ModuleNotFoundError: No module named 'pypdf'

Solución:
pip install pypdf

o
pip3 install pypdf


18. QUÉ SE PUEDE HACER CON ESTE SCRIPT
--------------------------------------

Este script permite:
- convertir un PDF normal a cuadernillo
- generar automáticamente el nombre de salida
- definir un nombre de salida personalizado
- definir una ruta de salida personalizada
- ajustar el margen interior
- preparar PDFs escaneados para impresión tipo folleto
- trabajar con documentos cuya cantidad de páginas no sea múltiplo de 4


19. LO QUE ESTA VERSIÓN NO HACE
-------------------------------

Esta versión no incluye:
- corrección automática de páginas rotadas
- soporte para A4
- marcas de corte
- detección automática de escaneos descentrados
- imposiciones más complejas que un cuadernillo estándar


20. RESUMEN DE COMANDOS PRINCIPALES
-----------------------------------

Instalar dependencia:
pip install pypdf

Conversión básica:
python pdf_a_cuadernillo.py "archivo.pdf"

Conversión básica con `py`:
py pdf_a_cuadernillo.py "archivo.pdf"

Conversión básica en Linux/macOS:
python3 pdf_a_cuadernillo.py "archivo.pdf"

Salida personalizada:
python pdf_a_cuadernillo.py "archivo.pdf" -o "archivo_cuadernillo.pdf"

Ruta de salida personalizada:
python pdf_a_cuadernillo.py "C:\entrada\archivo.pdf" -o "C:\salida\archivo_cuadernillo.pdf"

Cambiar margen:
python pdf_a_cuadernillo.py "archivo.pdf" --margin 18

Combinar salida y margen:
python pdf_a_cuadernillo.py "archivo.pdf" -o "archivo_final.pdf" --margin 18