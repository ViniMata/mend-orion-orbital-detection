import cv2
import numpy as np
import math
import time
from collections import defaultdict, deque

# ─────────────────────────────────────────────
#  CONSTANTES
# ─────────────────────────────────────────────
VIDEO_PATH      = "debris_v1.mp4"  # caminho do video (0 = webcam)
BRILHO_MIN      = 60               # pixels mais brilhantes que isso sao debris
AREA_MIN        = 300              # tamanho minimo do objeto (pixels)
AREA_MAX        = 50000            # tamanho maximo do objeto (pixels)
MAX_DEBRIS      = 10               # maximo de debris rastreados ao mesmo tempo
HISTORICO       = 25               # quantos frames guardar na trilha
MAX_DISTANCIA   = 80               # distancia maxima para considerar o mesmo objeto
VELOCIDADE      = 0.75             # velocidade de reproducao (0.75 = 75% da velocidade)

# contadores globais
CONTADOR_ID     = 0                # ID unico para cada debris
objetos         = {}               # dicionario com todos os debris rastreados
desaparecido    = defaultdict(int) # conta frames que o objeto sumiu

# ─────────────────────────────────────────────
#  FUNCAO: calcula risco pelo tamanho do objeto
# ─────────────────────────────────────────────
def calcular_risco(area):
    if area > 15000:
        return "CRITICO", (0, 50, 255),   "GARRA"   # vermelho
    elif area > 6000:
        return "ALTO",    (0, 140, 255),  "GARRA"   # laranja
    elif area > 2000:
        return "MEDIO",   (0, 230, 255),  "LASER"   # amarelo
    else:
        return "BAIXO",   (0, 255, 120),  "LASER"   # verde

# ─────────────────────────────────────────────
#  FUNCAO: detecta objetos brilhantes no frame
#  Ideal para fundo preto (espaco): qualquer
#  coisa mais clara que BRILHO_MIN e detectada
# ─────────────────────────────────────────────
def detectar_debris(frame):
    # converte para escala de cinza
    cinza = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # threshold: pixels acima de BRILHO_MIN viram branco, resto preto
    _, mascara = cv2.threshold(cinza, BRILHO_MIN, 255, cv2.THRESH_BINARY)

    # remove ruido pequeno com operacoes morfologicas
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN,  kernel, iterations=2)
    mascara = cv2.morphologyEx(mascara, cv2.MORPH_CLOSE, kernel, iterations=2)

    # encontra os contornos dos objetos na mascara
    contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    deteccoes = []
    for cnt in contornos:
        area = cv2.contourArea(cnt)

        # filtra pelo tamanho minimo e maximo
        if not (AREA_MIN <= area <= AREA_MAX):
            continue

        # calcula o centro do objeto usando momentos
        M = cv2.moments(cnt)
        if M["m00"] == 0:
            continue
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])

        x, y, w, h = cv2.boundingRect(cnt)
        deteccoes.append({"cx": cx, "cy": cy, "area": area, "bbox": (x, y, w, h)})

    # ordena pelos maiores e limita quantidade
    deteccoes.sort(key=lambda d: d["area"], reverse=True)
    return deteccoes[:MAX_DEBRIS], mascara

# ─────────────────────────────────────────────
#  FUNCAO: rastreia objetos entre frames
#  Cada debris recebe um ID unico e mantem
#  o mesmo ID enquanto estiver visivel
# ─────────────────────────────────────────────
def rastrear(deteccoes):
    global CONTADOR_ID, objetos, desaparecido

    # se nao ha deteccoes, incrementa desaparecidos e remove antigos
    if not deteccoes:
        for oid in list(desaparecido):
            desaparecido[oid] += 1
            if desaparecido[oid] > 20:
                objetos.pop(oid, None)
                desaparecido.pop(oid, None)
        return objetos

    # se nao ha objetos conhecidos, registra todos como novos
    if not objetos:
        for det in deteccoes:
            trilha = deque(maxlen=HISTORICO)
            trilha.append((det["cx"], det["cy"]))
            objetos[CONTADOR_ID] = {**det, "trilha": trilha}
            desaparecido[CONTADOR_ID] = 0
            CONTADOR_ID += 1
        return objetos

    # associa cada deteccao ao objeto mais proximo ja conhecido
    usados_antigos = set()
    usados_novos   = set()

    for idx_a, (oid, obj) in enumerate(list(objetos.items())):
        melhor_dist = float("inf")
        melhor_idx  = -1

        for idx_n, det in enumerate(deteccoes):
            dist = math.hypot(det["cx"] - obj["cx"], det["cy"] - obj["cy"])
            if dist < melhor_dist:
                melhor_dist = dist
                melhor_idx  = idx_n

        # associa se estiver proximo o suficiente e ainda nao usado
        if melhor_dist < MAX_DISTANCIA and melhor_idx not in usados_novos:
            det = deteccoes[melhor_idx]
            objetos[oid]["trilha"].append((det["cx"], det["cy"]))
            objetos[oid].update({"cx": det["cx"], "cy": det["cy"],
                                 "area": det["area"], "bbox": det["bbox"]})
            desaparecido[oid] = 0
            usados_antigos.add(idx_a)
            usados_novos.add(melhor_idx)
        else:
            # objeto nao encontrado nesse frame
            desaparecido[oid] += 1
            if desaparecido[oid] > 20:
                objetos.pop(oid, None)
                desaparecido.pop(oid, None)

    # registra deteccoes novas que nao foram associadas
    for idx_n, det in enumerate(deteccoes):
        if idx_n not in usados_novos:
            trilha = deque(maxlen=HISTORICO)
            trilha.append((det["cx"], det["cy"]))
            objetos[CONTADOR_ID] = {**det, "trilha": trilha}
            desaparecido[CONTADOR_ID] = 0
            CONTADOR_ID += 1

    return objetos

# ─────────────────────────────────────────────
#  FUNCAO: desenha um debris no frame
# ─────────────────────────────────────────────
def desenhar_debris(frame, oid, dados):
    cx, cy       = dados["cx"], dados["cy"]
    area         = dados["area"]
    x, y, w, h   = dados["bbox"]
    trilha        = dados["trilha"]

    risco, cor, acao = calcular_risco(area)

    # desenha trilha de movimento
    pts = list(trilha)
    for i in range(1, len(pts)):
        cv2.line(frame, pts[i-1], pts[i], (255, 150, 0), 1)

    # desenha cantos do bounding box (estilo scanner)
    tam = 10
    for (px, py, dx, dy) in [(x, y, 1, 1), (x+w, y, -1, 1),
                               (x, y+h, 1, -1), (x+w, y+h, -1, -1)]:
        cv2.line(frame, (px, py), (px + dx*tam, py),         cor, 2)
        cv2.line(frame, (px, py), (px,           py + dy*tam), cor, 2)

    # circulo no centro do objeto
    cv2.circle(frame, (cx, cy), 4, cor, -1)

    # etiqueta com ID, risco e acao ORION
    label = f"#{oid:02d} {risco} | {acao}"
    pos_y = y - 8 if y > 20 else y + h + 16
    cv2.putText(frame, label, (x, pos_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, cor, 1, cv2.LINE_AA)

# ─────────────────────────────────────────────
#  FUNCAO: desenha o HUD (interface na tela)
# ─────────────────────────────────────────────
def desenhar_hud(frame, objetos, fps, total):
    h, w = frame.shape[:2]
    n    = len(objetos)

    # barra superior escura
    cv2.rectangle(frame, (0, 0), (w, 50), (5, 8, 18), -1)
    cv2.line(frame, (0, 50), (w, 50), (0, 220, 255), 1)

    # contador de debris em destaque no centro do topo
    cor_contador = (0, 230, 255) if n > 0 else (0, 255, 120)
    cv2.putText(frame, f"DEBRIS DETECTADOS: {n}",
                (w//2 - 145, 33),
                cv2.FONT_HERSHEY_DUPLEX, 0.85, cor_contador, 1, cv2.LINE_AA)

    # titulo a esquerda — MEND (solucao) | ORION (nave)
    cv2.putText(frame, "MEND | ORION DEBRIS DETECTION SYSTEM",
                (14, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 220, 255), 1)

    # fps a direita
    cv2.putText(frame, f"FPS:{fps:.0f}",
                (w - 80, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 120), 1)

    # barra inferior escura
    cv2.rectangle(frame, (0, h-40), (w, h), (5, 8, 18), -1)
    cv2.line(frame, (0, h-40), (w, h-40), (0, 220, 255), 1)

    # contagem por nivel de risco
    contagem = defaultdict(int)
    for d in objetos.values():
        r, _, _ = calcular_risco(d["area"])
        contagem[r] += 1

    info = (f"CRITICO:{contagem['CRITICO']}  ALTO:{contagem['ALTO']}  "
            f"MEDIO:{contagem['MEDIO']}  BAIXO:{contagem['BAIXO']}  |  "
            f"Total sessao: {total}")
    cv2.putText(frame, info, (14, h-14),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

# ─────────────────────────────────────────────
#  INICIALIZAR VIDEO
# ─────────────────────────────────────────────
vs = cv2.VideoCapture(VIDEO_PATH)

# calcula delay para reproducao em 0.75x
fps_video  = vs.get(cv2.CAP_PROP_FPS) or 30
delay_ms   = int((1000 / fps_video) / VELOCIDADE)

total_sessao = 0
fps_display  = 0.0
tempo_ant    = time.time()
ver_mascara  = False

print("=" * 50)
print("  MEND | ORION — Orbital Debris Detection")
print(f"  Video: {VIDEO_PATH}")
print(f"  FPS original: {fps_video:.1f} | Velocidade: {VELOCIDADE}x")
print("  Q = sair | M = mascara | +/- = brilho")
print("=" * 50)

cv2.namedWindow("MEND | ORION Debris Detection", cv2.WINDOW_NORMAL)
cv2.resizeWindow("MEND | ORION Debris Detection", 1280, 720)

# ─────────────────────────────────────────────
#  LOOP PRINCIPAL
# ─────────────────────────────────────────────
while True:
    ret, frame = vs.read()

    # reinicia o video quando terminar
    if not ret:
        vs.set(cv2.CAP_PROP_POS_FRAMES, 0)
        continue

    # 1. detecta objetos brilhantes (debris) no frame
    deteccoes, mascara = detectar_debris(frame)
    total_sessao += len(deteccoes)

    # 2. rastreia e da ID consistente para cada debris
    objetos_ativos = rastrear(deteccoes)

    # 3. desenha cada debris identificado
    for oid, dados in objetos_ativos.items():
        desenhar_debris(frame, oid, dados)

    # 4. calcula FPS de exibicao
    agora       = time.time()
    fps_display = 0.9 * fps_display + 0.1 * (1.0 / max(agora - tempo_ant, 1e-6))
    tempo_ant   = agora

    # 5. desenha HUD com contador e informacoes
    desenhar_hud(frame, objetos_ativos, fps_display, total_sessao)

    # 6. exibe o frame (ou a mascara de debug)
    if ver_mascara:
        mascara_colorida = cv2.cvtColor(mascara, cv2.COLOR_GRAY2BGR)
        display = np.hstack([frame, mascara_colorida])
    else:
        display = frame

    cv2.imshow("MEND | ORION Debris Detection", display)

    # 7. leitura de teclas
    tecla = cv2.waitKey(delay_ms) & 0xFF
    if tecla == ord("q"):
        break
    elif tecla == ord("m"):
        ver_mascara = not ver_mascara
    elif tecla == ord("+") or tecla == ord("="):
        BRILHO_MIN = min(BRILHO_MIN + 5, 250)
        print(f"  Brilho minimo: {BRILHO_MIN}")
    elif tecla == ord("-"):
        BRILHO_MIN = max(BRILHO_MIN - 5, 5)
        print(f"  Brilho minimo: {BRILHO_MIN}")

# limpa recursos
vs.release()
cv2.destroyAllWindows()
print(f"\n  Total de deteccoes na sessao: {total_sessao}")