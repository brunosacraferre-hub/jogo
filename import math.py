import math
import random
import sys
import pygame

pygame.init()
W, H = 1000, 700
tela = pygame.display.set_mode((W, H))
pygame.display.set_caption("Ping Pong 3D Arcade")
relogio = pygame.time.Clock()
pygame.mouse.set_visible(False)

F0 = pygame.font.SysFont("Arial", 17, bold=True)
F1 = pygame.font.SysFont("Arial", 22, bold=True)
F2 = pygame.font.SysFont("Arial", 36, bold=True)
F3 = pygame.font.SysFont("Arial", 60, bold=True)

# ---------------- Mundo 3D (metros) ----------------
# x = lateral, y = altura (mesa em y=0), z = profundidade (jogador em +z, robô em -z)
G = 9.8
R = 0.05                      # raio da bola
MW, ML = 0.76, 1.37           # meia largura / meio comprimento da mesa
NET_H = 0.1525
CHAO = -0.76
PZ, RZ = 1.75, -1.75          # plano das raquetes (jogador / robô)
PAREDE_Z = -5.5

CAM = (0.0, 1.2, 3.6)
PITCH = math.radians(20)
SP, CP = math.sin(PITCH), math.cos(PITCH)
FOCO = 1100
CY = H * 0.5

PONTOS = 7
VEL_RODADA = {1: 3.4, 2: 4.4, 3: 5.6}      # velocidade da bola por rodada
VEL_ROBO = {1: 1.5, 2: 2.1, 3: 2.8}        # velocidade lateral do robô
ERRO_ROBO = {1: 0.22, 2: 0.15, 3: 0.10}    # imprecisão do robô
FALHA_ROBO = {1: 0.15, 2: 0.10, 3: 0.06}   # chance de errar a devolução


def clamp(v, a, b):
    return max(a, min(b, v))


def proj(x, y, z):
    dx, dy, dz = x - CAM[0], y - CAM[1], z - CAM[2]
    prof = max(0.2, -dy * SP - dz * CP)
    k = FOCO / prof
    yc = dy * CP - dz * SP
    return (W / 2 + dx * k, CY - yc * k, k)


def P(pts):
    return [proj(*p)[:2] for p in pts]


# ---------------- Cenário (ginásio) pré-renderizado ----------------
def montar_cenario():
    s = pygame.Surface((W, H))
    for y in range(H):  # parede em degradê
        t = y / H
        pygame.draw.line(s, (int(78 - 28 * t), int(96 - 30 * t), int(128 - 34 * t)), (0, y), (W, y))
    pygame.draw.polygon(s, (32, 42, 60), [proj(x, y, PAREDE_Z)[:2] for x, y in [(-14, CHAO), (14, CHAO), (14, 5), (-14, 5)]])
    for y in range(H):
        t = y / H
        pygame.draw.line(s, (int(78 - 28 * t), int(96 - 30 * t), int(128 - 34 * t)), (0, y), (W, y))
    # janelas no alto
    for i in range(-5, 6):
        pts = [(i * 1.5 - 0.5, 3.2), (i * 1.5 + 0.5, 3.2), (i * 1.5 + 0.5, 4.4), (i * 1.5 - 0.5, 4.4)]
        pygame.draw.polygon(s, (170, 205, 235), [proj(x, y, PAREDE_Z)[:2] for x, y in pts])
    # faixas/banners
    cores = [(200, 60, 50), (240, 190, 40), (50, 140, 200), (60, 170, 90)]
    for i, c in enumerate(cores * 2):
        x0 = -9.5 + i * 2.4
        pts = [(x0, 1.7), (x0 + 2.0, 1.7), (x0 + 2.0, 2.5), (x0, 2.5)]
        pygame.draw.polygon(s, c, [proj(x, y, PAREDE_Z)[:2] for x, y in pts])
    # arquibancada com torcida
    rng = random.Random(7)
    for r in range(3):
        y0 = CHAO + r * 0.45
        pts = [(-14, y0), (14, y0), (14, y0 + 0.45), (-14, y0 + 0.45)]
        pygame.draw.polygon(s, (52 + r * 12, 60 + r * 12, 84 + r * 10), [proj(x, y, PAREDE_Z)[:2] for x, y in pts])
        x = -9.0 + rng.random() * 0.2
        while x < 9.0:
            px_, py_, k = proj(x, y0 + 0.32, PAREDE_Z)
            cor = (rng.randint(60, 240), rng.randint(60, 240), rng.randint(60, 240))
            pygame.draw.circle(s, (230, 190, 150), (int(px_), int(py_)), max(2, int(0.09 * k)))
            pygame.draw.rect(s, cor, (px_ - 0.12 * k, py_ + 0.09 * k, 0.24 * k, 0.2 * k), border_radius=3)
            x += 0.38
    # piso de madeira
    for i in range(-14, 14):
        c = (178, 128, 78) if i % 2 == 0 else (168, 118, 70)
        pygame.draw.polygon(s, c, P([(i, CHAO, PAREDE_Z), (i + 1, CHAO, PAREDE_Z), (i + 1, CHAO, 2.9), (i, CHAO, 2.9)]))
    for zz in range(-5, 3):
        pygame.draw.line(s, (140, 95, 55), proj(-14, CHAO, zz)[:2], proj(14, CHAO, zz)[:2], 1)
    # rodapé
    pygame.draw.line(s, (20, 25, 35), proj(-14, CHAO, PAREDE_Z)[:2], proj(14, CHAO, PAREDE_Z)[:2], 4)
    # linhas da quadra
    L = (240, 240, 235)
    for a, b in [((-3, -4.6), (3, -4.6)), ((-3, 2.6), (3, 2.6)), ((-3, -4.6), (-3, 2.6)), ((3, -4.6), (3, 2.6)), ((0, -4.6), (0, 2.6))]:
        pygame.draw.line(s, L, proj(a[0], CHAO, a[1])[:2], proj(b[0], CHAO, b[1])[:2], 3)
    # sombra da mesa no piso
    pygame.draw.polygon(s, (120, 80, 48), P([(-MW - 0.1, CHAO, -ML - 0.1), (MW + 0.1, CHAO, -ML - 0.1), (MW + 0.2, CHAO, ML + 0.15), (-MW - 0.2, CHAO, ML + 0.15)]))
    return s


CENARIO = montar_cenario()

# ---------------- Estado do jogo ----------------
bx = by = bz = 0.0
vx = vy = vz = 0.0
hitter = "j"
quicas = 0
prev_z = 0.0

px, py = 0.0, 0.3
mvx = 0.0
rpx, rpy = 0.0, 0.35
erro_robo = 0.0
anim_j = anim_r = 0.0

estado = "saque"
servidor = "j"
timer = 0.0
msg = ""
rodada = 1
pts_j = pts_r = 0
rod_j = rod_r = 0
msg_rodada = ""


def lancar(quem, tx, tz, vel):
    """Lança a bola da posição atual para quicar em (tx, tz) do lado do adversário."""
    global vx, vy, vz, hitter, quicas, estado, prev_z
    vz = -vel if quem == "j" else vel
    T = (tz - bz) / vz
    vx = (tx - bx) / T
    vy = (R - by + 0.5 * G * T * T) / T
    hitter, quicas, estado, prev_z = quem, 0, "jogo", bz


def iniciar_saque():
    global estado, servidor, timer, bx, by, bz, vx, vy, vz
    total = pts_j + pts_r
    primeiro = "j" if rodada % 2 == 1 else "r"
    outro = "r" if primeiro == "j" else "j"
    servidor = primeiro if (total // 2) % 2 == 0 else outro
    estado, timer = "saque", 1.0
    vx = vy = vz = 0.0
    by = 0.45
    bz = 1.55 if servidor == "j" else -1.55
    bx = px if servidor == "j" else rpx


def dar_ponto(ganhador, motivo):
    global pts_j, pts_r, estado, timer, msg
    if ganhador == "j":
        pts_j += 1
        msg = "PONTO SEU!  " + motivo
    else:
        pts_r += 1
        msg = "PONTO DO ROBÔ!  " + motivo
    estado, timer = "ponto", 1.3


def fim_de_ponto():
    global estado, rod_j, rod_r, msg_rodada
    if pts_j >= PONTOS or pts_r >= PONTOS:
        if pts_j > pts_r:
            rod_j += 1
            msg_rodada = f"RODADA {rodada} VENCIDA!"
        else:
            rod_r += 1
            msg_rodada = f"RODADA {rodada} PERDIDA!"
        estado = "fim" if rodada == 3 else "rodada"
    else:
        iniciar_saque()


def novo_jogo():
    global rodada, pts_j, pts_r, rod_j, rod_r
    rodada, pts_j, pts_r, rod_j, rod_r = 1, 0, 0, 0, 0
    iniciar_saque()


def perde(quem, motivo):
    dar_ponto("r" if quem == "j" else "j", motivo)


# ---------------- Desenho ----------------
def texto(s, fonte, cor, centro, sombra=True):
    img = fonte.render(s, True, cor)
    r = img.get_rect(center=centro)
    if sombra:
        tela.blit(fonte.render(s, True, (0, 0, 0)), r.move(2, 2))
    tela.blit(img, r)


def desenhar_raquete(x, y, z, cor, escala=1.0):
    pts = [proj(x + math.cos(a) * 0.115 * escala, y + math.sin(a) * 0.115 * escala, z)[:2]
           for a in [i * math.tau / 24 for i in range(24)]]
    k = proj(x, y, z)[2]
    cabo = [(x - 0.022, y - 0.1, z), (x + 0.022, y - 0.1, z), (x + 0.022, y - 0.25, z), (x - 0.022, y - 0.25, z)]
    pygame.draw.polygon(tela, (185, 135, 75), P(cabo))
    pygame.draw.polygon(tela, cor, pts)
    pygame.draw.polygon(tela, (25, 25, 25), pts, max(2, int(0.01 * k)))


def desenhar_robo():
    zr = -2.2
    cx = rpx * 0.8
    pygame.draw.polygon(tela, (95, 105, 120), P([(cx - 0.28, CHAO, zr), (cx + 0.28, CHAO, zr), (cx + 0.24, 0.55, zr), (cx - 0.24, 0.55, zr)]))
    pygame.draw.polygon(tela, (70, 80, 95), P([(cx - 0.18, 0.62, zr), (cx + 0.18, 0.62, zr), (cx + 0.18, 0.95, zr), (cx - 0.18, 0.95, zr)]))
    for ex in (-0.07, 0.07):
        ex_, ey_, k = proj(cx + ex, 0.8, zr)
        pygame.draw.circle(tela, (255, 80, 60), (int(ex_), int(ey_)), max(2, int(0.025 * k)))
    a = proj(cx + 0.22, 0.45, zr)
    b = proj(rpx, rpy - 0.05, RZ)
    pygame.draw.line(tela, (95, 105, 120), a[:2], b[:2], max(3, int(0.08 * a[2])))
    desenhar_raquete(rpx, rpy, RZ, (30, 30, 36), 1.0 + anim_r)


def desenhar_mesa():
    # pernas
    for (lx, lz) in [(-0.68, -1.25), (0.68, -1.25), (-0.68, 1.25), (0.68, 1.25)]:
        a, b = proj(lx, -0.06, lz), proj(lx, CHAO, lz)
        pygame.draw.line(tela, (55, 60, 70), a[:2], b[:2], max(3, int(0.07 * a[2])))
    pygame.draw.polygon(tela, (14, 55, 110), P([(-MW, 0, ML), (MW, 0, ML), (MW, -0.06, ML), (-MW, -0.06, ML)]))
    topo = P([(-MW, 0, -ML), (MW, 0, -ML), (MW, 0, ML), (-MW, 0, ML)])
    pygame.draw.polygon(tela, (24, 96, 178), topo)
    pygame.draw.polygon(tela, (245, 245, 245), topo, 3)
    pygame.draw.line(tela, (245, 245, 245), proj(0, 0, -ML)[:2], proj(0, 0, ML)[:2], 2)


def desenhar_rede():
    for i in range(-10, 11):
        x = i * (MW + 0.1) / 10
        pygame.draw.line(tela, (200, 200, 205), proj(x, 0, 0)[:2], proj(x, NET_H, 0)[:2], 1)
    for h in (0.04, 0.09):
        pygame.draw.line(tela, (200, 200, 205), proj(-MW - 0.1, h, 0)[:2], proj(MW + 0.1, h, 0)[:2], 1)
    topo_a, topo_b = proj(-MW - 0.1, NET_H, 0), proj(MW + 0.1, NET_H, 0)
    pygame.draw.line(tela, (255, 255, 255), topo_a[:2], topo_b[:2], max(3, int(0.012 * topo_a[2])))
    for x in (-MW - 0.1, MW + 0.1):
        a, b = proj(x, -0.02, 0), proj(x, NET_H + 0.02, 0)
        pygame.draw.line(tela, (40, 40, 40), a[:2], b[:2], max(3, int(0.015 * a[2])))


def desenhar_bola():
    sx, sy, k = proj(bx, by, bz)
    sobre_mesa = abs(bx) <= MW and abs(bz) <= ML
    shx, shy, shk = proj(bx, 0.0 if sobre_mesa else CHAO, bz)
    rw = max(3, int(R * shk * 1.2))
    pygame.draw.ellipse(tela, (8, 40, 80) if sobre_mesa else (110, 72, 42), (shx - rw, shy - rw * 0.35, rw * 2, rw * 0.7))
    r = max(4, int(R * k))
    pygame.draw.circle(tela, (255, 190, 30), (int(sx), int(sy)), r)
    pygame.draw.circle(tela, (255, 245, 190), (int(sx - r * 0.3), int(sy - r * 0.3)), max(1, r // 3))


def hud():
    x0, y0 = 10, H - 112
    painel = pygame.Surface((270, 102), pygame.SRCALPHA)
    pygame.draw.rect(painel, (10, 15, 25, 170), painel.get_rect(), border_radius=12)
    tela.blit(painel, (x0, y0))
    texto(f"VOCÊ {pts_j}  x  {pts_r} ROBÔ", F1, (255, 255, 255), (x0 + 135, y0 + 20))
    texto(f"RODADA {rodada}/3  •  até {PONTOS} pts", F0, (240, 200, 60), (x0 + 135, y0 + 44))
    texto("Velocidade: " + "▮" * rodada + "▯" * (3 - rodada), F0, (230, 235, 240), (x0 + 135, y0 + 66))
    for i in range(3):  # rodadas vencidas
        cj = (80, 200, 120) if i < rod_j else (70, 80, 95)
        cr = (220, 80, 70) if i < rod_r else (70, 80, 95)
        pygame.draw.circle(tela, cj, (x0 + 20 + i * 18, y0 + 88), 6)
        pygame.draw.circle(tela, cr, (x0 + 250 - i * 18, y0 + 88), 6)


def overlay(titulo, sub):
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    s.fill((0, 0, 0, 150))
    tela.blit(s, (0, 0))
    texto(titulo, F3, (255, 220, 80), (W // 2, H // 2 - 40))
    texto(sub, F1, (255, 255, 255), (W // 2, H // 2 + 30))


# ---------------- Loop principal ----------------
iniciar_saque()
rodando = True
while rodando:
    dt = 1 / 60
    clique = False
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            rodando = False
        elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
            rodando = False
        elif ev.type == pygame.MOUSEBUTTONDOWN:
            clique = True

    # Raquete do jogador: mouse controla lateral (x) e altura (y)
    mx, my = pygame.mouse.get_pos()
    ant_x = px
    px = clamp((mx / W - 0.5) * 1.9, -1.0, 1.0)
    py = clamp(-0.25 + (1 - my / H) * 1.25, -0.2, 0.95)
    mvx = mvx * 0.6 + ((px - ant_x) / dt) * 0.4

    # IA do robô
    if estado == "jogo" and vz < 0:
        t = max(0.0, (RZ - bz) / vz)
        alvo = clamp(bx + vx * t + erro_robo, -1.0, 1.0)
        alvo_y = clamp(by, 0.1, 0.85)
    else:
        alvo, alvo_y = 0.0, 0.35
    passo = VEL_ROBO[rodada] * dt
    rpx += clamp(alvo - rpx, -passo, passo)
    rpy += (alvo_y - rpy) * min(1.0, 10 * dt)
    anim_j = max(0.0, anim_j - dt * 3)
    anim_r = max(0.0, anim_r - dt * 3)

    vel = VEL_RODADA[rodada]

    if estado == "saque":
        if servidor == "j":
            bx, by, bz = px, 0.45, 1.55
            if clique:
                lancar("j", clamp(mvx * 0.3, -0.6, 0.6) + random.uniform(-0.3, 0.3), -0.7, vel * 0.9)
                anim_j = 0.3
        else:
            bx, by, bz = rpx, 0.45, -1.55
            timer -= dt
            if timer <= 0:
                erro_robo = random.uniform(-1, 1) * ERRO_ROBO[rodada]
                lancar("r", random.uniform(-0.55, 0.55), random.uniform(0.4, 0.8), vel * 0.9)
                anim_r = 0.3

    elif estado == "jogo":
        h = dt / 4
        for _ in range(4):
            if estado != "jogo":
                break
            prev_z = bz
            vy -= G * h
            bx += vx * h
            by += vy * h
            bz += vz * h

            # quique na mesa
            if by <= R and vy < 0 and abs(bx) <= MW and abs(bz) <= ML:
                by = R
                vy = -vy * 0.88
                lado = "r" if bz < 0 else "j"
                if lado == hitter:
                    perde(hitter, "Quicou do próprio lado")
                else:
                    quicas += 1
                    if quicas >= 2:
                        dar_ponto(hitter, "Dois quiques")
                continue

            # rede
            if (prev_z > 0 >= bz or prev_z < 0 <= bz) and by < NET_H + R and abs(bx) < MW + 0.15:
                perde(hitter, "Bola na rede")
                continue

            # raquete do jogador
            if vz > 0 and abs(bz - PZ) < 0.25 and math.hypot(bx - px, by - py) < 0.2:
                desvio = bx - px
                tx = clamp(desvio * 4.0 + mvx * 0.3, -0.85, 0.85)
                erro_robo = random.uniform(-1, 1) * ERRO_ROBO[rodada]
                lancar("j", tx, -0.6, vel * (1 + clamp(abs(mvx) * 0.05, 0, 0.2)))
                anim_j = 0.3
                continue

            # raquete do robô
            if vz < 0 and abs(bz - RZ) < 0.25 and math.hypot(bx - rpx, by - rpy) < 0.22:
                tx = random.uniform(-0.62, 0.62)
                if random.random() < FALHA_ROBO[rodada]:
                    tx = random.choice([-1, 1]) * random.uniform(0.9, 1.15)
                lancar("r", tx, random.uniform(0.3, 0.8), vel)
                anim_r = 0.3
                continue

            # chão: fim da jogada
            if by <= CHAO + R:
                if quicas >= 1:
                    dar_ponto(hitter, "Adversário não devolveu")
                else:
                    perde(hitter, "Bola fora")

    elif estado == "ponto":
        timer -= dt
        if timer <= 0:
            fim_de_ponto()

    elif estado == "rodada" and clique:
        rodada += 1
        pts_j = pts_r = 0
        iniciar_saque()

    elif estado == "fim" and clique:
        novo_jogo()

    # ---------- Render ----------
    tela.blit(CENARIO, (0, 0))
    desenhar_robo()
    desenhar_mesa()
    objetos = [(0.0, desenhar_rede), (bz, desenhar_bola),
               (PZ, lambda: desenhar_raquete(px, py, PZ, (200, 50, 40), 1.0 + anim_j))]
    for _, fn in sorted(objetos, key=lambda o: o[0]):
        fn()
    hud()

    if estado == "saque" and servidor == "j":
        texto("CLIQUE para sacar", F1, (255, 255, 255), (W // 2 + 60, H - 40))
    elif estado == "ponto":
        texto(msg, F1, (255, 230, 120), (W // 2 + 60, H - 40))
    elif estado == "rodada":
        overlay(msg_rodada, f"Clique para a rodada {rodada + 1}  (a bola fica mais rápida!)")
    elif estado == "fim":
        res = "VOCÊ VENCEU O JOGO!" if rod_j > rod_r else "O ROBÔ VENCEU O JOGO"
        overlay(res, f"Rodadas: Você {rod_j} x {rod_r} Robô  —  clique para jogar de novo")

    pygame.display.flip()
    relogio.tick(60)

pygame.quit()
sys.exit()
