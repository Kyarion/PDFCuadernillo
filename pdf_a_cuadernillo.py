from __future__ import annotations

import argparse
import math
from pathlib import Path

from pypdf import PdfReader, PdfWriter, PageObject, Transformation


# ============================================================
# TAMAÑOS
# ============================================================

# Tamaño Carta / Letter en puntos PDF
# 1 pulgada = 72 puntos
LETTER_W = 612  # 8.5"
LETTER_H = 792  # 11"

# ------------------------------------------------------------
# Área LÓGICA donde armamos el cuadernillo.
#
# El cuadernillo se compone primero como una hoja horizontal:
#
#        792 x 612
#
# Después se gira todo el contenido y se coloca físicamente
# dentro de una página Carta VERTICAL de:
#
#        612 x 792
#
# De esta forma CUPS/HPLIP detectará el PDF como Portrait.
# ------------------------------------------------------------

SHEET_W = LETTER_H  # 792
SHEET_H = LETTER_W  # 612

# Tamaño REAL de las páginas del PDF de salida
OUTPUT_W = LETTER_W  # 612
OUTPUT_H = LETTER_H  # 792


# ============================================================
# UTILIDADES
# ============================================================

def add_blank_pages(
    pages: list[PageObject],
    multiple: int,
) -> list[PageObject]:
    """
    Completa el documento hasta un múltiplo determinado.

    Para cuadernillo 2-up:
        múltiplo de 4

    Para cuadernillo 4-up:
        múltiplo de 8
    """
    total = len(pages)
    faltan = (multiple - (total % multiple)) % multiple

    resultado = list(pages)

    for _ in range(faltan):
        blank = PageObject.create_blank_page(
            width=LETTER_W,
            height=LETTER_H,
        )
        resultado.append(blank)

    return resultado


def fit_page_to_slot(
    src_page: PageObject,
    slot_x: float,
    slot_y: float,
    slot_w: float,
    slot_h: float,
    margin: float = 12,
) -> tuple[PageObject, Transformation]:
    """
    Calcula una transformación para escalar y centrar una
    página PDF dentro de un espacio determinado.
    """

    src_w = float(src_page.mediabox.width)
    src_h = float(src_page.mediabox.height)

    usable_w = slot_w - 2 * margin
    usable_h = slot_h - 2 * margin

    scale = min(
        usable_w / src_w,
        usable_h / src_h,
    )

    placed_w = src_w * scale
    placed_h = src_h * scale

    x = slot_x + (slot_w - placed_w) / 2
    y = slot_y + (slot_h - placed_h) / 2

    transform = (
        Transformation()
        .scale(scale)
        .translate(tx=x, ty=y)
    )

    return src_page, transform


def merge_page_in_slot(
    dest_page: PageObject,
    src_page: PageObject,
    slot_x: float,
    slot_y: float,
    slot_w: float,
    slot_h: float,
    margin: float = 12,
) -> None:
    """
    Inserta una página PDF dentro de uno de los espacios de
    la hoja lógica horizontal.
    """

    _, transform = fit_page_to_slot(
        src_page=src_page,
        slot_x=slot_x,
        slot_y=slot_y,
        slot_w=slot_w,
        slot_h=slot_h,
        margin=margin,
    )

    dest_page.merge_transformed_page(
        src_page,
        transform,
    )


# ============================================================
# CONVERSIÓN HORIZONTAL -> VERTICAL LADEADO
# ============================================================

def make_portrait_sideways(
    landscape_page: PageObject,
    direction: str = "right",
) -> PageObject:
    """
    Toma una página lógica horizontal de 792 x 612 y coloca
    físicamente su contenido girado 90 grados dentro de una
    página Carta VERTICAL de 612 x 792.

    MUY IMPORTANTE:

    No utiliza solamente la metadata /Rotate del PDF.

    El contenido realmente se transforma dentro de una
    MediaBox vertical.

    De esta manera CUPS/HPLIP verá:

        MediaBox = 612 x 792
        orientación = Portrait

    aunque visualmente el contenido esté ladeado.

    direction:

        "right"
            gira el contenido 90 grados hacia la derecha
            (sentido horario).

        "left"
            gira el contenido 90 grados hacia la izquierda
            (sentido antihorario).
    """

    portrait = PageObject.create_blank_page(
        width=OUTPUT_W,
        height=OUTPUT_H,
    )

    if direction == "right":

        # Rotación de -90°:
        #
        # (x, y) -> (y, -x)
        #
        # Después de rotar, el contenido queda debajo del
        # origen, por lo que lo movemos 792 puntos hacia arriba.
        #
        # Resultado:
        #
        # x: 0 .. 612
        # y: 0 .. 792

        transform = (
            Transformation()
            .rotate(-90)
            .translate(
                tx=0,
                ty=OUTPUT_H,
            )
        )

    elif direction == "left":

        # Rotación de +90°:
        #
        # (x, y) -> (-y, x)
        #
        # Después de rotar queda a la izquierda del origen,
        # así que lo desplazamos 612 puntos hacia la derecha.

        transform = (
            Transformation()
            .rotate(90)
            .translate(
                tx=OUTPUT_W,
                ty=0,
            )
        )

    else:
        raise ValueError(
            "direction debe ser 'right' o 'left'"
        )

    portrait.merge_transformed_page(
        landscape_page,
        transform,
    )

    return portrait


# ============================================================
# IMPOSICIÓN DE CUADERNILLO
# ============================================================

def booklet_sheet_indices(
    total_pages: int,
    sheet_index: int,
) -> dict[str, int]:
    """
    Devuelve los índices necesarios para una hoja de
    cuadernillo clásica.

    Ejemplo con 8 páginas:

    Frente:
        8 | 1

    Reverso:
        2 | 7
    """

    return {
        "front_left":
            total_pages - 1 - (2 * sheet_index),

        "front_right":
            2 * sheet_index,

        "back_left":
            2 * sheet_index + 1,

        "back_right":
            total_pages - 2 - (2 * sheet_index),
    }


# ============================================================
# CUADERNILLO 2-UP
# ============================================================

def build_booklet_2up(
    reader: PdfReader,
    margin: float = 12,
    sideways: str = "right",
) -> PdfWriter:
    """
    Genera un cuadernillo clásico.

    Cada cara contiene 2 páginas del PDF original.

    Internamente:
        Carta horizontal 792 x 612

    Salida real:
        Carta vertical 612 x 792

    El contenido queda girado 90 grados dentro de la página.
    """

    original_pages = list(reader.pages)

    padded_pages = add_blank_pages(
        original_pages,
        multiple=4,
    )

    total = len(padded_pages)

    writer = PdfWriter()

    left_slot = (
        0,
        0,
        SHEET_W / 2,
        SHEET_H,
    )

    right_slot = (
        SHEET_W / 2,
        0,
        SHEET_W / 2,
        SHEET_H,
    )

    num_sheets = total // 4

    for sheet in range(num_sheets):

        idx = booklet_sheet_indices(
            total,
            sheet,
        )

        # ----------------------------------------------------
        # CARA FRONTAL
        # ----------------------------------------------------

        front = PageObject.create_blank_page(
            width=SHEET_W,
            height=SHEET_H,
        )

        merge_page_in_slot(
            front,
            padded_pages[idx["front_left"]],
            *left_slot,
            margin=margin,
        )

        merge_page_in_slot(
            front,
            padded_pages[idx["front_right"]],
            *right_slot,
            margin=margin,
        )

        # Convertimos la hoja horizontal a una página
        # físicamente vertical.
        front_portrait = make_portrait_sideways(
            front,
            direction=sideways,
        )

        writer.add_page(front_portrait)

        # ----------------------------------------------------
        # CARA POSTERIOR
        # ----------------------------------------------------

        back = PageObject.create_blank_page(
            width=SHEET_W,
            height=SHEET_H,
        )

        merge_page_in_slot(
            back,
            padded_pages[idx["back_left"]],
            *left_slot,
            margin=margin,
        )

        merge_page_in_slot(
            back,
            padded_pages[idx["back_right"]],
            *right_slot,
            margin=margin,
        )

        back_portrait = make_portrait_sideways(
            back,
            direction=sideways,
        )

        writer.add_page(back_portrait)

    return writer


# ============================================================
# CUADERNILLO 4-UP
# ============================================================

def build_booklet_4up(
    reader: PdfReader,
    margin: float = 12,
    sideways: str = "right",
) -> PdfWriter:
    """
    Genera un cuadernillo 4-up.

    Cada cara de la hoja contiene:

        2 páginas arriba
        2 páginas abajo

    Por lo tanto:

        4 páginas originales por cara
        8 páginas originales por hoja física

    El documento se arma primero en Carta horizontal y luego
    todo el contenido se gira dentro de una página Carta
    vertical.

    Está diseñado para doblar la hoja una sola vez, sin cortes.
    """

    original_pages = list(reader.pages)

    # Cada hoja física contiene 8 páginas originales.
    padded_pages = add_blank_pages(
        original_pages,
        multiple=8,
    )

    total = len(padded_pages)

    writer = PdfWriter()

    # --------------------------------------------------------
    # Cuadrantes de la hoja lógica horizontal
    # --------------------------------------------------------

    half_w = SHEET_W / 2
    half_h = SHEET_H / 2

    # Coordenadas PDF:
    # origen = esquina inferior izquierda

    slot_tl = (
        0,
        half_h,
        half_w,
        half_h,
    )

    slot_tr = (
        half_w,
        half_h,
        half_w,
        half_h,
    )

    slot_bl = (
        0,
        0,
        half_w,
        half_h,
    )

    slot_br = (
        half_w,
        0,
        half_w,
        half_h,
    )

    # Una hoja física contiene 8 páginas del PDF original.
    num_sheets = total // 8

    # Tratamos cada par de páginas originales como si fuera
    # una "página lógica" del cuadernillo clásico.
    num_pairs = total // 2

    for sheet in range(num_sheets):

        p_idx = booklet_sheet_indices(
            num_pairs,
            sheet,
        )

        # ====================================================
        # CARA FRONTAL
        # ====================================================

        front = PageObject.create_blank_page(
            width=SHEET_W,
            height=SHEET_H,
        )

        # ----------------------------------------------------
        # PAR IZQUIERDO
        # Páginas provenientes del final del documento
        # ----------------------------------------------------

        pair = p_idx["front_left"]

        merge_page_in_slot(
            front,
            padded_pages[2 * pair],
            *slot_tl,
            margin=margin,
        )

        merge_page_in_slot(
            front,
            padded_pages[2 * pair + 1],
            *slot_bl,
            margin=margin,
        )

        # ----------------------------------------------------
        # PAR DERECHO
        # Páginas provenientes del inicio del documento
        # ----------------------------------------------------

        pair = p_idx["front_right"]

        merge_page_in_slot(
            front,
            padded_pages[2 * pair],
            *slot_tr,
            margin=margin,
        )

        merge_page_in_slot(
            front,
            padded_pages[2 * pair + 1],
            *slot_br,
            margin=margin,
        )

        # Convertimos a Carta vertical
        front_portrait = make_portrait_sideways(
            front,
            direction=sideways,
        )

        writer.add_page(front_portrait)

        # ====================================================
        # CARA POSTERIOR
        # ====================================================

        back = PageObject.create_blank_page(
            width=SHEET_W,
            height=SHEET_H,
        )

        # ----------------------------------------------------
        # PAR IZQUIERDO
        # ----------------------------------------------------

        pair = p_idx["back_left"]

        merge_page_in_slot(
            back,
            padded_pages[2 * pair],
            *slot_tl,
            margin=margin,
        )

        merge_page_in_slot(
            back,
            padded_pages[2 * pair + 1],
            *slot_bl,
            margin=margin,
        )

        # ----------------------------------------------------
        # PAR DERECHO
        # ----------------------------------------------------

        pair = p_idx["back_right"]

        merge_page_in_slot(
            back,
            padded_pages[2 * pair],
            *slot_tr,
            margin=margin,
        )

        merge_page_in_slot(
            back,
            padded_pages[2 * pair + 1],
            *slot_br,
            margin=margin,
        )

        # Convertimos a Carta vertical
        back_portrait = make_portrait_sideways(
            back,
            direction=sideways,
        )

        writer.add_page(back_portrait)

    return writer


# ============================================================
# SELECCIÓN DEL MODO
# ============================================================

def build_booklet(
    reader: PdfReader,
    margin: float = 12,
    pages_per_side: int = 2,
    sideways: str = "right",
) -> PdfWriter:
    """
    Construye el cuadernillo según la cantidad de páginas
    solicitadas por cara.
    """

    if pages_per_side == 2:
        return build_booklet_2up(
            reader,
            margin=margin,
            sideways=sideways,
        )

    if pages_per_side == 4:
        return build_booklet_4up(
            reader,
            margin=margin,
            sideways=sideways,
        )

    raise ValueError(
        "pages_per_side debe ser 2 o 4"
    )


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Convierte un PDF en cuadernillo Carta con "
            "2 o 4 páginas por cara. "
            "La salida es Carta vertical con el contenido "
            "girado 90 grados."
        )
    )

    parser.add_argument(
        "input_pdf",
        help=(
            "Ruta del PDF de entrada, relativa a pdf/input/"
        ),
    )

    parser.add_argument(
        "-o",
        "--output",
        help=(
            "Ruta del PDF de salida. "
            "Si no se indica, se crea en pdf/output/"
        ),
    )

    parser.add_argument(
        "--margin",
        type=float,
        default=12,
        help=(
            "Margen interno en puntos PDF. "
            "Default: 12"
        ),
    )

    parser.add_argument(
        "--p",
        type=int,
        choices=[2, 4],
        default=4,
        help=(
            "Cantidad de páginas originales por cara: "
            "2 o 4. Default: 4"
        ),
    )

    parser.add_argument(
        "--sideways",
        choices=["right", "left"],
        default="right",
        help=(
            "Dirección en que se gira el contenido "
            "dentro de la hoja vertical. "
            "'right' = horario, "
            "'left' = antihorario. "
            "Default: right"
        ),
    )

    args = parser.parse_args()

    # --------------------------------------------------------
    # Entrada
    # --------------------------------------------------------

    input_path = Path("pdf/input") / args.input_pdf

    if not input_path.exists():
        raise FileNotFoundError(
            f"No existe el archivo: {input_path}"
        )

    # --------------------------------------------------------
    # Salida
    # --------------------------------------------------------

    output_dir = Path("pdf/output")
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    if args.output:

        output_path = Path(args.output)

    else:

        suffix = (
            f"_cuadernillo_{args.p}up_vertical.pdf"
        )

        output_path = (
            output_dir
            / f"{input_path.stem}{suffix}"
        )

    if output_path.parent != Path("."):
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    # --------------------------------------------------------
    # Leer PDF
    # --------------------------------------------------------

    reader = PdfReader(
        str(input_path)
    )

    # --------------------------------------------------------
    # Construir cuadernillo
    # --------------------------------------------------------

    writer = build_booklet(
        reader,
        margin=args.margin,
        pages_per_side=args.p,
        sideways=args.sideways,
    )

    # --------------------------------------------------------
    # Guardar
    # --------------------------------------------------------

    with output_path.open("wb") as f:
        writer.write(f)

    # --------------------------------------------------------
    # Estadísticas
    # --------------------------------------------------------

    total_original = len(reader.pages)

    multiple = (
        4
        if args.p == 2
        else 8
    )

    total_padded = (
        math.ceil(total_original / multiple)
        * multiple
    )

    blanks_added = (
        total_padded - total_original
    )

    # --------------------------------------------------------
    # Resultado
    # --------------------------------------------------------

    print()
    print("==========================================")
    print(" CUADERNILLO GENERADO")
    print("==========================================")
    print()

    print(f"PDF original:")
    print(f"  {input_path}")

    print()

    print(
        f"Páginas originales: "
        f"{total_original}"
    )

    print(
        f"Páginas finales ajustadas: "
        f"{total_padded}"
    )

    print(
        f"Páginas en blanco agregadas: "
        f"{blanks_added}"
    )

    print(
        f"Páginas por cara: "
        f"{args.p}"
    )

    print(
        f"Giro del contenido: "
        f"{args.sideways}"
    )

    print()

    print("PDF de salida:")
    print(f"  {output_path}")

    print()

    print("Tamaño físico de cada página PDF:")
    print(
        f"  {OUTPUT_W} x {OUTPUT_H} puntos"
    )
    print("  Carta / Letter VERTICAL")

    print()

    print("==========================================")
    print(" CONFIGURACIÓN DE IMPRESIÓN")
    print("==========================================")
    print()

    print("- Papel: Carta / Letter")
    print("- Orientación: VERTICAL / Portrait")
    print("- Páginas por hoja: 1")
    print("- Escala: 100% / Tamaño real")
    print("- NO usar 'ajustar orientación'")
    print("- NO usar 'rotar automáticamente'")
    print("- NO seleccionar Landscape")
    print()
    print(
        "El contenido ya está girado físicamente "
        "90 grados dentro del PDF."
    )
    print()


if __name__ == "__main__":
    main()