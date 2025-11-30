import cv2
import easyocr
import numpy as np
import imutils


class DetectorPlaca:
    def __init__(self, gpu=False, min_area=300):
        print("Carregando modelo OCR (uma única vez)...")
        # Carregamos a IA apenas uma vez na inicialização do programa
        self.reader = easyocr.Reader(['pt'], gpu=gpu, quantize=False)
        self.min_area = min_area
        self.cap = None

    def conectar_camera(self):
        """Inicia a conexão com a webcam se não estiver ativa"""
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)
            return True
        return True

    def desconectar_camera(self):
        """Libera a webcam para economizar recursos"""
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

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blur, 30, 200)

        keypoints = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(keypoints)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

        location = None
        for contour in contours:
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
            if len(approx) == 4 and cv2.contourArea(contour) > self.min_area:
                location = approx
                break

        texto_lido = None
        crop = None

        if location is not None:
            cv2.drawContours(frame, [location], -1, (0, 255, 0), 2)

            try:
                mask = np.zeros(gray.shape, np.uint8)
                new_image = cv2.drawContours(mask, [location], 0, 255, -1)
                new_image = cv2.bitwise_and(frame, frame, mask=mask)
                (x, y) = np.where(mask == 255)

                if len(x) > 0 and len(y) > 0:
                    (topx, topy) = (np.min(x), np.min(y))
                    (bottomx, bottomy) = (np.max(x), np.max(y))
                    crop = new_image[topx:bottomx + 1, topy:bottomy + 1]

                    crop_gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                    crop_gray = cv2.resize(crop_gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
                    _, crop_binary = cv2.threshold(crop_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

                    result = self.reader.readtext(crop_binary)

                    for (bbox, text, prob) in result:
                        text_clean = text.replace(" ", "").upper().replace("-", "").replace(".", "")
                        if len(text_clean) >= 7 and prob > 0.4:
                            texto_lido = text_clean
                            cv2.putText(frame, text_clean, (location[0][0][0], location[0][0][1] - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            except Exception as e:
                pass

        return frame, texto_lido, crop