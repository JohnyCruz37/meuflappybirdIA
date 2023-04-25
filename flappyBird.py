import pygame
import os
import random
import neat

inteligencia = True
geracao = 0

# tamanho da área do jogo

TELA_LARGURA = 500
TELA_ALTURA = 700

# constantes

IMAGEM_CANO = pygame.transform.scale2x(
    pygame.image.load(os.path.join("imgs", "pipe.png"))
)
IMAGEM_CHAO = pygame.transform.scale2x(
    pygame.image.load(os.path.join("imgs", "base.png"))
)
IMAGEM_BG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))
IMAGENS_PASSARO = [
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))),
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))),
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png"))),
]

pygame.font.init()
FONTE_PONTOS = pygame.font.SysFont("calibri", 30)


# objetos do jogo
class Passaro:
    IMGS = IMAGENS_PASSARO

    # animação
    ROTACAO_MAX = 25
    VELOCIDADE_ROTACAO = 20
    TEMPO_ANIMACAO = 5

    # atributos
    def __init__(self, x, y):
        # inicialização do passaro
        self.x = x
        self.y = y
        self.angulo = 0
        self.velocidade = 0
        self.altura = self.y
        self.tempo = 0
        self.contagem_img = 0
        self.img = self.IMGS[0]

    def pular(self):
        self.velocidade = -10.5
        self.tempo = 0
        self.altura = self.y

    def mover(self):
        # calcular deslocamento
        self.tempo += 1
        # formula de aceleração => S = so + vot + at^2/2
        deslocamento = 1.5 * (self.tempo**2) + self.velocidade * self.tempo

        # restringir deslocamento
        if deslocamento > 12:
            deslocamento = 12
        elif deslocamento < 0:
            deslocamento -= 2

        # deslocar o passaro
        self.y += deslocamento

        # animaçâo do angulo
        if deslocamento < 0 or self.y < (self.altura + 50):
            if self.angulo < self.ROTACAO_MAX:
                self.angulo = self.ROTACAO_MAX
        else:
            if self.angulo > -90:
                self.angulo -= self.VELOCIDADE_ROTACAO

    def desenhar(self, tela):
        # definir imagem
        self.contagem_img += 1

        if self.contagem_img < self.TEMPO_ANIMACAO:
            self.img = self.IMGS[0]
        elif self.contagem_img < self.TEMPO_ANIMACAO * 2:
            self.img = self.IMGS[1]
        elif self.contagem_img < self.TEMPO_ANIMACAO * 3:
            self.img = self.IMGS[2]
        elif self.contagem_img < self.TEMPO_ANIMACAO * 4:
            self.img = self.IMGS[1]
        elif self.contagem_img >= (self.TEMPO_ANIMACAO * 4) + 1:
            self.img = self.IMGS[0]
            self.contagem_img = 0

        # não bater a asa quando estiver caindo
        if self.angulo <= -80:
            self.img = self.IMGS[2]
            # define que se caso o passaro esteja caindo a proxima batida da asa seja para baixo
            self.contagem_img = self.TEMPO_ANIMACAO * 2

        # desenhar a imagem
        #  rotaciona a imagem do passaro
        img_rotacionada = pygame.transform.rotate(self.img, self.angulo)

        # define a posição central do passaro
        posicao_centro = self.img.get_rect(topleft=(self.x, self.y)).center

        # posiciona o passaro na tela
        posicao = img_rotacionada.get_rect(center=posicao_centro)
        tela.blit(img_rotacionada, posicao.topleft)

    def pegar_mascara(self):
        return pygame.mask.from_surface(self.img)


class Cano:
    # constante do cano
    DISTANCIA = 200
    VELOCIDADE = 5

    def __init__(self, x):
        self.x = x
        self.altura = 0
        self.posicao_topo = 0
        self.posicao_base = 0
        self.CANO_TOPO = pygame.transform.flip(IMAGEM_CANO, False, True)
        self.CANO_BASE = IMAGEM_CANO
        self.passou = False
        self.definir_altura()

    def definir_altura(self):
        self.altura = random.randrange(50, 350)
        self.posicao_topo = self.altura - self.CANO_TOPO.get_height()
        self.posicao_base = self.altura + self.DISTANCIA

    def mover(self):
        self.x -= self.VELOCIDADE

    def desenhar(self, tela):
        tela.blit(self.CANO_TOPO, (self.x, self.posicao_topo))
        tela.blit(self.CANO_BASE, (self.x, self.posicao_base))

    def colidir(self, passaro):
        passaro_mask = passaro.pegar_mascara()
        topo_mask = pygame.mask.from_surface(self.CANO_TOPO)
        base_mask = pygame.mask.from_surface(self.CANO_BASE)

        distancia_topo = (self.x - passaro.x, self.posicao_topo - round(passaro.y))
        distancia_base = (self.x - passaro.x, self.posicao_base - round(passaro.y))

        topo_colisao = passaro_mask.overlap(topo_mask, distancia_topo)
        base_colisao = passaro_mask.overlap(base_mask, distancia_base)

        if topo_colisao or base_colisao:
            return True
        else:
            return False


class Chao:
    # constantes
    VELOCIDADE = 5
    LARGURA = IMAGEM_CHAO.get_width()
    IMG = IMAGEM_CHAO

    def __init__(self, y):
        self.y = y
        self.x0 = 0
        self.x1 = self.x0 + self.LARGURA

    def mover(self):
        self.x0 -= self.VELOCIDADE
        self.x1 -= self.VELOCIDADE

        if self.x0 + self.LARGURA < 0:
            self.x0 = self.x1 + self.LARGURA
        if self.x1 + self.LARGURA < 0:
            self.x1 = self.x0 + self.LARGURA

    def desenhar(self, tela):
        tela.blit(self.IMG, (self.x0, self.y))
        tela.blit(self.IMG, (self.x1, self.y))


# Função para desenhar o jogo na tela
def desenha_tela(tela, passaros, canos, chao, pontos):
    tela.blit(IMAGEM_BG, (0, 0))

    for passaro in passaros:
        passaro.desenhar(tela)

    for cano in canos:
        cano.desenhar(tela)

    texto = FONTE_PONTOS.render(f"Pontuação: {pontos}", 1, (255, 255, 255))
    tela.blit(texto, (TELA_LARGURA - 10 - texto.get_width(), 10))

    if inteligencia:
        texto = FONTE_PONTOS.render(f"Geração: {geracao}", 1, (255, 255, 255))
        tela.blit(texto, (10, 10))

    chao.desenhar(tela)
    pygame.display.update()


# Função principal
def principal(genomas, config):
    global geracao  # identifica que havera mudança no valor da variavel global
    geracao += 1

    if inteligencia:
        redes = []
        lista_genomas = []
        passaros = []
        for _, genoma in genomas:
            rede = neat.nn.FeedForwardNetwork.create(genoma, config)
            # pontuação interna dos passaros
            redes.append(rede)
            genoma.fitness = 0
            lista_genomas.append(genoma)
            passaros.append(Passaro(230, 250))
    else:
        passaros = [Passaro(230, 250)]

    chao = Chao(630)
    canos = [Cano(600)]
    tela = pygame.display.set_mode((TELA_LARGURA, TELA_ALTURA))
    pontos = 0
    relogio = pygame.time.Clock()

    rodando = True
    while rodando:
        relogio.tick(30)

        # inteção do jogador com o jogo
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
                pygame.quit()
                quit()
            if not inteligencia:
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_SPACE:
                        for passaro in passaros:
                            passaro.pular()

        i_cano = 0
        if len(passaros) > 0:
            if len(canos) > 1 and passaros[0].x > (
                canos[0].x + canos[0].CANO_TOPO.get_width()
            ):
                i_cano = 1
        else:
            rodando = False
            break

        # mover as coisas
        for i, passaro in enumerate(passaros):
            passaro.mover()

            if inteligencia:
                # premiar o passaro que avançar
                lista_genomas[i].fitness += 0.1

                # decisão de pular ou não pular
                output = redes[i].activate(
                    (
                        passaro.y,
                        abs(passaro.y - canos[i_cano].altura),
                        abs(passaro.y - canos[i_cano].posicao_base),
                    )
                )
                if output[0] > 0.5:
                    passaro.pular()

        chao.mover()

        add_cano = False
        remover_canos = []
        for cano in canos:
            for i, passaro in enumerate(passaros):
                if cano.colidir(passaro):
                    passaros.pop(i)
                    if inteligencia:
                        # punição para o passaro que colidir
                        lista_genomas[i].fitness -= 1
                        lista_genomas.pop(i)
                        redes.pop(i)

                if not cano.passou and passaro.x > cano.x:
                    cano.passou = True
                    add_cano = True
            cano.mover()

            if cano.x + cano.CANO_TOPO.get_width() < 0:
                remover_canos.append(cano)

        if add_cano:
            pontos += 1
            canos.append(Cano(500))
            for genoma in lista_genomas:
                # premiar o passaro que passar o cano
                genoma.fitness += 5
        for cano in remover_canos:
            canos.remove(cano)

        for i, passaro in enumerate(passaros):
            if (passaro.y + passaro.img.get_height()) > chao.y or passaro.y < 0:
                passaros.pop(i)
                if inteligencia:
                    lista_genomas.pop(i)
                    redes.pop(i)

        desenha_tela(tela, passaros, canos, chao, pontos)


def iniciar(config_arquivo):
    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_arquivo,
    )

    populacao = neat.Population(config)
    populacao.add_reporter(neat.StdOutReporter(True))
    populacao.add_reporter(neat.StatisticsReporter())

    if inteligencia:
        populacao.run(principal, 50)
    else:
        principal(None, None)


if __name__ == "__main__":
    arquivo = os.path.dirname(__file__)
    arquivo_config = os.path.join(arquivo, "config.txt")
    iniciar(arquivo_config)
