import cv2
import easyocr
import numpy as np
import imutils


class DetectorPlaca:
    def __init__(self, gpu=False, min_area=300):
        print("Carregando modelo OCR (uma única vez)...")
        # Inicializa o EasyOCR.
        # 'gpu=True' é muito mais rápido (precisa de NVIDIA CUDA).
        # 'quantize=False' mantém precisão alta.
        self.reader = easyocr.Reader(['pt'], gpu=gpu, quantize=False)
        self.min_area = min_area
        self.cap = None

    def conectar_camera(self):
        """Inicia a conexão com a webcam se não estiver ativa"""
        # Verifica se o objeto de captura existe ou se está fechado
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)  # 0 é geralmente a webcam padrão
            return True
        return True

    def desconectar_camera(self):
        """Libera a webcam para economizar recursos"""
        # Importante liberar a câmera para que outros apps possam usá-la
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
        self.cap = None

    def ler_frame(self):
        """Captura um frame se a câmera estiver conectada"""
        if self.cap is None or not self.cap.isOpened():
            return None

        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame

    def processar(self, frame):
        """
        Recebe um frame, tenta achar a placa e ler.
        """
        if frame is None:
            return None, None, None

        # --- ETAPA 1: Pré-processamento visual ---
        # Converte para cinza (reduz a complexidade de 3 canais de cor para 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Blur Gaussian: Suaviza a imagem para remover ruídos que atrapalham a detecção de bordas
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        # Canny: Algoritmo para detectar bordas baseado em gradiente de cor
        edged = cv2.Canny(blur, 30, 200)

        # --- ETAPA 2: Encontrar Contornos ---
        # Encontra as curvas que formam objetos na imagem de bordas
        keypoints = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(keypoints)
        # Ordena os contornos por área (do maior para o menor) e pega os top 10
        # Isso economiza processamento ignorando sujeiras pequenas
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

        location = None
        for contour in contours:
            # Aproxima o contorno para um polígono simples
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * peri, True)

            # Se o polígono tem 4 pontos, assumimos que é um retângulo (provável placa)
            # E se a área for maior que o mínimo definido
            if len(approx) == 4 and cv2.contourArea(contour) > self.min_area:
                location = approx
                break

        texto_lido = None
        crop = None

        # --- ETAPA 3: Extração e Leitura ---
        if location is not None:
            # Desenha o retângulo verde na imagem original
            cv2.drawContours(frame, [location], -1, (0, 255, 0), 2)

            try:
                # Cria uma máscara preta do tamanho da imagem
                mask = np.zeros(gray.shape, np.uint8)
                # Pinta de branco a área onde a placa está na máscara
                new_image = cv2.drawContours(mask, [location], 0, 255, -1)
                # Recorta a imagem original usando a máscara (fundo fica preto)
                new_image = cv2.bitwise_and(frame, frame, mask=mask)

                # Corta o retângulo exato (Crop) removendo as partes pretas inúteis
                (x, y) = np.where(mask == 255)
                if len(x) > 0 and len(y) > 0:
                    (topx, topy) = (np.min(x), np.min(y))
                    (bottomx, bottomy) = (np.max(x), np.max(y))
                    crop = new_image[topx:bottomx + 1, topy:bottomy + 1]

                    # --- ETAPA 4: Tratamento para o OCR (Melhorar a imagem para a IA) ---
                    crop_gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                    # Aumenta a imagem 3x (Upscaling) - Ajuda muito o OCR em placas distantes
                    crop_gray = cv2.resize(crop_gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
                    # Threshold (Otsu): Transforma em preto e branco puro (binário) para destacar letras
                    _, crop_binary = cv2.threshold(crop_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

                    # --- ETAPA 5: Reconhecimento de Texto ---
                    result = self.reader.readtext(crop_binary)

                    for (bbox, text, prob) in result:
                        # Limpeza: Remove espaços, pontos e traços para padronizar
                        text_clean = text.replace(" ", "").upper().replace("-", "").replace(".", "")

                        # Filtro de qualidade: Só aceita se tiver 7 caracteres (padrão Brasil)
                        # e certeza acima de 40%
                        if len(text_clean) >= 7 and prob > 0.4:
                            texto_lido = text_clean
                            # Escreve o texto lido na tela acima do retângulo
                            cv2.putText(frame, text_clean, (location[0][0][0], location[0][0][1] - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            except Exception as e:
                # O try/except evita que o programa crashe se o crop falhar
                pass

        return frame, texto_lido, crop