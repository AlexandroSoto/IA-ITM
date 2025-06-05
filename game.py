import pygame
import random
import csv
import os
import pandas as pd
from modelos import entrenar_modelo

# Inicializar Pygame
pygame.init()

# Dimensiones
w, h = 800, 400
pantalla = pygame.display.set_mode((w, h))
pygame.display.set_caption("Juego: Dos Naves y Esquivar")

# Colores
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)

# Jugador
jugador = pygame.Rect(50, h - 100, 32, 48)
jugador_pos_inicial = jugador.x
jugador_retroceso = False
vel_retorno = 1

# Naves y balas
nave_der = pygame.Rect(w - 100, h - 100, 64, 64)
bala_h = pygame.Rect(w - 50, h - 90, 16, 16)

nave_arriba = pygame.Rect(50, 0, 64, 64)
bala_v = pygame.Rect(nave_arriba.centerx - 8, nave_arriba.bottom, 16, 16)

# Cargar imágenes
try:
    jugador_frames = [pygame.image.load(f'assets/sprites/mono_frame_{i}.png') for i in range(1, 5)]
except:
    jugador_frames = [pygame.Surface((32, 48)) for _ in range(4)]
    for frame in jugador_frames:
        frame.fill((255, 0, 0))

bala_img = pygame.image.load('assets/sprites/purple_ball.png')
fondo_img = pygame.transform.scale(pygame.image.load('assets/game/fondo2.png'), (w, h))
nave_img = pygame.image.load('assets/game/ufo.png')

# Estados
current_frame = 0
frame_count = 0
frame_speed = 10
salto = False
salto_altura = 15
gravedad = 1
en_suelo = True
bala_h_disparada = False
bala_v_disparada = False
pausa = False
modo_auto = False
menu_activo = True
modelo_actual = None
fuente = pygame.font.SysFont('Arial', 24)
fondo_x1 = 0
fondo_x2 = w

archivo_horizontal = 'datos_bala_horizontal.csv'
archivo_vertical = 'datos_bala_vertical.csv'

if not os.path.exists(archivo_horizontal):
    with open(archivo_horizontal, 'w', newline='') as f:
        csv.writer(f).writerow(['velocidad_bala_h', 'distancia_h', 'accion_salto'])

if not os.path.exists(archivo_vertical):
    with open(archivo_vertical, 'w', newline='') as f:
        csv.writer(f).writerow(['velocidad_bala_v', 'distancia_v', 'accion_retroceso'])

def reiniciar_balas():
    global bala_h, bala_v, bala_h_disparada, bala_v_disparada
    bala_h.x = w - 50
    bala_h.y = h - 90
    bala_v.x = nave_arriba.centerx - 8
    bala_v.y = nave_arriba.bottom
    bala_h_disparada = False
    bala_v_disparada = False

def disparar_balas():
    global bala_h_disparada, bala_v_disparada, velocidad_bala_h, velocidad_bala_v
    if not bala_h_disparada:
        velocidad_bala_h = random.randint(-8, -4)
        bala_h.x = w - 50
        bala_h.y = h - 90
        bala_h_disparada = True
    if not bala_v_disparada:
        velocidad_bala_v = random.randint(2, 6)
        bala_v.x = nave_arriba.centerx - 8
        bala_v.y = nave_arriba.bottom
        bala_v_disparada = True

def guardar_datos(es_horizontal, velocidad, distancia, accion):
    archivo = archivo_horizontal if es_horizontal else archivo_vertical
    with open(archivo, 'a', newline='') as f:
        csv.writer(f).writerow([velocidad, distancia, accion])

def resetear_balas():
    global bala_h_disparada, bala_v_disparada

    if bala_h_disparada:
        distancia = abs(jugador.x - bala_h.x)
        accion = 1 if salto else 0
        guardar_datos(True, velocidad_bala_h, distancia, accion)
        if bala_h.x < 0:
            bala_h_disparada = False

    if bala_v_disparada:
        distancia = abs(jugador.y - bala_v.y)
        accion = 1 if jugador_retroceso else 0
        guardar_datos(False, velocidad_bala_v, distancia, accion)
        if bala_v.y > h:
            bala_v_disparada = False

def manejar_salto():
    global salto, salto_altura, en_suelo
    if salto:
        jugador.y -= salto_altura
        salto_altura -= gravedad
        if jugador.y >= h - 100:
            jugador.y = h - 100
            salto = False
            salto_altura = 15
            en_suelo = True

def manejar_retorno():
    global jugador_retroceso
    if jugador.x < jugador_pos_inicial:
        jugador.x += vel_retorno
        if jugador.x >= jugador_pos_inicial:
            jugador.x = jugador_pos_inicial
            jugador_retroceso = False

def mostrar_menu():
    global menu_activo, modo_auto, modelo_actual
    reiniciar_balas()
    menu_activo = True
    pantalla.fill(NEGRO)
    texto = fuente.render("Presiona 'A' Auto, 'M' Manual, 'Q' Salir", True, BLANCO)
    pantalla.blit(texto, (w // 4, h // 2))
    pygame.display.flip()
    while menu_activo:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit(); exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_a:
                    modo_auto = True
                    elegir_modelo()
                    menu_activo = False
                elif evento.key == pygame.K_m:
                    modo_auto = False
                    menu_activo = False
                elif evento.key == pygame.K_q:
                    pygame.quit(); exit()

def elegir_modelo():
    global modelo_actual
    pantalla.fill(NEGRO)
    texto = fuente.render("Modelo: '1' Árbol, '2' KNN, '3' Red Neuronal", True, BLANCO)
    pantalla.blit(texto, (w // 5, h // 2))
    pygame.display.flip()
    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit(); exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    tipo = 'arbol' if evento.key == pygame.K_1 else 'knn' if evento.key == pygame.K_2 else 'red'
                    data_h = archivo_horizontal
                    data_v = archivo_vertical
                    modelo_actual = (
                        entrenar_modelo(data_h, tipo),
                        entrenar_modelo(data_v, tipo)
                    )
                    return

def update():
    global current_frame, frame_count, menu_activo
    pantalla.blit(fondo_img, (fondo_x1, 0))
    pantalla.blit(fondo_img, (fondo_x2, 0))

    frame_count += 1
    if frame_count >= frame_speed:
        current_frame = (current_frame + 1) % len(jugador_frames)
        frame_count = 0
    pantalla.blit(jugador_frames[current_frame], (jugador.x, jugador.y))

    pantalla.blit(nave_img, (nave_der.x, nave_der.y))
    pantalla.blit(nave_img, (nave_arriba.x, nave_arriba.y))

    if bala_h_disparada:
        bala_h.x += velocidad_bala_h
    if bala_v_disparada:
        bala_v.y += velocidad_bala_v

    pantalla.blit(bala_img, (bala_h.x, bala_h.y))
    pantalla.blit(bala_img, (bala_v.x, bala_v.y))

    if jugador.colliderect(bala_h):
        guardar_datos(True, velocidad_bala_h, abs(jugador.x - bala_h.x), 1 if salto else 0)
        mostrar_menu()
    elif jugador.colliderect(bala_v):
        guardar_datos(False, velocidad_bala_v, abs(jugador.y - bala_v.y), 1 if jugador_retroceso else 0)
        mostrar_menu()

    resetear_balas()

def main():
    global salto, en_suelo, jugador_retroceso
    reloj = pygame.time.Clock()
    mostrar_menu()
    correr = True

    while correr:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                correr = False
            if evento.type == pygame.KEYDOWN:
                if not modo_auto:
                    if evento.key == pygame.K_SPACE and en_suelo:
                        salto = True; en_suelo = False
                    if evento.key == pygame.K_LEFT:
                        jugador.x -= 60
                        jugador.x = max(0, jugador.x)
                        jugador_retroceso = True
                if evento.key == pygame.K_q:
                    pygame.quit(); exit()

        if not pausa:
            if not modo_auto:
                if salto: manejar_salto()
                if jugador_retroceso: manejar_retorno()
            else:
                if bala_h_disparada:
                    pred = modelo_actual[0].predict(pd.DataFrame([[velocidad_bala_h, abs(jugador.x - bala_h.x)]],
                                                                  columns=["velocidad_bala_h", "distancia_h"]))[0]
                    if pred == 1 and en_suelo:
                        salto = True
                        en_suelo = False

                if bala_v_disparada:
                    pred = modelo_actual[1].predict(pd.DataFrame([[velocidad_bala_v, abs(jugador.y - bala_v.y)]],
                                                                  columns=["velocidad_bala_v", "distancia_v"]))[0]
                    if pred == 1 and not jugador_retroceso and jugador.x > 0:
                        jugador.x -= 60
                        jugador.x = max(0, jugador.x)
                        jugador_retroceso = True

                if salto: manejar_salto()
                if jugador_retroceso: manejar_retorno()

            if not bala_h_disparada or not bala_v_disparada:
                disparar_balas()

            update()

        pygame.display.flip()
        reloj.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()
