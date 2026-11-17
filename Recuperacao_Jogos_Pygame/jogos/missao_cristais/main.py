"""
Missão dos Cristais - jogo de plataforma com Pygame
Recuperação de Computação Gráfica

Objetivo: coletar todos os cristais e chegar ao portal sem perder as 3 vidas.
Controles: veja o arquivo LEIAME.txt (setas/A-D movem, ESPAÇO/↑/W pula).
"""
import os
import sys
import pygame

# ----------------------------------------------------------------------
# CONSTANTES
# ----------------------------------------------------------------------
LARGURA, ALTURA = 800, 600          # tamanho da janela
FPS = 60
TILE = 40                           # tamanho de cada bloco da matriz (px)

VEL_JOGADOR = 260                   # px/s
GRAVIDADE = 1800                    # px/s²
FORCA_PULO = -640                   # px/s (negativo = para cima)
VEL_QUEDA_MAX = 900                 # limita a velocidade de queda
VEL_INIMIGO = 90                    # px/s
TEMPO_INVULNERAVEL = 1.5            # segundos
VIDAS_INICIAIS = 3
PONTOS_CRISTAL = 10

PASTA = os.path.dirname(os.path.abspath(__file__))
PASTA_ASSETS = os.path.join(PASTA, "assets")

# ----------------------------------------------------------------------
# FASE (matriz de caracteres)
#   #  plataforma/chão     C  cristal      E  inimigo
#   P  posição inicial     G  portal       .  espaço vazio
# A fase tem 60 colunas x 15 linhas (2400 x 600 px): maior que a janela.
# ----------------------------------------------------------------------
FASE = [
    "............................................................",
    "............................................................",
    "............................................................",
    "............................................................",
    "............................................................",
    "............................................................",
    "............................................................",
    "............................................................",
    "..........................CC..............C.................",
    ".........................####............####...............",
    ".........CC..........C.........C#....C......................",
    "........####....##..####............####......##............",
    "..P........E.........C..E...............E...........CE...G..",
    "###############...############...############...############",
    "###############...############...############...############",
]

LARGURA_MUNDO = len(FASE[0]) * TILE
ALTURA_MUNDO = len(FASE) * TILE


# ----------------------------------------------------------------------
# RECURSOS (imagens e sons) - com alternativa caso um arquivo falte
# ----------------------------------------------------------------------
def carregar_imagem(nome, tamanho, cor_alternativa):
    """Carrega uma imagem PNG com transparência (convert_alpha)."""
    caminho = os.path.join(PASTA_ASSETS, nome)
    try:
        return pygame.image.load(caminho).convert_alpha()
    except (pygame.error, FileNotFoundError):
        surf = pygame.Surface(tamanho, pygame.SRCALPHA)
        surf.fill(cor_alternativa)
        return surf


class SomVazio:
    """Usado quando não há placa de som: evita erros ao chamar play()."""
    def play(self):
        pass


def carregar_som(nome):
    caminho = os.path.join(PASTA_ASSETS, nome)
    try:
        return pygame.mixer.Sound(caminho)
    except (pygame.error, FileNotFoundError):
        return SomVazio()


# ----------------------------------------------------------------------
# SPRITES
# ----------------------------------------------------------------------
class Plataforma(pygame.sprite.Sprite):
    def __init__(self, x, y, imagem):
        super().__init__()
        self.image = imagem
        self.rect = self.image.get_rect(topleft=(x, y))


class Cristal(pygame.sprite.Sprite):
    def __init__(self, x, y, imagem):
        super().__init__()
        self.image = imagem
        # centraliza o cristal dentro do bloco da matriz
        self.rect = self.image.get_rect(center=(x + TILE // 2, y + TILE // 2))


class Portal(pygame.sprite.Sprite):
    def __init__(self, x, y, imagem):
        super().__init__()
        self.image = imagem
        # base do portal apoiada no chão do bloco
        self.rect = self.image.get_rect(midbottom=(x + TILE // 2, y + TILE))


class Inimigo(pygame.sprite.Sprite):
    """Inimigo que patrulha entre dois limites (esquerdo e direito)."""

    def __init__(self, x, y, imagem, limite_esq, limite_dir):
        super().__init__()
        self.image = imagem
        self.rect = self.image.get_rect(midbottom=(x + TILE // 2, y + TILE))
        self.pos_x = float(self.rect.x)
        self.limite_esq = limite_esq
        self.limite_dir = limite_dir
        self.direcao = 1  # 1 = direita, -1 = esquerda

    def update(self, dt):
        self.pos_x += self.direcao * VEL_INIMIGO * dt
        self.rect.x = round(self.pos_x)
        # ao chegar em um limite, inverte o sentido
        if self.rect.right >= self.limite_dir:
            self.rect.right = self.limite_dir
            self.pos_x = float(self.rect.x)
            self.direcao = -1
        elif self.rect.left <= self.limite_esq:
            self.rect.left = self.limite_esq
            self.pos_x = float(self.rect.x)
            self.direcao = 1


class Jogador(pygame.sprite.Sprite):
    def __init__(self, x, y, imagem):
        super().__init__()
        self.imagem_base = imagem
        self.image = imagem
        self.inicio = (x + TILE // 2, y + TILE)   # ponto de partida (midbottom)
        self.rect = self.image.get_rect(midbottom=self.inicio)
        self.pos = pygame.Vector2(self.rect.topleft)
        self.vel_y = 0.0
        self.no_chao = False
        self.olhando_direita = True
        self.invulneravel = 0.0   # tempo restante de invulnerabilidade (s)

    def reiniciar_posicao(self):
        """Volta ao ponto inicial (usado após cair no buraco)."""
        self.rect.midbottom = self.inicio
        self.pos.update(self.rect.topleft)
        self.vel_y = 0
        self.invulneravel = TEMPO_INVULNERAVEL

    def pular(self):
        # só pula se estiver apoiado em uma plataforma
        if self.no_chao:
            self.vel_y = FORCA_PULO
            self.no_chao = False
            return True
        return False

    def levar_dano(self):
        """Ativa a invulnerabilidade; retorna True se o dano valeu."""
        if self.invulneravel > 0:
            return False
        self.invulneravel = TEMPO_INVULNERAVEL
        self.vel_y = -350          # pequeno impulso ao ser atingido
        self.no_chao = False
        return True

    def update(self, dt, plataformas):
        teclas = pygame.key.get_pressed()

        # ---------------- movimento horizontal ----------------
        direcao = 0
        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            direcao -= 1
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            direcao += 1
        if direcao != 0:
            self.olhando_direita = direcao > 0

        self.pos.x += direcao * VEL_JOGADOR * dt
        self.rect.x = round(self.pos.x)
        self._colisao_horizontal(direcao, plataformas)

        # ---------------- movimento vertical ------------------
        self.vel_y = min(self.vel_y + GRAVIDADE * dt, VEL_QUEDA_MAX)
        self.pos.y += self.vel_y * dt
        self.rect.y = round(self.pos.y)
        self._colisao_vertical(plataformas)

        # não deixa sair pelas laterais do mundo
        if self.rect.left < 0:
            self.rect.left = 0
            self.pos.x = self.rect.x
        if self.rect.right > LARGURA_MUNDO:
            self.rect.right = LARGURA_MUNDO
            self.pos.x = self.rect.x

        # ---------------- invulnerabilidade -------------------
        if self.invulneravel > 0:
            self.invulneravel = max(0.0, self.invulneravel - dt)

        # imagem (espelhada conforme a direção)
        self.image = self.imagem_base if self.olhando_direita else \
            pygame.transform.flip(self.imagem_base, True, False)

    def _colisao_horizontal(self, direcao, plataformas):
        """Resolve colisões apenas no eixo X."""
        for p in pygame.sprite.spritecollide(self, plataformas, False):
            if direcao > 0:
                self.rect.right = p.rect.left
            elif direcao < 0:
                self.rect.left = p.rect.right
            self.pos.x = self.rect.x

    def _colisao_vertical(self, plataformas):
        """Resolve colisões apenas no eixo Y."""
        self.no_chao = False
        for p in pygame.sprite.spritecollide(self, plataformas, False):
            if self.vel_y > 0:            # caindo: pousa em cima
                self.rect.bottom = p.rect.top
                self.no_chao = True
                self.vel_y = 0
            elif self.vel_y < 0:          # subindo: bate a cabeça
                self.rect.top = p.rect.bottom
                self.vel_y = 0
            self.pos.y = self.rect.y


# ----------------------------------------------------------------------
# CONSTRUÇÃO DA FASE
# ----------------------------------------------------------------------
def eh_solido(matriz, linha, coluna):
    if 0 <= linha < len(matriz) and 0 <= coluna < len(matriz[0]):
        return matriz[linha][coluna] == "#"
    return False


def limites_patrulha(matriz, linha, coluna, alcance=4):
    """Calcula até onde o inimigo anda: para na borda da plataforma
    (ou ao encontrar uma parede) e no máximo 'alcance' blocos para cada lado."""
    esq = coluna
    while (esq - 1 >= 0 and coluna - (esq - 1) <= alcance
           and not eh_solido(matriz, linha, esq - 1)
           and eh_solido(matriz, linha + 1, esq - 1)):
        esq -= 1
    dir_ = coluna
    while (dir_ + 1 < len(matriz[0]) and (dir_ + 1) - coluna <= alcance
           and not eh_solido(matriz, linha, dir_ + 1)
           and eh_solido(matriz, linha + 1, dir_ + 1)):
        dir_ += 1
    return esq * TILE, (dir_ + 1) * TILE


class Jogo:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
        except pygame.error:
            pass  # sem áudio: o jogo continua funcionando
        self.tela = pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption("Missão dos Cristais")
        self.relogio = pygame.time.Clock()
        self.fonte = pygame.font.SysFont(None, 28)
        self.fonte_grande = pygame.font.SysFont(None, 64)

        # imagens (com transparência)
        self.img_jogador = carregar_imagem("jogador.png", (28, 36), (80, 160, 255, 255))
        self.img_cristal = carregar_imagem("cristal.png", (24, 28), (0, 255, 255, 255))
        self.img_inimigo = carregar_imagem("inimigo.png", (32, 32), (255, 60, 60, 255))
        self.img_bloco = carregar_imagem("bloco.png", (TILE, TILE), (90, 90, 110, 255))
        self.img_portal = carregar_imagem("portal.png", (40, 80), (190, 90, 255, 255))
        # sons
        self.som_cristal = carregar_som("cristal.wav")
        self.som_pulo = carregar_som("pulo.wav")
        self.som_dano = carregar_som("dano.wav")

        self.estado = "menu"      # menu | jogando | vitoria | derrota
        self.novo_jogo()

    # ------------------------------------------------------------------
    def novo_jogo(self):
        """Cria a fase do zero: restaura vidas, pontos, cristais e posições."""
        self.vidas = VIDAS_INICIAIS
        self.pontos = 0
        self.camera_x = 0

        self.plataformas = pygame.sprite.Group()
        self.cristais = pygame.sprite.Group()
        self.inimigos = pygame.sprite.Group()
        self.portais = pygame.sprite.GroupSingle()
        self.todos = pygame.sprite.Group()
        self.jogador = None

        for l, linha in enumerate(FASE):
            for c, simbolo in enumerate(linha):
                x, y = c * TILE, l * TILE
                if simbolo == "#":
                    self.plataformas.add(Plataforma(x, y, self.img_bloco))
                elif simbolo == "C":
                    self.cristais.add(Cristal(x, y, self.img_cristal))
                elif simbolo == "E":
                    esq, dir_ = limites_patrulha(FASE, l, c)
                    self.inimigos.add(Inimigo(x, y, self.img_inimigo, esq, dir_))
                elif simbolo == "P":
                    self.jogador = Jogador(x, y, self.img_jogador)
                elif simbolo == "G":
                    self.portais.add(Portal(x, y, self.img_portal))

        self.todos.add(self.plataformas, self.cristais, self.inimigos,
                       self.portais.sprite, self.jogador)

    # ------------------------------------------------------------------
    def atualizar_camera(self):
        """A câmera segue o jogador, mas nunca passa dos limites do mundo.
        Ela só muda o deslocamento usado no desenho: as posições reais
        (rect) dos objetos continuam sendo as do mundo."""
        alvo = self.jogador.rect.centerx - LARGURA // 2
        self.camera_x = max(0, min(alvo, LARGURA_MUNDO - LARGURA))

    def atualizar(self, dt):
        self.jogador.update(dt, self.plataformas)
        self.inimigos.update(dt)
        self.atualizar_camera()

        # cristais: dokill=True remove o cristal do grupo -> pontua só uma vez
        coletados = pygame.sprite.spritecollide(self.jogador, self.cristais, True)
        for _ in coletados:
            self.pontos += PONTOS_CRISTAL
            self.som_cristal.play()

        # inimigos: dano com invulnerabilidade de 1,5 s
        if pygame.sprite.spritecollide(self.jogador, self.inimigos, False):
            if self.jogador.levar_dano():
                self.vidas -= 1
                self.som_dano.play()

        # queda abaixo do cenário
        if self.jogador.rect.top > ALTURA_MUNDO + 50:
            self.vidas -= 1
            self.som_dano.play()
            self.jogador.reiniciar_posicao()

        if self.vidas <= 0:
            self.vidas = 0
            self.estado = "derrota"
            return

        # portal: só vale com todos os cristais coletados
        if (pygame.sprite.spritecollideany(self.jogador, self.portais)
                and len(self.cristais) == 0):
            self.estado = "vitoria"

    # ------------------------------------------------------------------
    def texto(self, msg, fonte, cor, centro=None, topleft=None):
        surf = fonte.render(msg, True, cor)
        rect = surf.get_rect(center=centro) if centro else surf.get_rect(topleft=topleft)
        self.tela.blit(surf, rect)

    def desenhar_fundo(self):
        self.tela.fill((18, 22, 40))
        # estrelas com efeito de paralaxe simples (só decoração)
        for i in range(60):
            x = (i * 137 - self.camera_x * 0.3) % LARGURA
            y = (i * 71) % (ALTURA - 120)
            pygame.draw.circle(self.tela, (120, 130, 170), (int(x), int(y)), 1 + i % 2)

    def desenhar(self):
        self.desenhar_fundo()

        # desenha cada sprite deslocando pela câmera (posição do mundo - camera_x)
        for spr in self.todos:
            if spr is self.jogador and self.jogador.invulneravel > 0:
                # pisca enquanto está invulnerável
                if int(self.jogador.invulneravel * 10) % 2 == 0:
                    continue
            self.tela.blit(spr.image, (spr.rect.x - self.camera_x, spr.rect.y))

        # HUD
        pygame.draw.rect(self.tela, (0, 0, 0), (0, 0, LARGURA, 36))
        self.texto(f"Pontos: {self.pontos}", self.fonte, (255, 255, 255), topleft=(12, 9))
        self.texto(f"Vidas: {self.vidas}", self.fonte, (255, 120, 120), topleft=(250, 9))
        self.texto(f"Cristais restantes: {len(self.cristais)}", self.fonte,
                   (120, 230, 255), topleft=(430, 9))

        # aviso ao tocar no portal sem ter todos os cristais
        if (pygame.sprite.spritecollideany(self.jogador, self.portais)
                and len(self.cristais) > 0):
            self.texto("Colete todos os cristais para usar o portal!", self.fonte,
                       (255, 230, 120), centro=(LARGURA // 2, 70))

    def tela_mensagem(self, titulo, subtitulo, cor):
        veu = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        veu.fill((0, 0, 0, 170))
        self.tela.blit(veu, (0, 0))
        self.texto(titulo, self.fonte_grande, cor, centro=(LARGURA // 2, ALTURA // 2 - 40))
        for i, linha in enumerate(subtitulo):
            self.texto(linha, self.fonte, (230, 230, 230),
                       centro=(LARGURA // 2, ALTURA // 2 + 20 + i * 32))

    # ------------------------------------------------------------------
    def executar(self):
        while True:
            dt = min(self.relogio.tick(FPS) / 1000, 1 / 30)  # limita para evitar "atravessar" blocos

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
                    elif self.estado == "jogando":
                        if evento.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                            if self.jogador.pular():
                                self.som_pulo.play()
                    elif self.estado in ("vitoria", "derrota"):
                        if evento.key in (pygame.K_RETURN, pygame.K_r):
                            self.novo_jogo()
                            self.estado = "jogando"

            if self.estado == "jogando":
                self.atualizar(dt)

            self.desenhar()
            if self.estado == "menu":
                self.tela_mensagem("MISSÃO DOS CRISTAIS",
                                   ["Colete todos os cristais e alcance o portal.",
                                    "Setas ou A/D: mover   |   ESPAÇO, ↑ ou W: pular",
                                    "Pressione ENTER para começar"],
                                   (120, 230, 255))
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
