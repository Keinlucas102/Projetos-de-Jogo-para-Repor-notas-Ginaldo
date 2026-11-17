"""Gera as imagens (PNG com transparência) e os sons (WAV) dos dois jogos."""
import math, os, struct, wave
from PIL import Image, ImageDraw

E = 4  # desenha em escala maior e reduz, para bordas suaves

def nova(w, h):
    return Image.new("RGBA", (w * E, h * E), (0, 0, 0, 0))

def salvar(img, caminho, w, h):
    img.resize((w, h), Image.LANCZOS).save(caminho)

def p(*v):  # escala coordenadas
    return [c * E for c in v]

# ---------------- Missão dos Cristais ----------------
d = "missao_cristais/assets"
# jogador 28x36
im = nova(28, 36); g = ImageDraw.Draw(im)
g.rounded_rectangle(p(4, 12, 24, 34), radius=4 * E, fill=(60, 120, 220, 255))
g.ellipse(p(3, 0, 25, 20), fill=(235, 240, 250, 255), outline=(40, 60, 120, 255), width=E)
g.rounded_rectangle(p(8, 5, 22, 14), radius=3 * E, fill=(40, 200, 240, 255))
g.rectangle(p(6, 30, 12, 36), fill=(30, 60, 130, 255)); g.rectangle(p(16, 30, 22, 36), fill=(30, 60, 130, 255))
salvar(im, f"{d}/jogador.png", 28, 36)
# cristal 24x28
im = nova(24, 28); g = ImageDraw.Draw(im)
g.polygon(p(12, 0, 22, 9, 18, 26, 6, 26, 2, 9), fill=(70, 220, 255, 255), outline=(255, 255, 255, 255))
g.polygon(p(12, 0, 22, 9, 12, 12), fill=(190, 250, 255, 255))
g.line(p(12, 12, 18, 26), fill=(255, 255, 255, 200), width=E)
salvar(im, f"{d}/cristal.png", 24, 28)
# inimigo 32x32
im = nova(32, 32); g = ImageDraw.Draw(im)
g.rounded_rectangle(p(2, 8, 30, 32), radius=8 * E, fill=(220, 60, 70, 255))
g.polygon(p(4, 10, 8, 0, 13, 9), fill=(220, 60, 70, 255)); g.polygon(p(28, 10, 24, 0, 19, 9), fill=(220, 60, 70, 255))
g.ellipse(p(7, 13, 14, 21), fill="white"); g.ellipse(p(18, 13, 25, 21), fill="white")
g.ellipse(p(10, 15, 13, 19), fill="black"); g.ellipse(p(19, 15, 22, 19), fill="black")
salvar(im, f"{d}/inimigo.png", 32, 32)
# bloco 40x40 (opaco)
im = Image.new("RGBA", (40, 40), (88, 92, 120, 255)); g = ImageDraw.Draw(im)
g.rectangle((0, 0, 39, 5), fill=(120, 190, 130, 255))
g.rectangle((0, 0, 39, 39), outline=(50, 54, 78, 255), width=2)
g.line((0, 20, 39, 20), fill=(70, 74, 100, 255), width=1)
im.save(f"{d}/bloco.png")
# portal 40x80
im = nova(40, 80); g = ImageDraw.Draw(im)
g.ellipse(p(2, 2, 38, 78), fill=(130, 60, 220, 255), outline=(220, 180, 255, 255), width=2 * E)
g.ellipse(p(9, 12, 31, 68), fill=(210, 150, 255, 255))
g.ellipse(p(15, 24, 25, 56), fill=(255, 255, 255, 255))
salvar(im, f"{d}/portal.png", 40, 80)

# ---------------- Defesa Orbital ----------------
d = "defesa_orbital/assets"
im = nova(48, 48); g = ImageDraw.Draw(im)  # nave apontando para cima
g.polygon(p(24, 1, 44, 44, 24, 36, 4, 44), fill=(90, 190, 255, 255), outline=(255, 255, 255, 255))
g.polygon(p(24, 8, 30, 28, 18, 28), fill=(220, 245, 255, 255))
g.polygon(p(18, 38, 24, 47, 30, 38), fill=(255, 170, 60, 255))
salvar(im, f"{d}/nave.png", 48, 48)
im = nova(36, 36); g = ImageDraw.Draw(im)
g.polygon(p(18, 1, 35, 18, 18, 35, 1, 18), fill=(255, 130, 60, 255), outline=(255, 230, 180, 255))
g.ellipse(p(11, 11, 25, 25), fill=(120, 30, 10, 255))
salvar(im, f"{d}/inimigo_reto.png", 36, 36)
im = nova(36, 36); g = ImageDraw.Draw(im)
g.ellipse(p(2, 2, 34, 34), fill=(210, 60, 200, 255), outline=(255, 190, 250, 255), width=E)
for ang in range(0, 360, 60):
    x, y = 18 + 17 * math.cos(math.radians(ang)), 18 + 17 * math.sin(math.radians(ang))
    g.ellipse(p(x - 3, y - 3, x + 3, y + 3), fill=(255, 190, 250, 255))
g.ellipse(p(12, 12, 24, 24), fill=(255, 255, 120, 255))
salvar(im, f"{d}/inimigo_perseguidor.png", 36, 36)
im = nova(8, 20); g = ImageDraw.Draw(im)
g.rounded_rectangle(p(1, 0, 7, 20), radius=3 * E, fill=(255, 255, 130, 255))
salvar(im, f"{d}/projetil.png", 8, 20)
im = nova(140, 140); g = ImageDraw.Draw(im)
g.ellipse(p(35, 35, 105, 105), fill=(150, 160, 185, 255), outline=(230, 235, 250, 255), width=2 * E)
g.rectangle(p(0, 62, 140, 78), fill=(110, 120, 150, 255))
g.rectangle(p(62, 0, 78, 140), fill=(110, 120, 150, 255))
for x0 in (6, 110):
    g.rectangle(p(x0, 52, x0 + 24, 88), fill=(60, 110, 200, 255), outline=(200, 220, 255, 255), width=E)
g.ellipse(p(55, 55, 85, 85), fill=(70, 220, 255, 255))
salvar(im, f"{d}/estacao.png", 140, 140)

# ---------------- Sons (WAV) ----------------
def tom(caminho, freqs, dur, vol=0.4, queda=True, ruido=False):
    taxa = 22050
    n = int(taxa * dur)
    dados = bytearray()
    seed = 12345
    for i in range(n):
        t = i / taxa
        f = freqs[0] + (freqs[-1] - freqs[0]) * (i / n)
        env = (1 - i / n) if queda else min(1, i / (0.05 * n)) * (1 - i / n)
        if ruido:
            seed = (seed * 1103515245 + 12345) & 0x7fffffff
            amostra = ((seed / 0x7fffffff) * 2 - 1)
        else:
            amostra = math.sin(2 * math.pi * f * t)
        dados += struct.pack("<h", int(amostra * env * vol * 32767))
    with wave.open(caminho, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(taxa); w.writeframes(bytes(dados))

tom("missao_cristais/assets/cristal.wav", (880, 1760), 0.18)
tom("missao_cristais/assets/pulo.wav", (300, 620), 0.15, 0.3)
tom("missao_cristais/assets/dano.wav", (220, 80), 0.3, 0.4)
tom("defesa_orbital/assets/tiro.wav", (1200, 300), 0.10, 0.25)
tom("defesa_orbital/assets/explosao.wav", (200, 60), 0.30, 0.45, ruido=True)
tom("defesa_orbital/assets/dano.wav", (240, 90), 0.30, 0.4)
print("assets gerados")
