"""
Defesa Orbital - jogo de tiro espacial com Pygame
Recuperação de Computação Gráfica

Objetivo: sobreviver a três ondas de inimigos protegendo a estação.
Controles: veja o arquivo LEIAME.txt (WASD/setas movem, mouse mira,
botão esquerdo atira, P pausa).
"""
import math
import os
import random
import sys
import pygame

# ----------------------------------------------------------------------
# CONSTANTES (velocidades em pixels por segundo; tempos em segundos)
# ----------------------------------------------------------------------
LARGURA, ALTURA = 900, 650
FPS = 60

VEL_NAVE = 300
VEL_PROJETIL = 700
INTERVALO_TIRO = 0.250          # 250 ms entre disparos
VIDA_MAXIMA = 100
DANO_CONTATO = 20
TEMPO_PROTECAO = 1.0            # intervalo de proteção após levar dano

# Cada onda: quantidade de inimigos de cada tipo, multiplicador de
# velocidade e intervalo entre as gerações. A dificuldade cresce a cada onda.
ONDAS = [
    {"retos": 5,  "perseguidores": 2, "vel": 1.00, "intervalo": 1.2},
    {"retos": 7,  "perseguidores": 5, "vel": 1.25, "intervalo": 0.9},
    {"retos": 9,  "perseguidores": 9, "vel": 1.50, "intervalo": 0.7},
]
VEL_RETO = 130
VEL_PERSEGUIDOR = 95
PAUSA_ENTRE_ONDAS = 2.0

PASTA = os.path.dirname(os.path.abspath(__file__))
PASTA_ASSETS = os.path.join(PASTA, "assets")


# ----------------------------------------------------------------------
# RECURSOS
# ----------------------------------------------------------------------
def carregar_imagem(nome, tamanho, cor):
    caminho = os.path.join(PASTA_ASSETS, nome)
    try:
        return pygame.image.load(caminho).convert_alpha()
    except (pygame.error, FileNotFoundError):
        surf = pygame.Surface(tamanho, pygame.SRCALPHA)
        pygame.draw.circle(surf, cor, (tamanho[0] // 2, tamanho[1] // 2), min(tamanho) // 2)
        return surf


class SomVazio:
    def play(self):
        pass


def carregar_som(nome):
    try:
        return pygame.mixer.Sound(os.path.join(PASTA_ASSETS, nome))
    except (pygame.error, FileNotFoundError):
        return SomVazio()


# ----------------------------------------------------------------------
# SPRITES
# ----------------------------------------------------------------------
class Nave(pygame.sprite.Sprite):
    def __init__(self, imagem):
        super().__init__()
        self.imagem_base = imagem               # imagem apontando para cima
        self.image = imagem
        self.pos = pygame.Vector2(LARGURA / 2, ALTURA / 2 + 120)
        self.rect = self.image.get_rect(center=self.pos)
        self.raio = 18                          # usado na colisão circular
        self.vida = VIDA_MAXIMA
        self.recarga = 0.0                      # tempo até poder atirar de novo
        self.protecao = 0.0                     # tempo restante de proteção
        self.ultima_mira = pygame.Vector2(0, -1)

    def direcao_mira(self):
        """Vetor normalizado da nave até o cursor do mouse.
        Se o cursor estiver exatamente no centro da nave (vetor nulo),
        usa a última direção válida em vez de dividir por zero."""
        alvo = pygame.Vector2(pygame.mouse.get_pos()) - self.pos
        if alvo.length_squared() > 1e-6:
            self.ultima_mira = alvo.normalize()
        return self.ultima_mira

    def update(self, dt):
        # ---- movimento (WASD ou setas) ----
        teclas = pygame.key.get_pressed()
        mov = pygame.Vector2(
            (teclas[pygame.K_d] or teclas[pygame.K_RIGHT]) - (teclas[pygame.K_a] or teclas[pygame.K_LEFT]),
            (teclas[pygame.K_s] or teclas[pygame.K_DOWN]) - (teclas[pygame.K_w] or teclas[pygame.K_UP]),
        )
        # normaliza: na diagonal a velocidade total é igual à horizontal/vertical
        if mov.length_squared() > 0:
            mov = mov.normalize()
        self.pos += mov * VEL_NAVE * dt

        # mantém a nave dentro da janela
        meia_l, meia_a = self.imagem_base.get_width() / 2, self.imagem_base.get_height() / 2
        self.pos.x = max(meia_l, min(LARGURA - meia_l, self.pos.x))
        self.pos.y = max(meia_a, min(ALTURA - meia_a, self.pos.y))

        # ---- rotação para o mouse ----
        mira = self.direcao_mira()
        # imagem aponta para cima (0,-1); rotate() gira no sentido anti-horário,
        # por isso o sinal negativo do ângulo
        angulo = -pygame.Vector2(0, -1).angle_to(mira)
        self.image = pygame.transform.rotate(self.imagem_base, angulo)
        self.rect = self.image.get_rect(center=(round(self.pos.x), round(self.pos.y)))

        # ---- temporizadores (só avançam quando update é chamado, ou seja, fora da pausa) ----
        self.recarga = max(0.0, self.recarga - dt)
        self.protecao = max(0.0, self.protecao - dt)

    def pode_atirar(self):
        return self.recarga <= 0

    def atirar(self, imagem_projetil):
        self.recarga = INTERVALO_TIRO
        direcao = self.direcao_mira()
        # o projétil nasce na ponta da nave
        origem = self.pos + direcao * 24
        return Projetil(origem, direcao, imagem_projetil)

    def levar_dano(self):
        """Retorna True se o dano foi aplicado (fora do período de proteção)."""
        if self.protecao > 0:
            return False
        self.vida = max(0, self.vida - DANO_CONTATO)
        self.protecao = TEMPO_PROTECAO
        return True


class Projetil(pygame.sprite.Sprite):
    def __init__(self, pos, direcao, imagem):
        super().__init__()
        angulo = -pygame.Vector2(0, -1).angle_to(direcao)
        self.image = pygame.transform.rotate(imagem, angulo)
        self.pos = pygame.Vector2(pos)
        self.vel = direcao * VEL_PROJETIL        # px/s
        self.rect = self.image.get_rect(center=self.pos)

    def update(self, dt):
        self.pos += self.vel * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        # remove o projétil que saiu da área visível
        if not self.rect.colliderect(pygame.Rect(0, 0, LARGURA, ALTURA)):
            self.kill()


def ponto_de_entrada():
    """Sorteia um ponto fora da janela, em uma das quatro bordas."""
    lado = random.choice("cbel")  # cima, baixo, esquerda(e), direita(l)
    margem = 40
    if lado == "c":
        return pygame.Vector2(random.uniform(0, LARGURA), -margem)
    if lado == "b":
        return pygame.Vector2(random.uniform(0, LARGURA), ALTURA + margem)
    if lado == "e":
        return pygame.Vector2(-margem, random.uniform(0, ALTURA))
    return pygame.Vector2(LARGURA + margem, random.uniform(0, ALTURA))


class InimigoReto(pygame.sprite.Sprite):
    """Inimigo que anda em linha reta. Ao chegar a uma borda, ricocheteia
    (assim continua na tela até ser destruído, como a onda exige)."""
    pontos = 10

    def __init__(self, imagem, multiplicador):
        super().__init__()
        self.image = imagem
        self.pos = ponto_de_entrada()
        self.raio = 16
        self.vida = 1
        # escolhe um ponto aleatório na área central e segue até ele
        alvo = pygame.Vector2(random.uniform(150, LARGURA - 150),
                              random.uniform(150, ALTURA - 150))
        direcao = alvo - self.pos
        direcao = direcao.normalize() if direcao.length_squared() > 0 else pygame.Vector2(0, 1)
        self.vel = direcao * VEL_RETO * multiplicador
        self.rect = self.image.get_rect(center=self.pos)

    def update(self, dt, alvo_pos=None):
        self.pos += self.vel * dt
        # ricochete (só quando está indo para fora da janela)
        if self.pos.x < self.raio and self.vel.x < 0:
            self.vel.x *= -1
        elif self.pos.x > LARGURA - self.raio and self.vel.x > 0:
            self.vel.x *= -1
        if self.pos.y < self.raio and self.vel.y < 0:
            self.vel.y *= -1
        elif self.pos.y > ALTURA - self.raio and self.vel.y > 0:
            self.vel.y *= -1
        self.rect.center = (round(self.pos.x), round(self.pos.y))


class InimigoPerseguidor(pygame.sprite.Sprite):
    """Inimigo que recalcula a direção a cada quadro para seguir a nave."""
    pontos = 20

    def __init__(self, imagem, multiplicador):
        super().__init__()
        self.image = imagem
        self.pos = ponto_de_entrada()
        self.raio = 16
        self.vida = 2                   # precisa de 2 tiros
        self.velocidade = VEL_PERSEGUIDOR * multiplicador
        self.rect = self.image.get_rect(center=self.pos)

    def update(self, dt, alvo_pos=None):
        if alvo_pos is not None:
            direcao = alvo_pos - self.pos
            if direcao.length_squared() > 1e-6:      # evita normalizar vetor nulo
                self.pos += direcao.normalize() * self.velocidade * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))


# ----------------------------------------------------------------------
# JOGO
# ----------------------------------------------------------------------
class Jogo:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
        except pygame.error:
            pass
        self.tela = pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption("Defesa Orbital")
        self.relogio = pygame.time.Clock()
        self.fonte = pygame.font.SysFont(None, 28)
        self.fonte_grande = pygame.font.SysFont(None, 64)

        self.img_nave = carregar_imagem("nave.png", (48, 48), (80, 200, 255))
        self.img_reto = carregar_imagem("inimigo_reto.png", (36, 36), (255, 120, 60))
        self.img_perseguidor = carregar_imagem("inimigo_perseguidor.png", (36, 36), (255, 60, 200))
        self.img_projetil = carregar_imagem("projetil.png", (8, 20), (255, 255, 120))
        self.img_estacao = carregar_imagem("estacao.png", (140, 140), (180, 180, 200))
        self.som_tiro = carregar_som("tiro.wav")
        self.som_explosao = carregar_som("explosao.wav")
        self.som_dano = carregar_som("dano.wav")

        random.seed()
        self.estrelas = [(random.randrange(LARGURA), random.randrange(ALTURA), random.choice((1, 1, 2)))
                         for _ in range(90)]
        self.estado = "menu"      # menu | jogando | pausado | vitoria | derrota
        self.reiniciar()

    def reiniciar(self):
        """Restaura todos os valores iniciais."""
        self.nave = Nave(self.img_nave)
        self.projeteis = pygame.sprite.Group()
        self.inimigos = pygame.sprite.Group()
        self.pontos = 0
        self.onda = 0                  # índice da onda atual
        self.iniciar_onda()

    def iniciar_onda(self):
        cfg = ONDAS[self.onda]
        # fila de inimigos a gerar (embaralhada para misturar os tipos)
        self.fila = ["reto"] * cfg["retos"] + ["perseguidor"] * cfg["perseguidores"]
        random.shuffle(self.fila)
        self.tempo_geracao = 0.5
        self.pausa_onda = 0.0
        self.onda_concluida = False

    # ------------------------------------------------------------------
    def atualizar(self, dt):
        cfg = ONDAS[self.onda]
        self.nave.update(dt)

        # disparo: botão esquerdo, respeitando o intervalo de 250 ms
        if pygame.mouse.get_pressed()[0] and self.nave.pode_atirar():
            self.projeteis.add(self.nave.atirar(self.img_projetil))
            self.som_tiro.play()

        self.projeteis.update(dt)
        for inimigo in self.inimigos:
            inimigo.update(dt, self.nave.pos)

        # ---- geração dos inimigos da onda ----
        if self.fila:
            self.tempo_geracao -= dt
            if self.tempo_geracao <= 0:
                tipo = self.fila.pop()
                classe = InimigoReto if tipo == "reto" else InimigoPerseguidor
                img = self.img_reto if tipo == "reto" else self.img_perseguidor
                self.inimigos.add(classe(img, cfg["vel"]))
                self.tempo_geracao = cfg["intervalo"]

        # ---- projéteis x inimigos: cada projétil acerta só UM inimigo ----
        acertos = pygame.sprite.groupcollide(self.projeteis, self.inimigos, True, False,
                                             pygame.sprite.collide_circle_ratio(0.9))
        # (os projéteis acima já foram removidos; aplicamos dano ao 1º inimigo de cada um)
        ja_atingidos = set()
        for projetil, lista in acertos.items():
            alvo = lista[0]
            alvo.vida -= 1
            if alvo.vida <= 0 and alvo not in ja_atingidos:
                ja_atingidos.add(alvo)
                self.pontos += alvo.pontos
                self.som_explosao.play()
                alvo.kill()

        # ---- nave x inimigos: dano com intervalo de proteção ----
        for inimigo in self.inimigos:
            if self.colide_circulo(self.nave, inimigo):
                if self.nave.levar_dano():
                    self.som_dano.play()
                break

        if self.nave.vida <= 0:
            self.estado = "derrota"
            return

        # ---- fim de onda: tudo gerado E tudo destruído ----
        if not self.fila and len(self.inimigos) == 0:
            if self.onda == len(ONDAS) - 1:
                self.estado = "vitoria"
            else:
                self.pausa_onda += dt
                self.onda_concluida = True
                if self.pausa_onda >= PAUSA_ENTRE_ONDAS:
                    self.onda += 1
                    self.iniciar_onda()

    @staticmethod
    def colide_circulo(a, b):
        return a.pos.distance_to(b.pos) < a.raio + b.raio

    # ------------------------------------------------------------------
    def texto(self, msg, fonte, cor, centro=None, topleft=None):
        surf = fonte.render(msg, True, cor)
        rect = surf.get_rect(center=centro) if centro else surf.get_rect(topleft=topleft)
        self.tela.blit(surf, rect)

    def desenhar(self):
        self.tela.fill((8, 10, 24))
        for x, y, r in self.estrelas:
            pygame.draw.circle(self.tela, (140, 150, 190), (x, y), r)

        # estação espacial no centro (decoração do cenário)
        self.tela.blit(self.img_estacao, self.img_estacao.get_rect(center=(LARGURA // 2, ALTURA // 2)))

        self.projeteis.draw(self.tela)
        self.inimigos.draw(self.tela)

        # a nave pisca enquanto está protegida
        if not (self.nave.protecao > 0 and int(self.nave.protecao * 12) % 2 == 0):
            self.tela.blit(self.nave.image, self.nave.rect)

        # ---- HUD ----
        # barra de vida
        pygame.draw.rect(self.tela, (60, 20, 20), (15, 15, 220, 20))
        largura_vida = int(220 * self.nave.vida / VIDA_MAXIMA)
        cor = (80, 220, 100) if self.nave.vida > 40 else (240, 80, 70)
        pygame.draw.rect(self.tela, cor, (15, 15, largura_vida, 20))
        pygame.draw.rect(self.tela, (255, 255, 255), (15, 15, 220, 20), 2)
        self.texto("Vida", self.fonte, (255, 255, 255), topleft=(245, 17))
        self.texto(f"Pontos: {self.pontos}", self.fonte, (255, 255, 255), topleft=(15, 45))
        self.texto(f"Onda {self.onda + 1} de {len(ONDAS)}", self.fonte, (120, 220, 255),
                   topleft=(LARGURA - 150, 17))
        if self.onda_concluida and self.estado == "jogando":
            self.texto(f"Onda {self.onda + 1} concluída!", self.fonte_grande, (255, 240, 130),
                       centro=(LARGURA // 2, 120))

    def tela_mensagem(self, titulo, linhas, cor):
        veu = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        veu.fill((0, 0, 0, 170))
        self.tela.blit(veu, (0, 0))
        self.texto(titulo, self.fonte_grande, cor, centro=(LARGURA // 2, ALTURA // 2 - 50))
        for i, linha in enumerate(linhas):
            self.texto(linha, self.fonte, (230, 230, 230),
                       centro=(LARGURA // 2, ALTURA // 2 + 10 + i * 32))

    # ------------------------------------------------------------------
    def executar(self):
        while True:
            # delta time em segundos (limitado para evitar saltos grandes)
            dt = min(self.relogio.tick(FPS) / 1000, 0.05)

            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if self.estado == "menu" and evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.estado = "jogando"
                    elif evento.key == pygame.K_p:
                        if self.estado == "jogando":
                            self.estado = "pausado"
                        elif self.estado == "pausado":
                            self.estado = "jogando"
                    elif self.estado in ("vitoria", "derrota") and evento.key in (pygame.K_r, pygame.K_RETURN):
                        self.reiniciar()
                        self.estado = "jogando"

            # Na pausa, atualizar() não é chamado: movimentos, geração de
            # inimigos, recarga do tiro e proteção ficam todos congelados.
            if self.estado == "jogando":
                self.atualizar(dt)

            self.desenhar()
            if self.estado == "menu":
                self.tela_mensagem("DEFESA ORBITAL",
                                   ["Proteja a estação durante 3 ondas de ataque.",
                                    "WASD/Setas: mover  |  Mouse: mirar  |  Botão esquerdo: atirar",
                                    "P: pausa   |   Pressione ENTER para começar"],
                                   (120, 220, 255))
            elif self.estado == "pausado":
                self.tela_mensagem("PAUSADO", ["Pressione P para continuar"], (255, 240, 130))
            elif self.estado == "vitoria":
                self.tela_mensagem("VITÓRIA!", [f"Pontuação final: {self.pontos}",
                                                "Pressione R ou ENTER para jogar de novo"],
                                   (120, 255, 150))
            elif self.estado == "derrota":
                self.tela_mensagem("DERROTA", [f"Pontuação: {self.pontos}",
                                               "Pressione R ou ENTER para tentar de novo"],
                                   (255, 110, 110))
            pygame.display.flip()


if __name__ == "__main__":
    Jogo().executar()
