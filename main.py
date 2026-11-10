import base64
import html
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, colorchooser

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageTk


# =========================================================
# 1. CONFIGURAÇÕES
# =========================================================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

COR_FUNDO = "#72004F"
COR_DESTAQUE = "#E83EAD"
COR_CLARA = "#F5A6DF"
COR_TEXTO = "#FFFFFF"
COR_ESCURO = "#480039"

LARGURA = 1200
ALTURA = 700

foto_perfil = None
foto_destaque = None
imagem_preview = None
campos_contatos = []


# =========================================================
# 2. FONTES E CORES
# =========================================================

def fonte(tamanho, negrito=False):
    arquivo = (
        "C:/Windows/Fonts/arialbd.ttf"
        if negrito
        else "C:/Windows/Fonts/arial.ttf"
    )

    try:
        return ImageFont.truetype(arquivo, tamanho)
    except OSError:
        return ImageFont.load_default()


def rgb(cor):
    cor = cor.lstrip("#")
    return tuple(
        int(cor[i:i + 2], 16)
        for i in (0, 2, 4)
    )


def escurecer(cor, fator=0.55):
    return tuple(
        int(valor * fator)
        for valor in rgb(cor)
    )


def escolher_cor(tipo):
    global COR_FUNDO, COR_DESTAQUE, COR_CLARA

    cores = {
        "fundo": COR_FUNDO,
        "destaque": COR_DESTAQUE,
        "clara": COR_CLARA,
    }

    cor = colorchooser.askcolor(
        initialcolor=cores[tipo],
        title="Escolha uma cor",
    )

    if not cor[1]:
        return

    if tipo == "fundo":
        COR_FUNDO = cor[1]
    elif tipo == "destaque":
        COR_DESTAQUE = cor[1]
    elif tipo == "clara":
        COR_CLARA = cor[1]

    atualizar_previa()


def restaurar_cores():
    global COR_FUNDO, COR_DESTAQUE, COR_CLARA

    COR_FUNDO = "#72004F"
    COR_DESTAQUE = "#E83EAD"
    COR_CLARA = "#F5A6DF"

    atualizar_previa()


# =========================================================
# 3. SELEÇÃO E PREPARAÇÃO DE IMAGENS
# =========================================================

def selecionar_imagem(tipo):
    global foto_perfil, foto_destaque

    caminho = filedialog.askopenfilename(
        title="Selecione uma imagem",
        filetypes=[
            ("Imagens", "*.png *.jpg *.jpeg *.webp"),
            ("Todos os arquivos", "*.*"),
        ],
    )

    if not caminho:
        return

    try:
        with Image.open(caminho) as teste:
            teste.verify()

    except Exception:
        messagebox.showerror(
            "LiCards",
            "Não foi possível abrir essa imagem."
        )
        return

    if tipo == "perfil":
        foto_perfil = caminho

        status_perfil.configure(
            text="Foto de perfil selecionada",
            text_color="#78D99B",
        )

    else:
        foto_destaque = caminho

        status_destaque.configure(
            text="Segunda imagem selecionada",
            text_color="#78D99B",
        )

    atualizar_previa()


def preparar_imagem(caminho, tamanho, preto_branco=False):
    imagem = Image.open(caminho).convert("RGBA")

    if preto_branco:
        alpha = imagem.getchannel("A")

        imagem_rgb = ImageOps.grayscale(
            imagem.convert("RGB")
        )

        imagem_rgb = ImageOps.colorize(
            imagem_rgb,
            black="#111111",
            white="#FFFFFF",
        )

        imagem = imagem_rgb.convert("RGBA")
        imagem.putalpha(alpha)

    imagem.thumbnail(
        tamanho,
        Image.Resampling.LANCZOS
    )

    return imagem


# =========================================================
# 4. CONTATOS DINÂMICOS
# =========================================================

def obter_contatos():
    contatos = []

    for item in campos_contatos:
        titulo = item["titulo"].get().strip()
        endereco = item["endereco"].get().strip()
        icone = item["icone"].get().strip()

        if titulo and endereco:
            contatos.append({
                "titulo": titulo,
                "endereco": endereco,
                "icone": icone,
            })

    return contatos


def adicionar_contato(titulo="", endereco="", icone="🔗"):
    linha = ctk.CTkFrame(
        contatos_container,
        fg_color="#3A2633",
        corner_radius=10,
    )

    linha.pack(
        fill="x",
        padx=10,
        pady=5,
    )

    entrada_icone = ctk.CTkEntry(
        linha,
        width=48,
        placeholder_text="🔗",
        justify="center",
    )

    entrada_icone.insert(0, icone)

    entrada_icone.grid(
        row=0,
        column=0,
        padx=(8, 4),
        pady=8,
    )

    entrada_titulo = ctk.CTkEntry(
        linha,
        width=105,
        placeholder_text="Nome",
    )

    entrada_titulo.insert(0, titulo)

    entrada_titulo.grid(
        row=0,
        column=1,
        padx=4,
        pady=8,
    )

    entrada_endereco = ctk.CTkEntry(
        linha,
        placeholder_text="Link, e-mail ou telefone",
    )

    entrada_endereco.insert(0, endereco)

    entrada_endereco.grid(
        row=0,
        column=2,
        sticky="ew",
        padx=4,
        pady=8,
    )

    linha.grid_columnconfigure(2, weight=1)

    item = {
        "frame": linha,
        "icone": entrada_icone,
        "titulo": entrada_titulo,
        "endereco": entrada_endereco,
    }

    campos_contatos.append(item)

    def remover():
        linha.destroy()

        if item in campos_contatos:
            campos_contatos.remove(item)

    ctk.CTkButton(
        linha,
        text="✕",
        width=32,
        fg_color="#8C315F",
        hover_color="#B13B75",
        command=remover,
    ).grid(
        row=0,
        column=3,
        padx=(4, 8),
        pady=8,
    )


# =========================================================
# 5. FUNÇÕES DE DESENHO
# =========================================================

def desenhar_texto_quebrado(
    desenho,
    texto,
    posicao,
    largura,
    fonte_usada,
    cor,
    limite=3,
):
    palavras = texto.split()
    linhas = []
    linha = ""

    for palavra in palavras:
        teste = (
            linha + " " + palavra
            if linha
            else palavra
        )

        if desenho.textlength(
            teste,
            font=fonte_usada
        ) <= largura:

            linha = teste

        else:
            if linha:
                linhas.append(linha)

            linha = palavra

    if linha:
        linhas.append(linha)

    x, y = posicao

    for linha in linhas[:limite]:
        desenho.text(
            (x, y),
            linha,
            font=fonte_usada,
            fill=cor,
        )

        y += 29


def desenhar_fundo(imagem, desenho):
    cor_inicio = rgb(COR_FUNDO)
    cor_final = escurecer(COR_FUNDO)

    for y in range(ALTURA):
        proporcao = y / ALTURA

        cor = tuple(
            int(
                cor_inicio[i] * (1 - proporcao)
                + cor_final[i] * proporcao
            )
            for i in range(3)
        )

        desenho.line(
            (0, y, LARGURA, y),
            fill=cor + (255,),
        )


def desenhar_foto_perfil(imagem, desenho, nome):
    centro_x = 205
    centro_y = 215
    tamanho = 250

    x = centro_x - tamanho // 2
    y = centro_y - tamanho // 2

    desenho.ellipse(
        (
            x - 8,
            y - 8,
            x + tamanho + 8,
            y + tamanho + 8,
        ),
        fill=COR_CLARA,
    )

    if foto_perfil:
        try:
            foto = Image.open(
                foto_perfil
            ).convert("RGB")

            foto = ImageOps.fit(
                foto,
                (tamanho, tamanho),
                method=Image.Resampling.LANCZOS,
            )

            mascara = Image.new(
                "L",
                (tamanho, tamanho),
                0,
            )

            ImageDraw.Draw(mascara).ellipse(
                (0, 0, tamanho, tamanho),
                fill=255,
            )

            imagem.paste(
                foto,
                (x, y),
                mascara,
            )

            return

        except Exception as erro:
            print(
                "Erro ao carregar foto de perfil:",
                erro,
            )

    desenho.ellipse(
        (x, y, x + tamanho, y + tamanho),
        fill=COR_ESCURO,
    )

    desenho.text(
        (centro_x, centro_y),
        nome[:1].upper(),
        font=fonte(100, True),
        fill=COR_TEXTO,
        anchor="mm",
    )

    # =========================================================
# 6. GERAR CARTÃO PNG
# =========================================================

def gerar_cartao():

    nome = campo_nome.get().strip() or "Seu Nome"
    profissao = campo_profissao.get().strip() or "Sua profissão"
    localizacao = (
        campo_localizacao.get().strip()
        or "Sua localização"
    )

    descricao = campo_descricao.get(
        "1.0",
        "end"
    ).strip() or "Conte um pouco sobre você."

    contatos = obter_contatos()

    imagem = Image.new(
        "RGBA",
        (LARGURA, ALTURA),
        COR_FUNDO
    )

    desenho = ImageDraw.Draw(imagem)

    # Fundo em degradê
    desenhar_fundo(imagem, desenho)

    # Moldura
    desenho.rounded_rectangle(
        (30, 30, 1170, 670),
        radius=30,
        outline=COR_DESTAQUE,
        width=3
    )

    # Barra superior
    desenho.rounded_rectangle(
        (450, 75, 1120, 225),
        radius=18,
        fill=COR_DESTAQUE
    )

    # Seta decorativa
    desenho.polygon(
        [
            (450, 130),
            (405, 165),
            (405, 145),
            (375, 145),
            (375, 105),
            (405, 105),
            (405, 85),
        ],
        fill=COR_DESTAQUE
    )

    # Descrição
    desenhar_texto_quebrado(
        desenho,
        descricao,
        (485, 105),
        590,
        fonte(23),
        COR_TEXTO,
        limite=3
    )

    # Foto de perfil
    desenhar_foto_perfil(
        imagem,
        desenho,
        nome
    )

    # Nome
    desenho.text(
        (205, 365),
        nome[:24],
        font=fonte(30, True),
        fill=COR_TEXTO,
        anchor="mm"
    )

    # Localização
    desenho.text(
        (205, 405),
        localizacao[:30],
        font=fonte(18),
        fill=COR_TEXTO,
        anchor="mm"
    )

    # Profissão
    desenho.text(
        (205, 445),
        profissao[:30],
        font=fonte(18, True),
        fill=COR_CLARA,
        anchor="mm"
    )

    # Segunda imagem opcional
    if foto_destaque:

        try:
            imagem_extra = preparar_imagem(
                foto_destaque,
                (220, 125),
                preto_branco=preto_branco.get()
            )

            desenho.rounded_rectangle(
                (75, 510, 335, 650),
                radius=15,
                fill=COR_CLARA
            )

            # Máscara arredondada
            mascara = Image.new(
                "L",
                imagem_extra.size,
                0
            )

            ImageDraw.Draw(mascara).rounded_rectangle(
                (
                    0,
                    0,
                    imagem_extra.width - 1,
                    imagem_extra.height - 1
                ),
                radius=12,
                fill=255
            )

            x = 205 - imagem_extra.width // 2
            y = 580 - imagem_extra.height // 2

            imagem.paste(
                imagem_extra,
                (x, y),
                mascara
            )

        except Exception as erro:
            print("Erro na segunda imagem:", erro)

    # Contatos
    contatos_exibidos = contatos[:8]

    posicoes = [
        (420, 285),
        (785, 285),
        (420, 375),
        (785, 375),
        (420, 465),
        (785, 465),
        (420, 555),
        (785, 555),
    ]

    cores_blocos = [
        COR_DESTAQUE,
        COR_ESCURO,
        COR_CLARA,
    ]

    for indice, contato in enumerate(contatos_exibidos):

        x, y = posicoes[indice]

        cor_bloco = cores_blocos[
            indice % len(cores_blocos)
        ]

        cor_texto = (
            COR_ESCURO
            if cor_bloco == COR_CLARA
            else COR_TEXTO
        )

        desenho.rounded_rectangle(
            (x, y, x + 335, y + 75),
            radius=13,
            fill=cor_bloco
        )

        # Marcador decorativo
        desenho.ellipse(
            (x + 14, y + 25, x + 26, y + 37),
            fill=cor_texto
        )

        # Nome do contato
        desenho.text(
            (x + 38, y + 10),
            contato["titulo"][:22],
            font=fonte(19, True),
            fill=cor_texto
        )

        # Endereço ou informação
        valor = contato["endereco"]

        if len(valor) > 34:
            valor = valor[:31] + "..."

        desenho.text(
            (x + 38, y + 43),
            valor,
            font=fonte(13),
            fill=cor_texto
        )

    # Aviso se houver mais de oito contatos
    if len(contatos) > 8:

        desenho.text(
            (785, 645),
            f"+ {len(contatos) - 8} contatos disponíveis no HTML",
            font=fonte(13),
            fill=COR_CLARA
        )

    # Assinatura
    desenho.text(
        (600, 680),
        "LiCards",
        font=fonte(15, True),
        fill=COR_CLARA,
        anchor="mm"
    )

    return imagem.convert("RGB")


# =========================================================
# 7. PRÉ-VISUALIZAÇÃO
# =========================================================

def atualizar_previa():
    global imagem_preview

    try:
        imagem = gerar_cartao()

        miniatura = imagem.resize(
            (600, 350),
            Image.Resampling.LANCZOS
        )

        imagem_preview = ImageTk.PhotoImage(
            miniatura
        )

        previa.configure(
            image=imagem_preview,
            text=""
        )

    except Exception as erro:

        messagebox.showerror(
            "Erro na pré-visualização",
            f"Não foi possível gerar o cartão:\n{erro}"
        )


# =========================================================
# 8. SALVAR CARTÃO PNG
# =========================================================

def baixar_png():

    try:
        imagem = gerar_cartao()

        caminho = filedialog.asksaveasfilename(
            title="Salvar cartão",
            defaultextension=".png",
            initialfile="meu_cartao.png",
            filetypes=[
                ("Imagem PNG", "*.png")
            ]
        )

        if not caminho:
            return

        imagem.save(
            caminho,
            "PNG"
        )

        messagebox.showinfo(
            "LiCards",
            "Cartão PNG salvo com sucesso!"
        )

    except Exception as erro:

        messagebox.showerror(
            "Erro ao salvar",
            f"Não foi possível salvar o cartão:\n{erro}"
        )

        # =========================================================
# 9. CONVERTER IMAGENS PARA BASE64
# =========================================================

def imagem_em_base64(caminho):

    if not caminho:
        return ""

    try:
        with open(caminho, "rb") as arquivo:
            conteudo = base64.b64encode(
                arquivo.read()
            ).decode("utf-8")

        extensao = Path(caminho).suffix.lower()

        tipos = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
        }

        tipo = tipos.get(extensao, "image/png")

        return f"data:{tipo};base64,{conteudo}"

    except Exception as erro:
        print("Erro ao converter imagem:", erro)
        return ""


# =========================================================
# 10. PREPARAR LINKS DOS CONTATOS
# =========================================================

def preparar_link(titulo, endereco):

    endereco = endereco.strip()

    if not endereco:
        return ""

    titulo_lower = titulo.lower()

    # E-mail
    if "@" in endereco and " " not in endereco:
        if not endereco.startswith("mailto:"):
            return "mailto:" + endereco

        return endereco

    # WhatsApp
    if "whatsapp" in titulo_lower:

        numero = "".join(
            caractere
            for caractere in endereco
            if caractere.isdigit()
        )

        if numero:
            return "https://wa.me/" + numero

    # Telefone
    if any(
        palavra in titulo_lower
        for palavra in ("telefone", "celular", "ligação")
    ):

        numero = "".join(
            caractere
            for caractere in endereco
            if caractere.isdigit() or caractere == "+"
        )

        if numero:
            return "tel:" + numero

    # Links de sites e redes sociais
    if endereco.startswith(("https://", "http://")):
        return endereco

    # Impede esquemas perigosos
    if ":" in endereco.split("/")[0]:
        return ""

    return "https://" + endereco


# =========================================================
# 11. EXPORTAR CARTÃO DIGITAL HTML
# =========================================================

def exportar_html():

    try:

        nome = campo_nome.get().strip() or "Seu Nome"

        profissao = (
            campo_profissao.get().strip()
            or "Sua profissão"
        )

        localizacao = (
            campo_localizacao.get().strip()
            or "Sua localização"
        )

        descricao = campo_descricao.get(
            "1.0",
            "end"
        ).strip() or "Conheça um pouco mais sobre mim."

        contatos = obter_contatos()

        foto1 = imagem_em_base64(foto_perfil)
        foto2 = imagem_em_base64(foto_destaque)

        # Foto de perfil
        if foto1:

            imagem_perfil_html = f"""
                <img
                    class="perfil"
                    src="{foto1}"
                    alt="Foto de perfil"
                >
            """

        else:

            imagem_perfil_html = f"""
                <div class="perfil inicial">
                    {html.escape(nome[:1].upper())}
                </div>
            """

        # Segunda imagem
        imagem_extra_html = ""

        if foto2:

            classe_extra = (
                "foto-extra preto-branco"
                if preto_branco.get()
                else "foto-extra"
            )

            imagem_extra_html = f"""
                <img
                    class="{classe_extra}"
                    src="{foto2}"
                    alt="Imagem adicional"
                >
            """

        # Criar os cartões de contato
        contatos_html = ""

        for contato in contatos:

            titulo = html.escape(
                contato["titulo"]
            )

            endereco = html.escape(
                contato["endereco"]
            )

            icone = html.escape(
                contato["icone"]
            )

            link = preparar_link(
                contato["titulo"],
                contato["endereco"]
            )

            if link:

                link_seguro = html.escape(
                    link,
                    quote=True
                )

                contatos_html += f"""
                    <a
                        class="contato"
                        href="{link_seguro}"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        <span class="icone">{icone}</span>

                        <span class="contato-texto">
                            <strong>{titulo}</strong>
                            <small>{endereco}</small>
                        </span>
                    </a>
                """

            else:

                contatos_html += f"""
                    <div class="contato">
                        <span class="icone">{icone}</span>

                        <span class="contato-texto">
                            <strong>{titulo}</strong>
                            <small>{endereco}</small>
                        </span>
                    </div>
                """

        if not contatos_html:

            contatos_html = """
                <p class="sem-contatos">
                    Nenhum contato foi adicionado.
                </p>
            """

        # Página HTML completa
        pagina = f"""<!DOCTYPE html>
<html lang="pt-BR">

<head>

    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <meta
        name="description"
        content="Cartão digital de {html.escape(nome, quote=True)}"
    >

    <title>LiCards - {html.escape(nome)}</title>

    <style>

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 30px 15px;
            font-family: Arial, sans-serif;
            color: white;
            background: linear-gradient(
                140deg,
                {COR_FUNDO},
                {COR_ESCURO}
            );
        }}

        .cartao {{
            width: 100%;
            max-width: 950px;
            padding: 35px;
            border: 2px solid {COR_DESTAQUE};
            border-radius: 25px;
            background: {COR_FUNDO};
            box-shadow: 0 20px 50px #0005;
        }}

        .cabecalho {{
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 30px;
        }}

        .descricao {{
            flex: 1;
            padding: 25px;
            border-radius: 15px;
            background: {COR_DESTAQUE};
            line-height: 1.7;
            overflow-wrap: anywhere;
        }}

        .conteudo {{
            display: grid;
            grid-template-columns: 1fr 1.7fr;
            gap: 30px;
        }}

        .identidade {{
            text-align: center;
        }}

        .perfil {{
            width: 180px;
            height: 180px;
            border-radius: 50%;
            object-fit: cover;
            border: 5px solid {COR_CLARA};
        }}

        .inicial {{
            display: flex;
            align-items: center;
            justify-content: center;
            margin: auto;
            background: {COR_CLARA};
            color: {COR_ESCURO};
            font-size: 65px;
            font-weight: bold;
        }}

        h1 {{
            margin-top: 20px;
            font-size: 27px;
            overflow-wrap: anywhere;
        }}

        .localizacao {{
            margin-top: 10px;
            color: #E7D5E0;
        }}

        .profissao {{
            margin-top: 8px;
            color: {COR_CLARA};
            font-weight: bold;
        }}

        .foto-extra {{
            display: block;
            max-width: 100%;
            max-height: 230px;
            margin: 25px auto 0;
            border-radius: 15px;
            object-fit: contain;
        }}

        .preto-branco {{
            filter: grayscale(100%);
        }}

        .dados {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            align-content: start;
            gap: 15px;
        }}

        .contato {{
            display: flex;
            align-items: center;
            gap: 12px;
            min-height: 95px;
            padding: 18px;
            border-radius: 15px;
            background: {COR_DESTAQUE};
            color: white;
            text-decoration: none;
            overflow-wrap: anywhere;
            transition: transform .2s, opacity .2s;
        }}

        .contato:nth-child(even) {{
            background: {COR_ESCURO};
            border: 1px solid {COR_DESTAQUE};
        }}

        .contato:hover {{
            transform: translateY(-4px);
            opacity: .85;
        }}

        .icone {{
            font-size: 25px;
            flex-shrink: 0;
        }}

        .contato-texto {{
            display: flex;
            flex-direction: column;
            gap: 7px;
            min-width: 0;
        }}

        .contato-texto strong {{
            font-size: 16px;
        }}

        .contato-texto small {{
            font-size: 12px;
            overflow-wrap: anywhere;
            opacity: .9;
        }}

        .sem-contatos {{
            color: #E7D5E0;
        }}

        .rodape {{
            margin-top: 35px;
            padding-top: 20px;
            border-top: 1px solid {COR_DESTAQUE};
            text-align: center;
            color: {COR_CLARA};
            font-size: 13px;
        }}

        @media (max-width: 650px) {{

            .cartao {{
                padding: 20px;
            }}

            .conteudo {{
                grid-template-columns: 1fr;
            }}

            .dados {{
                grid-template-columns: 1fr;
            }}

            .perfil {{
                width: 150px;
                height: 150px;
            }}

            .descricao {{
                padding: 18px;
            }}

        }}

    </style>

</head>

<body>

    <main class="cartao">

        <header class="cabecalho">

            <div class="descricao">
                {html.escape(descricao)}
            </div>

        </header>

        <section class="conteudo">

            <div class="identidade">

                {imagem_perfil_html}

                <h1>{html.escape(nome)}</h1>

                <p class="localizacao">
                    {html.escape(localizacao)}
                </p>

                <p class="profissao">
                    {html.escape(profissao)}
                </p>

                {imagem_extra_html}

            </div>

            <div class="dados">

                {contatos_html}

            </div>

        </section>

        <footer class="rodape">
            Criado com LiCards
        </footer>

    </main>

</body>

</html>
"""

        # Salvar arquivo
        caminho = filedialog.asksaveasfilename(
            title="Salvar cartão digital",
            defaultextension=".html",
            initialfile="meu_cartao_digital.html",
            filetypes=[
                ("Página HTML", "*.html")
            ]
        )

        if not caminho:
            return

        with open(
            caminho,
            "w",
            encoding="utf-8"
        ) as arquivo:

            arquivo.write(pagina)

        messagebox.showinfo(
            "LiCards",
            "Cartão digital HTML criado com sucesso!"
        )

        webbrowser.open(
            Path(caminho).resolve().as_uri()
        )

    except Exception as erro:

        messagebox.showerror(
            "Erro ao exportar HTML",
            f"Não foi possível criar o cartão:\n{erro}"
        )

# =========================================================
# 12. INTERFACE PRINCIPAL
# =========================================================

app = ctk.CTk()

app.title("LiCards - Criador de Cartões Digitais")
app.geometry("1250x850")
app.minsize(1000, 700)

app.configure(fg_color="#1B1118")


# =========================================================
# 13. CABEÇALHO
# =========================================================

cabecalho = ctk.CTkFrame(
    app,
    fg_color="transparent"
)

cabecalho.pack(
    fill="x",
    padx=25,
    pady=15
)

ctk.CTkLabel(
    cabecalho,
    text="LiCards",
    font=("Arial", 32, "bold"),
    text_color=COR_DESTAQUE
).pack(anchor="w")

ctk.CTkLabel(
    cabecalho,
    text="Crie seu cartão. Mostre sua identidade.",
    font=("Arial", 14),
    text_color="#D5C5CE"
).pack(anchor="w")


# =========================================================
# 14. ÁREA PRINCIPAL
# =========================================================

conteudo = ctk.CTkFrame(
    app,
    fg_color="transparent"
)

conteudo.pack(
    fill="both",
    expand=True,
    padx=20,
    pady=10
)

conteudo.grid_columnconfigure(0, weight=1)
conteudo.grid_columnconfigure(1, weight=2)
conteudo.grid_rowconfigure(0, weight=1)


# =========================================================
# 15. FORMULÁRIO LATERAL
# =========================================================

formulario = ctk.CTkScrollableFrame(
    conteudo,
    width=340,
    fg_color="#291D25",
    corner_radius=15
)

formulario.grid(
    row=0,
    column=0,
    sticky="nsew",
    padx=(0, 15)
)


def titulo_secao(texto):

    ctk.CTkLabel(
        formulario,
        text=texto,
        font=("Arial", 16, "bold"),
        text_color=COR_DESTAQUE
    ).pack(
        anchor="w",
        padx=15,
        pady=(18, 7)
    )


def criar_campo(texto, placeholder="Digite aqui"):

    ctk.CTkLabel(
        formulario,
        text=texto,
        font=("Arial", 12, "bold"),
        text_color=COR_TEXTO
    ).pack(
        anchor="w",
        padx=15,
        pady=(9, 3)
    )

    campo = ctk.CTkEntry(
        formulario,
        placeholder_text=placeholder,
        height=36
    )

    campo.pack(
        fill="x",
        padx=15
    )

    return campo


# =========================================================
# 16. DADOS PESSOAIS
# =========================================================

titulo_secao("DADOS PESSOAIS")

campo_nome = criar_campo(
    "Nome",
    "Seu nome"
)

campo_profissao = criar_campo(
    "Profissão",
    "Sua profissão"
)

campo_localizacao = criar_campo(
    "Localização",
    "Cidade - Estado"
)

ctk.CTkLabel(
    formulario,
    text="Sobre mim / Descrição",
    font=("Arial", 12, "bold"),
    text_color=COR_TEXTO
).pack(
    anchor="w",
    padx=15,
    pady=(12, 3)
)

campo_descricao = ctk.CTkTextbox(
    formulario,
    height=90
)

campo_descricao.pack(
    fill="x",
    padx=15
)


# =========================================================
# 17. FOTOS
# =========================================================

titulo_secao("FOTOS")

ctk.CTkButton(
    formulario,
    text="📷 Escolher foto de perfil",
    command=lambda: selecionar_imagem("perfil")
).pack(
    fill="x",
    padx=15,
    pady=5
)

status_perfil = ctk.CTkLabel(
    formulario,
    text="Nenhuma foto selecionada",
    font=("Arial", 10),
    text_color="#BBAAB4"
)

status_perfil.pack()

ctk.CTkButton(
    formulario,
    text="🖼 Escolher segunda imagem",
    command=lambda: selecionar_imagem("destaque")
).pack(
    fill="x",
    padx=15,
    pady=(12, 5)
)

status_destaque = ctk.CTkLabel(
    formulario,
    text="Segunda imagem opcional",
    font=("Arial", 10),
    text_color="#BBAAB4"
)

status_destaque.pack()

preto_branco = ctk.BooleanVar(value=False)

ctk.CTkCheckBox(
    formulario,
    text="Segunda imagem em preto e branco",
    variable=preto_branco,
    command=atualizar_previa
).pack(
    anchor="w",
    padx=15,
    pady=10
)


# =========================================================
# 18. CONTATOS DINÂMICOS
# =========================================================

titulo_secao("CONTATOS E REDES SOCIAIS")

ctk.CTkLabel(
    formulario,
    text="Adicione quantos contatos quiser.",
    font=("Arial", 11),
    text_color="#BBAAB4"
).pack(
    anchor="w",
    padx=15,
    pady=(0, 8)
)

contatos_container = ctk.CTkFrame(
    formulario,
    fg_color="transparent"
)

contatos_container.pack(
    fill="x",
    padx=10
)

# Contatos iniciais
adicionar_contato(
    "Instagram",
    "",
    "◎"
)

adicionar_contato(
    "WhatsApp",
    "",
    "☎"
)

adicionar_contato(
    "E-mail",
    "",
    "✉"
)

adicionar_contato(
    "LinkedIn",
    "",
    "in"
)

ctk.CTkButton(
    formulario,
    text="+ Adicionar outro contato",
    command=lambda: adicionar_contato(),
    fg_color="#59414E",
    hover_color="#755466"
).pack(
    fill="x",
    padx=15,
    pady=10
)


# =========================================================
# 19. PERSONALIZAR CORES
# =========================================================

titulo_secao("PERSONALIZAR CORES")

ctk.CTkButton(
    formulario,
    text="🎨 Cor do fundo",
    command=lambda: escolher_cor("fundo")
).pack(
    fill="x",
    padx=15,
    pady=5
)

ctk.CTkButton(
    formulario,
    text="🌈 Cor de destaque",
    command=lambda: escolher_cor("destaque")
).pack(
    fill="x",
    padx=15,
    pady=5
)

ctk.CTkButton(
    formulario,
    text="💗 Cor clara",
    command=lambda: escolher_cor("clara")
).pack(
    fill="x",
    padx=15,
    pady=5
)

ctk.CTkButton(
    formulario,
    text="Restaurar cores originais",
    command=restaurar_cores,
    fg_color="#59414E"
).pack(
    fill="x",
    padx=15,
    pady=5
)


# =========================================================
# 20. ÁREA DE PRÉ-VISUALIZAÇÃO
# =========================================================

area_previa = ctk.CTkFrame(
    conteudo,
    fg_color="#291D25",
    corner_radius=15
)

area_previa.grid(
    row=0,
    column=1,
    sticky="nsew"
)

ctk.CTkLabel(
    area_previa,
    text="PRÉ-VISUALIZAÇÃO",
    font=("Arial", 18, "bold"),
    text_color=COR_DESTAQUE
).pack(
    pady=20
)

previa = ctk.CTkLabel(
    area_previa,
    text="Sua prévia aparecerá aqui",
    width=600,
    height=350,
    fg_color="#1B1118",
    corner_radius=10
)

previa.pack(
    padx=15,
    pady=10
)


# =========================================================
# 21. BOTÕES DE AÇÃO
# =========================================================

ctk.CTkButton(
    area_previa,
    text="🔄 Atualizar cartão",
    command=atualizar_previa,
    height=42
).pack(
    fill="x",
    padx=60,
    pady=(20, 8)
)

ctk.CTkButton(
    area_previa,
    text="⬇ Baixar cartão PNG",
    command=baixar_png,
    height=42,
    fg_color="#C64F87",
    hover_color="#A83D70"
).pack(
    fill="x",
    padx=60,
    pady=8
)

ctk.CTkButton(
    area_previa,
    text="🔗 Exportar cartão digital HTML",
    command=exportar_html,
    height=42,
    fg_color="#59414E",
    hover_color="#755466"
).pack(
    fill="x",
    padx=60,
    pady=8
)


# =========================================================
# 22. INICIAR PROGRAMA
# =========================================================

atualizar_previa()

app.mainloop()