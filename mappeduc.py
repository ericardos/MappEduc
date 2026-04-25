# MappEduc - Ferramenta de Mapeamento de Projeção Educacional
# Copyright (C) 2026 Edson Ricardo dos Santos da Silva
#
# Licença: GNU General Public License v3.0
#
# Autor: Edson Ricardo dos Santos da Silva - Professor de Artes Visuais

import sys
import os
import json
import cv2
import numpy as np
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *
from collections import deque
import time
from datetime import datetime

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================
DEFAULT_GRID_COLS = 1
DEFAULT_GRID_ROWS = 1
SUBDIV = 4
MAX_TEXTURE = 512
VIDEO_UPDATE_MS = 50

PROGRAM_NAME = "MappEduc"
PROGRAM_VERSION = "2.6"
PROGRAM_AUTHOR = "Edson Ricardo dos Santos da Silva"
PROGRAM_AUTHOR_TITLE = "Professor de Artes Visuais"
PROGRAM_LICENSE = "GNU General Public License v3.0"
PROGRAM_COPYRIGHT = f"Copyright (C) 2026 {PROGRAM_AUTHOR}"

ICON_PATH = os.path.join(os.path.dirname(__file__), "icone.png")

# =============================================================================
# LINHA HORIZONTAL
# =============================================================================
class QHLine(QtWidgets.QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)


# =============================================================================
# DIÁLOGO DE BOAS-VINDAS
# =============================================================================
class WelcomeDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Bem-vindo ao {PROGRAM_NAME}")
        self.setMinimumWidth(550)
        self.setMinimumHeight(450)
        
        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QtGui.QIcon(ICON_PATH))
        
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout()
        
        if os.path.exists(ICON_PATH):
            icon_label = QtWidgets.QLabel()
            icon_pixmap = QtGui.QPixmap(ICON_PATH).scaled(80, 80, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
            icon_label.setPixmap(icon_pixmap)
            icon_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(icon_label)
        
        title = QtWidgets.QLabel(f"🎓 {PROGRAM_NAME}")
        title_font = QtGui.QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QtWidgets.QLabel("Ferramenta de Mapeamento de Projeção Educacional")
        subtitle_font = QtGui.QFont()
        subtitle_font.setPointSize(11)
        subtitle.setFont(subtitle_font)
        subtitle.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        layout.addSpacing(5)
        
        version_label = QtWidgets.QLabel(f"Versão {PROGRAM_VERSION}")
        version_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)
        
        layout.addSpacing(10)
        layout.addWidget(QHLine())
        
        author_group = QtWidgets.QGroupBox("👨‍🏫 Autor")
        author_layout = QtWidgets.QVBoxLayout()
        author_layout.addWidget(QtWidgets.QLabel(f"<b>{PROGRAM_AUTHOR}</b>"))
        author_layout.addWidget(QtWidgets.QLabel(PROGRAM_AUTHOR_TITLE))
        author_group.setLayout(author_layout)
        layout.addWidget(author_group)
        
        license_group = QtWidgets.QGroupBox("📜 Licença")
        license_layout = QtWidgets.QVBoxLayout()
        license_layout.addWidget(QtWidgets.QLabel(f"<b>{PROGRAM_LICENSE}</b>"))
        license_layout.addWidget(QtWidgets.QLabel(PROGRAM_COPYRIGHT))
        license_text = QtWidgets.QLabel(
            "Este programa é software livre sob os termos da GPL v3."
        )
        license_text.setWordWrap(True)
        license_layout.addWidget(license_text)
        license_group.setLayout(license_layout)
        layout.addWidget(license_group)
        
        layout.addSpacing(10)
        
        self.dont_show_checkbox = QtWidgets.QCheckBox("Não mostrar esta mensagem novamente")
        layout.addWidget(self.dont_show_checkbox)
        
        button_layout = QtWidgets.QHBoxLayout()
        btn_continue = QtWidgets.QPushButton("Continuar")
        btn_continue.setDefault(True)
        btn_continue.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(btn_continue)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def should_not_show_again(self):
        return self.dont_show_checkbox.isChecked()


# =============================================================================
# GERENCIADOR DE UNDO/REDO
# =============================================================================
class UndoManager:
    def __init__(self, max_steps=10):
        self.undo_stack = deque(maxlen=max_steps)
        self.redo_stack = deque(maxlen=max_steps)
    
    def save_state(self, layers):
        state = []
        for layer in layers:
            if layer.frame is not None:
                state.append({
                    'points': layer.points.copy(),
                    'grid_cols': layer.grid_cols,
                    'grid_rows': layer.grid_rows,
                    'opacity': layer.opacity,
                    'rotation': layer.rotation
                })
        if state:
            self.undo_stack.append(state)
            self.redo_stack.clear()
    
    def undo(self, layers):
        if len(self.undo_stack) < 2:
            return False
        current = self.undo_stack.pop()
        self.redo_stack.append(current)
        prev = self.undo_stack[-1]
        self._apply_state(layers, prev)
        return True
    
    def redo(self, layers):
        if not self.redo_stack:
            return False
        state = self.redo_stack.pop()
        self.undo_stack.append(state)
        self._apply_state(layers, state)
        return True
    
    def _apply_state(self, layers, state):
        for layer, s in zip(layers, state):
            if layer.frame is not None:
                layer.points = s['points'].copy()
                layer.grid_cols = s['grid_cols']
                layer.grid_rows = s['grid_rows']
                layer.opacity = s['opacity']
                layer.rotation = s.get('rotation', 0.0)


# =============================================================================
# CAMADA (LAYER)
# =============================================================================
class Layer:
    def __init__(self, path):
        self.path = path
        self.cap = None
        self.original_frame = None
        self.frame = None
        self.texture_edit = None
        self.texture_proj = None
        self.tex_size = None
        self.is_video = False
        self.visible = True
        self.locked = False
        self.opacity = 1.0
        self.fit_mode = True
        self.rotation = 0.0
        self._last_update = 0
        self._frame_counter = 0
        self._needs_texture_update = True
        self.has_alpha = False
        
        self.grid_cols = DEFAULT_GRID_COLS
        self.grid_rows = DEFAULT_GRID_ROWS
        
        # Chroma Key
        self.chroma_enabled = False
        self.chroma_color = (0, 0, 0)
        self.chroma_tolerance = 30

        if not os.path.exists(path):
            raise Exception(f"Arquivo não encontrado: {path}")

        ext = path.lower()
        if ext.endswith((".mp4", ".avi", ".mov", ".mkv", ".webm")):
            self._load_video(path)
        elif ext.endswith((".jpg", ".jpeg", ".png", ".bmp")):
            self._load_image(path)
        else:
            raise Exception(f"Formato não suportado")

        if self.original_frame is None:
            raise Exception(f"Não foi possível carregar o arquivo")

        self._process_frame()
        h, w = self.frame.shape[:2]
        self.points = self.create_grid(w, h, self.grid_cols, self.grid_rows)

    def _load_video(self, path):
        self.is_video = True
        self.cap = cv2.VideoCapture(path)
        if not self.cap.isOpened():
            raise Exception(f"Vídeo não suportado")
        ret, frame = self.cap.read()
        if ret and frame is not None:
            self.original_frame = frame
            self.has_alpha = False
        else:
            self.cap.release()
            raise Exception("Não foi possível ler o vídeo")

    def _load_image(self, path):
        self.is_video = False
        self.original_frame = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if self.original_frame is None:
            self.original_frame = cv2.imread(path, cv2.IMREAD_COLOR)
            if self.original_frame is None:
                raise Exception("Imagem não suportada")
            self.has_alpha = False
        else:
            self.has_alpha = (len(self.original_frame.shape) == 3 and self.original_frame.shape[2] == 4)

    def _apply_chroma_key(self, frame):
        if not self.chroma_enabled:
            return frame.copy()
        
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        elif len(frame.shape) == 3 and frame.shape[2] == 4:
            frame_rgb = cv2.cvtColor(frame[:, :, :3], cv2.COLOR_BGR2RGB)
        else:
            return frame.copy()
        
        color = np.array(self.chroma_color)
        tolerance = self.chroma_tolerance
        
        lower = np.clip(color - tolerance, 0, 255)
        upper = np.clip(color + tolerance, 0, 255)
        
        mask = cv2.inRange(frame_rgb, lower, upper)
        
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            result = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
        else:
            result = frame.copy()
            if result.shape[2] == 3:
                result = cv2.cvtColor(result, cv2.COLOR_BGR2BGRA)
        
        result[:, :, 3] = cv2.bitwise_not(mask)
        self.has_alpha = True
        
        return result

    def _process_frame(self):
        if self.original_frame is None:
            return
        
        processed = self._apply_chroma_key(self.original_frame)
        
        h, w = processed.shape[:2]
        if max(w, h) > MAX_TEXTURE:
            scale = MAX_TEXTURE / max(w, h)
            interpolation = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
            processed = cv2.resize(processed, (int(w*scale), int(h*scale)), 
                                   interpolation=interpolation)
        
        self.frame = processed

    def set_chroma_key(self, enabled, color=None, tolerance=None):
        self.chroma_enabled = enabled
        if color is not None:
            self.chroma_color = color
        if tolerance is not None:
            self.chroma_tolerance = tolerance
        self._process_frame()
        self._needs_texture_update = True

    def create_grid(self, w, h, cols, rows):
        if self.fit_mode:
            if w > h:
                scale_x = 1.0
                scale_y = h / w
            else:
                scale_x = w / h
                scale_y = 1.0
        else:
            scale_x = 1.0
            scale_y = 1.0
        
        pts = np.zeros((rows + 1, cols + 1, 2), dtype=np.float32)
        for y in range(rows + 1):
            py = y / rows if rows > 0 else 0
            ny = (py * 2 - 1) * scale_y
            for x in range(cols + 1):
                px = x / cols if cols > 0 else 0
                nx = (px * 2 - 1) * scale_x
                pts[y, x] = [nx, -ny]
        return pts

    def rebuild_grid(self):
        if self.frame is not None:
            h, w = self.frame.shape[:2]
            self.points = self.create_grid(w, h, self.grid_cols, self.grid_rows)
            self.rotation = 0.0

    def set_grid(self, cols, rows):
        self.grid_cols = cols
        self.grid_rows = rows
        self.rebuild_grid()

    def update(self):
        if not self.is_video or not self.visible:
            return
        
        current_time = time.time()
        if current_time - self._last_update < VIDEO_UPDATE_MS / 1000.0:
            return
        
        self._last_update = current_time
        
        if self.cap is None or not self.cap.isOpened():
            return
        
        self._frame_counter += 1
        if self._frame_counter % 2 != 0:
            self.cap.grab()
            return
        
        ret, frame = self.cap.read()
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()
            
        if ret and frame is not None:
            self.original_frame = frame
            self._process_frame()
            self._needs_texture_update = True
    
    def cleanup(self):
        if self.cap:
            self.cap.release()
            self.cap = None
        self.original_frame = None
        self.frame = None


# =============================================================================
# VISUALIZAÇÃO OPENGL
# =============================================================================
class GLView(QOpenGLWidget):
    def __init__(self, main_window=None, view_type="edit"):
        super().__init__()
        self.main_window = main_window
        self.view_type = view_type
        self.layers = []
        self.active = 0
        self.selected = None
        self.is_edit_view = (view_type == "edit")
        self.show_grid_in_proj = False  # NOVO: Flag para mostrar grid na projeção
        self.undo_manager = UndoManager()
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self._initialized = False
        
        self.zoom_level = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        
        self.is_panning = False
        self.is_dragging_point = False
        self.last_mouse_pos = None

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_TEXTURE_2D)
        glDisable(GL_DEPTH_TEST)
        self._initialized = True

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        self._update_projection()

    def _update_projection(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        left = -1.0 / self.zoom_level - self.pan_x
        right = 1.0 / self.zoom_level - self.pan_x
        bottom = -1.0 / self.zoom_level - self.pan_y
        top = 1.0 / self.zoom_level - self.pan_y
        glOrtho(left, right, bottom, top, -1, 1)
        glMatrixMode(GL_MODELVIEW)

    def update_texture(self, layer):
        frame = layer.frame
        if frame is None:
            return None
            
        h, w = frame.shape[:2]
        
        if len(frame.shape) == 2:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
            has_alpha = False
        elif frame.shape[2] == 3:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            has_alpha = False
        elif frame.shape[2] == 4:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGBA)
            has_alpha = True
        else:
            return None
        
        tex_attr = 'texture_edit' if self.view_type == "edit" else 'texture_proj'
        texture = getattr(layer, tex_attr)
        
        if has_alpha:
            internal = GL_RGBA
            fmt = GL_RGBA
        else:
            internal = GL_RGB
            fmt = GL_RGB
        
        if texture is None:
            texture = glGenTextures(1)
            setattr(layer, tex_attr, texture)
            layer.tex_size = (w, h)
            glBindTexture(GL_TEXTURE_2D, texture)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            glTexImage2D(GL_TEXTURE_2D, 0, internal, w, h, 0, fmt, GL_UNSIGNED_BYTE, frame_rgb)
        else:
            glBindTexture(GL_TEXTURE_2D, texture)
            if layer._needs_texture_update or getattr(layer, 'tex_size', (0, 0)) != (w, h):
                setattr(layer, 'tex_size', (w, h))
                glTexImage2D(GL_TEXTURE_2D, 0, internal, w, h, 0, fmt, GL_UNSIGNED_BYTE, frame_rgb)
                layer._needs_texture_update = False
            elif self.view_type == "proj":
                glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, w, h, fmt, GL_UNSIGNED_BYTE, frame_rgb)
        
        return texture

    def paintGL(self):
        if not self._initialized:
            return
        
        self._update_projection()
        
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_TEXTURE_2D)
        
        # Renderizar na ordem inversa: última da lista = fundo, primeira = frente
        for layer in reversed(self.layers):
            if not layer.visible or layer.frame is None:
                continue
            
            if layer.is_video:
                layer.update()
            
            texture = self.update_texture(layer)
            if texture is None:
                continue
            
            glBindTexture(GL_TEXTURE_2D, texture)
            glColor4f(1.0, 1.0, 1.0, layer.opacity)
            
            p = layer.points
            cols = layer.grid_cols
            rows = layer.grid_rows
            
            for i in range(rows):
                for j in range(cols):
                    p00, p10 = p[i][j], p[i][j+1]
                    p01, p11 = p[i+1][j], p[i+1][j+1]
                    
                    glBegin(GL_TRIANGLE_STRIP)
                    step = 1.0/SUBDIV
                    for k in range(SUBDIV+1):
                        u = k * step
                        u1 = 1-u
                        tx = (j+u)/cols
                        
                        x0 = u1*p00[0] + u*p10[0]
                        y0 = u1*p00[1] + u*p10[1]
                        x1 = u1*p01[0] + u*p11[0]
                        y1 = u1*p01[1] + u*p11[1]
                        
                        glTexCoord2f(tx, i/rows)
                        glVertex2f(x0, y0)
                        glTexCoord2f(tx, (i+1)/rows)
                        glVertex2f(x1, y1)
                    glEnd()
        
        # NOVO: Desenhar grid na projeção (apenas linhas, sem pontos)
        if self.view_type == "proj" and self.show_grid_in_proj and self.layers:
            layer = self.layers[self.active]
            if layer.visible:
                self._draw_proj_grid(layer)
        
        if self.is_edit_view:
            self._draw_overlay()
            self._draw_info()
        
        glFlush()

    def _draw_proj_grid(self, layer):
        """Desenha apenas as linhas do grid na janela de projeção (sem pontos)"""
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        cols = layer.grid_cols
        rows = layer.grid_rows
        
        # Linhas ciano bem visíveis e mais grossas
        glColor4f(0.0, 1.0, 1.0, 0.9)  # Ciano brilhante
        glLineWidth(3.0)  # Linhas mais grossas para projeção
        
        glBegin(GL_LINES)
        # Linhas horizontais
        for i in range(rows + 1):
            for j in range(cols):
                glVertex2f(*layer.points[i][j])
                glVertex2f(*layer.points[i][j+1])
        # Linhas verticais
        for j in range(cols + 1):
            for i in range(rows):
                glVertex2f(*layer.points[i][j])
                glVertex2f(*layer.points[i+1][j])
        glEnd()
        
        glEnable(GL_TEXTURE_2D)

    def _draw_info(self):
        painter = QtGui.QPainter(self)
        painter.setPen(QtGui.QColor(255, 255, 255, 180))
        painter.setFont(QtGui.QFont("Arial", 10))
        
        y_pos = 25
        
        if self.zoom_level != 1.0:
            painter.drawText(10, y_pos, f"🔍 Zoom: {self.zoom_level:.1f}x")
            y_pos += 20
        
        if self.pan_x != 0 or self.pan_y != 0:
            painter.drawText(10, y_pos, f"🖐️ Pan: ({self.pan_x:.2f}, {self.pan_y:.2f})")
            y_pos += 20
        
        if self.selected is not None:
            painter.setPen(QtGui.QColor(255, 255, 0, 200))
            painter.drawText(10, y_pos, f"📍 Ponto selecionado: {self.selected}")
            y_pos += 20
        
        if self.layers:
            layer = self.layers[self.active]
            if layer.visible:
                painter.setPen(QtGui.QColor(200, 200, 200, 180))
                painter.drawText(10, y_pos, f"💧 Opacidade: {int(layer.opacity * 100)}%")
                if layer.chroma_enabled:
                    y_pos += 20
                    painter.drawText(10, y_pos, f"🎭 Chroma Key ativo")
                if layer.rotation != 0:
                    y_pos += 20
                    painter.drawText(10, y_pos, f"🔄 Rotação: {layer.rotation:.0f}°")
        
        painter.end()

    def _draw_overlay(self):
        if not self.layers:
            return
        
        layer = self.layers[self.active]
        if not layer.visible:
            return
        
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glLineWidth(2.0)
        
        cols = layer.grid_cols
        rows = layer.grid_rows
        
        for i in range(rows + 1):
            for j in range(cols + 1):
                x, y = layer.points[i][j]
                
                if layer.locked:
                    glColor3f(1.0, 0.0, 0.0)
                elif i == 0 or i == rows or j == 0 or j == cols:
                    glColor3f(1.0, 0.5, 0.0)
                else:
                    glColor3f(0.0, 0.8, 0.0)
                
                if self.selected == (i, j):
                    glColor3f(1.0, 1.0, 0.0)
                    self._draw_point(x, y, 0.035)
                else:
                    self._draw_point(x, y, 0.02)
        
        glColor4f(0.0, 0.8, 1.0, 0.8)
        glBegin(GL_LINES)
        for i in range(rows + 1):
            for j in range(cols):
                glVertex2f(*layer.points[i][j])
                glVertex2f(*layer.points[i][j+1])
        for j in range(cols + 1):
            for i in range(rows):
                glVertex2f(*layer.points[i][j])
                glVertex2f(*layer.points[i+1][j])
        glEnd()
        
        glEnable(GL_TEXTURE_2D)

    def _draw_point(self, x, y, size):
        glBegin(GL_QUADS)
        glVertex2f(x-size, y-size)
        glVertex2f(x+size, y-size)
        glVertex2f(x+size, y+size)
        glVertex2f(x-size, y+size)
        glEnd()

    def _screen_to_world(self, pos):
        mx = (pos.x() / self.width()) * 2 - 1
        my = -((pos.y() / self.height()) * 2 - 1)
        wx = mx / self.zoom_level + self.pan_x
        wy = my / self.zoom_level + self.pan_y
        return wx, wy

    def _find_point_at(self, wx, wy):
        if not self.layers:
            return None
        
        layer = self.layers[self.active]
        if layer.locked or not layer.visible:
            return None
        
        min_dist = 0.07 / self.zoom_level
        closest = None
        closest_dist = float('inf')
        
        for i in range(layer.points.shape[0]):
            for j in range(layer.points.shape[1]):
                px, py = layer.points[i][j]
                dist = ((px - wx) ** 2 + (py - wy) ** 2) ** 0.5
                if dist < min_dist and dist < closest_dist:
                    closest_dist = dist
                    closest = (i, j)
        
        return closest

    def wheelEvent(self, e):
        if not self.is_edit_view:
            return
        
        wx, wy = self._screen_to_world(e.position())
        
        delta = e.angleDelta().y()
        if delta > 0:
            self.zoom_level *= 1.1
        else:
            self.zoom_level /= 1.1
        
        self.zoom_level = max(0.1, min(10.0, self.zoom_level))
        
        mx = (e.position().x() / self.width()) * 2 - 1
        my = -((e.position().y() / self.height()) * 2 - 1)
        self.pan_x = wx - mx / self.zoom_level
        self.pan_y = wy - my / self.zoom_level
        
        self.update()
        if self.main_window:
            self.main_window.view_proj.update()
            self.main_window.statusBar().showMessage(f"🔍 Zoom: {self.zoom_level:.1f}x", 1000)

    def mousePressEvent(self, e):
        if not self.is_edit_view:
            return
        
        if e.button() == QtCore.Qt.MouseButton.MiddleButton or \
           e.button() == QtCore.Qt.MouseButton.RightButton:
            self.is_panning = True
            self.last_mouse_pos = e.position()
            self.setCursor(QtCore.Qt.CursorShape.ClosedHandCursor)
            return
        
        if e.button() == QtCore.Qt.MouseButton.LeftButton:
            if not self.layers:
                return
            
            layer = self.layers[self.active]
            if not layer.visible:
                return
            
            wx, wy = self._screen_to_world(e.position())
            point = self._find_point_at(wx, wy)
            
            if point is not None and not layer.locked:
                self.is_dragging_point = True
                self.selected = point
                self.undo_manager.save_state(self.layers)
                self.update()
                if self.main_window:
                    self.main_window.view_proj.update()
                    self.main_window.statusBar().showMessage(f"📍 Ponto {point} selecionado", 1000)
            else:
                self.is_panning = True
                self.last_mouse_pos = e.position()
                self.setCursor(QtCore.Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, e):
        if self.is_panning and self.last_mouse_pos is not None:
            delta = e.position() - self.last_mouse_pos
            self.pan_x -= delta.x() / (self.width() * 0.5) / self.zoom_level
            self.pan_y += delta.y() / (self.height() * 0.5) / self.zoom_level
            self.last_mouse_pos = e.position()
            self.update()
            if self.main_window:
                self.main_window.view_proj.update()
            return
        
        if self.is_dragging_point and self.selected is not None:
            if not self.layers:
                return
            
            layer = self.layers[self.active]
            if layer.locked or not layer.visible:
                return
            
            wx, wy = self._screen_to_world(e.position())
            i, j = self.selected
            layer.points[i][j] = [wx, wy]
            self.update()
            if self.main_window:
                self.main_window.view_proj.update()

    def mouseReleaseEvent(self, e):
        if self.is_panning:
            self.is_panning = False
            self.last_mouse_pos = None
            self.setCursor(QtCore.Qt.CursorShape.ArrowCursor)
            return
        
        if self.is_dragging_point:
            self.is_dragging_point = False

    def mouseDoubleClickEvent(self, e):
        if e.button() == QtCore.Qt.MouseButton.LeftButton:
            self._reset_view()
    
    def _reset_view(self):
        self.zoom_level = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.update()
        if self.main_window:
            self.main_window.view_proj.update()
            self.main_window.statusBar().showMessage("🔄 Visualização resetada", 1500)

    def _scale_layer(self, factor):
        if not self.layers:
            return
        
        layer = self.layers[self.active]
        if layer.locked or not layer.visible:
            return
        
        self.undo_manager.save_state(self.layers)
        
        center_x = np.mean(layer.points[:, :, 0])
        center_y = np.mean(layer.points[:, :, 1])
        
        for i in range(layer.points.shape[0]):
            for j in range(layer.points.shape[1]):
                layer.points[i, j, 0] = center_x + (layer.points[i, j, 0] - center_x) * factor
                layer.points[i, j, 1] = center_y + (layer.points[i, j, 1] - center_y) * factor
        
        self.update()
        if self.main_window:
            self.main_window.view_proj.update()
            scale_percent = int(factor * 100)
            self.main_window.statusBar().showMessage(f"📏 Escala: {scale_percent}%", 1500)
    
    def _reset_layer_scale(self):
        if not self.layers:
            return
        
        layer = self.layers[self.active]
        if layer.locked or not layer.visible:
            return
        
        self.undo_manager.save_state(self.layers)
        layer.rebuild_grid()
        self.update()
        if self.main_window:
            self.main_window.view_proj.update()
            self.main_window.statusBar().showMessage("📏 Escala resetada", 1500)

    def _rotate_layer(self, degrees):
        if not self.layers:
            return
        
        layer = self.layers[self.active]
        if layer.locked or not layer.visible:
            return
        
        self.undo_manager.save_state(self.layers)
        
        layer.rotation += degrees
        layer.rotation = layer.rotation % 360
        
        center_x = np.mean(layer.points[:, :, 0])
        center_y = np.mean(layer.points[:, :, 1])
        
        rad = np.radians(degrees)
        cos_a = np.cos(rad)
        sin_a = np.sin(rad)
        
        for i in range(layer.points.shape[0]):
            for j in range(layer.points.shape[1]):
                dx = layer.points[i, j, 0] - center_x
                dy = layer.points[i, j, 1] - center_y
                layer.points[i, j, 0] = center_x + dx * cos_a - dy * sin_a
                layer.points[i, j, 1] = center_y + dx * sin_a + dy * cos_a
        
        self.update()
        if self.main_window:
            self.main_window.view_proj.update()
            self.main_window.statusBar().showMessage(f"🔄 Rotação: {layer.rotation:.0f}°", 1500)

    def _reset_rotation(self):
        if not self.layers:
            return
        
        layer = self.layers[self.active]
        if layer.locked or not layer.visible:
            return
        
        if layer.rotation == 0:
            return
        
        degrees = -layer.rotation
        self.undo_manager.save_state(self.layers)
        
        center_x = np.mean(layer.points[:, :, 0])
        center_y = np.mean(layer.points[:, :, 1])
        
        rad = np.radians(degrees)
        cos_a = np.cos(rad)
        sin_a = np.sin(rad)
        
        for i in range(layer.points.shape[0]):
            for j in range(layer.points.shape[1]):
                dx = layer.points[i, j, 0] - center_x
                dy = layer.points[i, j, 1] - center_y
                layer.points[i, j, 0] = center_x + dx * cos_a - dy * sin_a
                layer.points[i, j, 1] = center_y + dx * sin_a + dy * cos_a
        
        layer.rotation = 0.0
        
        self.update()
        if self.main_window:
            self.main_window.view_proj.update()
            self.main_window.statusBar().showMessage("🔄 Rotação resetada", 1500)

    def _move_selected_point(self, dx, dy):
        if not self.layers:
            return False
        
        layer = self.layers[self.active]
        if layer.locked or not layer.visible:
            return False
        
        if self.selected is not None:
            self.undo_manager.save_state(self.layers)
            i, j = self.selected
            layer.points[i, j, 0] += dx / self.zoom_level
            layer.points[i, j, 1] += dy / self.zoom_level
            self.update()
            if self.main_window:
                self.main_window.view_proj.update()
            return True
        else:
            self.undo_manager.save_state(self.layers)
            for i in range(layer.points.shape[0]):
                for j in range(layer.points.shape[1]):
                    layer.points[i, j, 0] += dx / self.zoom_level
                    layer.points[i, j, 1] += dy / self.zoom_level
            self.update()
            if self.main_window:
                self.main_window.view_proj.update()
            return True

    def keyPressEvent(self, e):
        if not self.layers or not self.is_edit_view:
            return
        
        layer = self.layers[self.active]
        
        # ZOOM
        if e.key() == QtCore.Qt.Key.Key_Plus or e.key() == QtCore.Qt.Key.Key_Equal:
            self.zoom_level *= 1.2
            self.zoom_level = min(10.0, self.zoom_level)
            self.update()
            if self.main_window:
                self.main_window.view_proj.update()
                self.main_window.statusBar().showMessage(f"🔍 Zoom: {self.zoom_level:.1f}x", 1000)
            return
                
        elif e.key() == QtCore.Qt.Key.Key_Minus:
            self.zoom_level /= 1.2
            self.zoom_level = max(0.1, self.zoom_level)
            self.update()
            if self.main_window:
                self.main_window.view_proj.update()
                self.main_window.statusBar().showMessage(f"🔍 Zoom: {self.zoom_level:.1f}x", 1000)
            return
                
        elif e.key() == QtCore.Qt.Key.Key_0 or e.key() == QtCore.Qt.Key.Key_Home:
            self._reset_view()
            return
            
        # MOVER PONTO/CAMADA COM SETAS
        elif e.key() == QtCore.Qt.Key.Key_Left:
            if self._move_selected_point(-0.01, 0):
                msg = "⬅️ Ponto movido" if self.selected else "⬅️ Camada movida"
                if self.main_window:
                    self.main_window.statusBar().showMessage(msg, 500)
            return
                
        elif e.key() == QtCore.Qt.Key.Key_Right:
            if self._move_selected_point(0.01, 0):
                msg = "➡️ Ponto movido" if self.selected else "➡️ Camada movida"
                if self.main_window:
                    self.main_window.statusBar().showMessage(msg, 500)
            return
                
        elif e.key() == QtCore.Qt.Key.Key_Up:
            if self._move_selected_point(0, 0.01):
                msg = "⬆️ Ponto movido" if self.selected else "⬆️ Camada movida"
                if self.main_window:
                    self.main_window.statusBar().showMessage(msg, 500)
            return
                
        elif e.key() == QtCore.Qt.Key.Key_Down:
            if self._move_selected_point(0, -0.01):
                msg = "⬇️ Ponto movido" if self.selected else "⬇️ Camada movida"
                if self.main_window:
                    self.main_window.statusBar().showMessage(msg, 500)
            return
        
        # ESCALA
        if e.key() == QtCore.Qt.Key.Key_S and not layer.locked and layer.visible:
            if e.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier:
                self._scale_layer(0.9)
            elif e.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier:
                self._reset_layer_scale()
            else:
                self._scale_layer(1.1)
            return
        
        # ROTAÇÃO
        if e.key() == QtCore.Qt.Key.Key_Q and not layer.locked and layer.visible:
            if e.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier:
                self._rotate_layer(-5)
            elif e.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier:
                self._reset_rotation()
            else:
                self._rotate_layer(5)
            return
        
        # VISIBILIDADE
        if e.key() == QtCore.Qt.Key.Key_V:
            layer.visible = not layer.visible
            self.update()
            if self.main_window:
                self.main_window.view_proj.update()
                self.main_window._update_list_display()
            return
                
        # TRAVAR
        if e.key() == QtCore.Qt.Key.Key_L:
            layer.locked = not layer.locked
            self.update()
            if self.main_window:
                self.main_window._update_list_display()
                self.main_window._update_lock_button()
            return
                
        # DELETAR
        if e.key() == QtCore.Qt.Key.Key_Delete:
            if self.main_window:
                self.main_window._remove_layer()
            return
                
        # UNDO/REDO
        if e.key() == QtCore.Qt.Key.Key_Z and e.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier:
            if e.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier:
                if self.undo_manager.redo(self.layers):
                    self.update()
                    if self.main_window:
                        self.main_window.view_proj.update()
            else:
                if self.undo_manager.undo(self.layers):
                    self.update()
                    if self.main_window:
                        self.main_window.view_proj.update()
            return
                        
        # RESET GRID
        if e.key() == QtCore.Qt.Key.Key_R:
            if not layer.locked and layer.visible:
                self.undo_manager.save_state(self.layers)
                layer.rebuild_grid()
                self._reset_view()
                self.update()
                if self.main_window:
                    self.main_window.view_proj.update()
                    self.main_window._update_grid_sliders()
            return
                    
        # FIT MODE
        if e.key() == QtCore.Qt.Key.Key_F:
            if self.main_window:
                self.main_window._toggle_fit_mode()
            return
        
        # ESC - Desselecionar ponto
        if e.key() == QtCore.Qt.Key.Key_Escape:
            self.selected = None
            self.update()
            if self.main_window:
                self.main_window.statusBar().showMessage("📍 Seleção cancelada", 1000)
            return


# =============================================================================
# ITEM PERSONALIZADO PARA LISTA DE CAMADAS
# =============================================================================
class LayerListItem(QtWidgets.QWidget):
    def __init__(self, layer, main_window, index, parent=None):
        super().__init__(parent)
        self.layer = layer
        self.main_window = main_window
        self.index = index
        self._setup_ui()
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
    def _setup_ui(self):
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)
        
        self.visible_cb = QtWidgets.QCheckBox()
        self.visible_cb.setChecked(self.layer.visible)
        self.visible_cb.toggled.connect(self._toggle_visibility)
        layout.addWidget(self.visible_cb)
        
        icon = "✨" if self.layer.has_alpha else ("🎬" if self.layer.is_video else "🖼️")
        if self.layer.chroma_enabled:
            icon = "🎭"
        status = "🔒" if self.layer.locked else ""
        rot_text = f" {self.layer.rotation:.0f}°" if self.layer.rotation != 0 else ""
        grid_text = f" [{self.layer.grid_cols}x{self.layer.grid_rows}]" if self.layer.grid_cols != 1 or self.layer.grid_rows != 1 else ""
        self.label = ClickableLabel(f"{icon}{rot_text}{grid_text} {status} {os.path.basename(self.layer.path)}")
        self.label.setStyleSheet("padding: 3px;")
        self.label.clicked.connect(self._select_layer)
        layout.addWidget(self.label, 1)
        
        self.setLayout(layout)
        self.setMouseTracking(True)
        self.update_style()
    
    def _show_context_menu(self, pos):
        menu = QtWidgets.QMenu()
        
        order_menu = menu.addMenu("📶 Ordem")
        up_action = order_menu.addAction("⬆️ Mover para Frente")
        up_action.triggered.connect(lambda: self.main_window._move_layer_up(self.index))
        down_action = order_menu.addAction("⬇️ Mover para Trás")
        down_action.triggered.connect(lambda: self.main_window._move_layer_down(self.index))
        order_menu.addSeparator()
        top_action = order_menu.addAction("⏫ Enviar para Frente de Tudo")
        top_action.triggered.connect(lambda: self.main_window._move_layer_to_top(self.index))
        bottom_action = order_menu.addAction("⏬ Enviar para Trás de Tudo")
        bottom_action.triggered.connect(lambda: self.main_window._move_layer_to_bottom(self.index))
        
        menu.addSeparator()
        
        duplicate_action = menu.addAction("📋 Duplicar Camada")
        duplicate_action.triggered.connect(self._duplicate_layer)
        
        replace_action = menu.addAction("🔄 Substituir Arquivo...")
        replace_action.triggered.connect(self._replace_media)
        
        menu.addSeparator()
        
        chroma_menu = menu.addMenu("🎭 Chroma Key")
        if self.layer.chroma_enabled:
            config_action = chroma_menu.addAction("⚙️ Configurar...")
            config_action.triggered.connect(self._configure_chroma)
            disable_action = chroma_menu.addAction("❌ Desativar")
            disable_action.triggered.connect(self._disable_chroma)
        else:
            enable_action = chroma_menu.addAction("✅ Ativar (usar preto)...")
            enable_action.triggered.connect(self._enable_chroma_default)
            config_action = chroma_menu.addAction("⚙️ Configurar...")
            config_action.triggered.connect(self._configure_chroma)
        
        menu.addSeparator()
        
        rotate_menu = menu.addMenu("🔄 Rotação")
        rotate_right = rotate_menu.addAction("↪️ Rotacionar +5°")
        rotate_right.triggered.connect(lambda: self.main_window.view_edit._rotate_layer(5))
        rotate_left = rotate_menu.addAction("↩️ Rotacionar -5°")
        rotate_left.triggered.connect(lambda: self.main_window.view_edit._rotate_layer(-5))
        rotate_reset = rotate_menu.addAction("🔄 Resetar Rotação")
        rotate_reset.triggered.connect(lambda: self.main_window.view_edit._reset_rotation())
        
        menu.addSeparator()
        
        reset_action = menu.addAction("🔄 Resetar Grid")
        reset_action.triggered.connect(self._reset_grid)
        
        menu.exec(self.mapToGlobal(pos))
    
    def _duplicate_layer(self):
        self.main_window._duplicate_layer(self.index)
    
    def _replace_media(self):
        self.main_window._replace_media(self.index)
    
    def _enable_chroma_default(self):
        self.main_window._enable_chroma_key(self.index)
    
    def _disable_chroma(self):
        self.main_window._disable_chroma_key(self.index)
    
    def _configure_chroma(self):
        self.main_window._configure_chroma_key(self.index)
    
    def _reset_grid(self):
        if not self.layer.locked:
            self.main_window.view_edit.undo_manager.save_state(self.main_window.layers)
            self.layer.rebuild_grid()
            self.main_window._update_all()
            self.main_window.statusBar().showMessage("🔄 Grid resetado", 1500)
    
    def mousePressEvent(self, event):
        self._select_layer()
        super().mousePressEvent(event)
    
    def _toggle_visibility(self, checked):
        self.layer.visible = checked
        self.update_display()
        self.main_window._update_all()
        self.main_window.statusBar().showMessage(f"👁 Camada {'visível' if checked else 'oculta'}", 1500)
    
    def _select_layer(self):
        self.main_window._select_layer_by_index(self.index)
    
    def update_display(self):
        self.visible_cb.setChecked(self.layer.visible)
        icon = "✨" if self.layer.has_alpha else ("🎬" if self.layer.is_video else "🖼️")
        if self.layer.chroma_enabled:
            icon = "🎭"
        status = "🔒" if self.layer.locked else ""
        rot_text = f" {self.layer.rotation:.0f}°" if self.layer.rotation != 0 else ""
        grid_text = f" [{self.layer.grid_cols}x{self.layer.grid_rows}]" if self.layer.grid_cols != 1 or self.layer.grid_rows != 1 else ""
        self.label.setText(f"{icon}{rot_text}{grid_text} {status} {os.path.basename(self.layer.path)}")
        self.update_style()
    
    def update_style(self):
        if self.index == self.main_window.view_edit.active:
            self.setStyleSheet("""
                QWidget {
                    background-color: #4a6c8f;
                    border-radius: 5px;
                    border: 1px solid #5a7c9f;
                }
                QCheckBox { background-color: transparent; }
                QLabel { background-color: transparent; color: white; font-weight: bold; }
            """)
        else:
            self.setStyleSheet("""
                QWidget {
                    background-color: transparent;
                    border-radius: 5px;
                }
                QWidget:hover { background-color: #3a3a3a; }
                QCheckBox { background-color: transparent; }
                QLabel { background-color: transparent; color: #ccc; }
            """)


class ClickableLabel(QtWidgets.QLabel):
    clicked = QtCore.Signal()
    
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


# =============================================================================
# JANELA PRINCIPAL
# =============================================================================
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{PROGRAM_NAME} - Mapeamento de Projeção Educacional")
        self.resize(1000, 600)
        
        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QtGui.QIcon(ICON_PATH))
        
        self.settings = QtCore.QSettings("MappEduc", "Settings")
        self._load_settings()
        
        self.view_edit = GLView(self, "edit")
        self.view_proj = GLView(self, "proj")
        
        self.layers = []
        self.view_edit.layers = self.layers
        self.view_proj.layers = self.layers
        
        self.layer_items = []
        
        self._create_ui()
        
        self.view_proj.setWindowTitle("Projeção - MappEduc")
        if os.path.exists(ICON_PATH):
            self.view_proj.setWindowIcon(QtGui.QIcon(ICON_PATH))
        self.view_proj.resize(640, 480)
        self.view_proj.show()
        
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._update_all)
        self.timer.start(50)
        
        if self.show_welcome:
            QtCore.QTimer.singleShot(100, self._show_welcome)
        
        self.statusBar().showMessage(f"🎓 {PROGRAM_NAME} v{PROGRAM_VERSION} | F1 para ajuda | {PROGRAM_AUTHOR}")
    
    def _load_settings(self):
        self.show_welcome = self.settings.value("show_welcome", True, type=bool)
        self.last_project_folder = self.settings.value("last_project_folder", os.path.expanduser("~"))
        self.last_media_folder = self.settings.value("last_media_folder", os.path.expanduser("~"))
    
    def _save_settings(self):
        self.settings.setValue("show_welcome", self.show_welcome)
        self.settings.setValue("last_project_folder", self.last_project_folder)
        self.settings.setValue("last_media_folder", self.last_media_folder)
    
    def _show_welcome(self):
        dialog = WelcomeDialog(self)
        dialog.exec()
        self.show_welcome = not dialog.should_not_show_again()
        self._save_settings()
    
    def _create_ui(self):
        self.list_container = QtWidgets.QWidget()
        self.list_layout = QtWidgets.QVBoxLayout()
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(3)
        self.list_layout.addStretch()
        self.list_container.setLayout(self.list_layout)
        
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidget(self.list_container)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(250)
        scroll_area.setMaximumHeight(400)
        
        btn_add = QtWidgets.QPushButton("➕ Adicionar Mídia")
        btn_add.clicked.connect(self._add_media)
        
        btn_remove = QtWidgets.QPushButton("❌ Remover Selecionada")
        btn_remove.clicked.connect(self._remove_layer)
        
        self.btn_lock = QtWidgets.QPushButton("🔓 Destravar")
        self.btn_lock.setCheckable(True)
        self.btn_lock.clicked.connect(self._toggle_lock)
        
        self.btn_fit = QtWidgets.QPushButton("📐 Modo Ajuste")
        self.btn_fit.setCheckable(True)
        self.btn_fit.setChecked(True)
        self.btn_fit.clicked.connect(self._toggle_fit_mode)
        
        self.btn_fullscreen = QtWidgets.QPushButton("🖥️ Tela Cheia (F11)")
        self.btn_fullscreen.clicked.connect(self._toggle_fullscreen)
        
        btn_export = QtWidgets.QPushButton("💾 Salvar Projeto")
        btn_export.clicked.connect(self._export_project)
        
        btn_import = QtWidgets.QPushButton("📂 Abrir Projeto")
        btn_import.clicked.connect(self._import_project)
        
        btn_help = QtWidgets.QPushButton("📚 Ajuda (F1)")
        btn_help.clicked.connect(self._show_help)
        
        btn_about = QtWidgets.QPushButton("ℹ️ Sobre")
        btn_about.clicked.connect(self._show_about)
        
        btn_reset_view = QtWidgets.QPushButton("🔄 Reset View (0/Home)")
        btn_reset_view.clicked.connect(lambda: self.view_edit._reset_view())
        
        btn_deselect = QtWidgets.QPushButton("📍 Deselecionar (ESC)")
        btn_deselect.clicked.connect(self._deselect_point)
        
        # NOVO: Checkbox para mostrar grid na projeção
        self.show_grid_cb = QtWidgets.QCheckBox("☑ Mostrar Grid na Projeção")
        self.show_grid_cb.setChecked(False)
        self.show_grid_cb.toggled.connect(self._toggle_proj_grid)
        
        self.cols_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.cols_slider.setMinimum(1)
        self.cols_slider.setMaximum(8)
        self.cols_slider.setValue(1)
        self.cols_slider.valueChanged.connect(self._change_grid)
        
        self.rows_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.rows_slider.setMinimum(1)
        self.rows_slider.setMaximum(8)
        self.rows_slider.setValue(1)
        self.rows_slider.valueChanged.connect(self._change_grid)
        
        self.opacity_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.valueChanged.connect(self._change_opacity)
        
        self.lbl_cols_value = QtWidgets.QLabel("1")
        self.cols_slider.valueChanged.connect(lambda v: self.lbl_cols_value.setText(str(v)))
        
        self.lbl_rows_value = QtWidgets.QLabel("1")
        self.rows_slider.valueChanged.connect(lambda v: self.lbl_rows_value.setText(str(v)))
        
        self.lbl_grid_full = QtWidgets.QLabel("Malha: 1x1")
        self.lbl_opacity_value = QtWidgets.QLabel("100%")
        self.opacity_slider.valueChanged.connect(lambda v: self.lbl_opacity_value.setText(f"{v}%"))
        
        side = QtWidgets.QVBoxLayout()
        side.setSpacing(5)
        
        side.addWidget(QtWidgets.QLabel("📁 CAMADAS (clique direito para opções)"))
        side.addWidget(scroll_area)
        
        layer_buttons = QtWidgets.QHBoxLayout()
        layer_buttons.addWidget(btn_add)
        layer_buttons.addWidget(btn_remove)
        side.addLayout(layer_buttons)
        side.addWidget(self.btn_lock)
        side.addWidget(self.btn_fit)
        side.addWidget(QHLine())
        
        side.addWidget(QtWidgets.QLabel("⚙️ CONTROLES"))
        
        cols_layout = QtWidgets.QHBoxLayout()
        cols_layout.addWidget(QtWidgets.QLabel("Colunas:"))
        cols_layout.addWidget(self.lbl_cols_value)
        side.addLayout(cols_layout)
        side.addWidget(self.cols_slider)
        
        rows_layout = QtWidgets.QHBoxLayout()
        rows_layout.addWidget(QtWidgets.QLabel("Linhas:"))
        rows_layout.addWidget(self.lbl_rows_value)
        side.addLayout(rows_layout)
        side.addWidget(self.rows_slider)
        
        side.addWidget(self.lbl_grid_full)
        
        opacity_layout = QtWidgets.QHBoxLayout()
        opacity_layout.addWidget(QtWidgets.QLabel("Opacidade:"))
        opacity_layout.addWidget(self.lbl_opacity_value)
        side.addLayout(opacity_layout)
        side.addWidget(self.opacity_slider)
        side.addWidget(QHLine())
        
        side.addWidget(QtWidgets.QLabel("🖼️ VISUALIZAÇÃO"))
        side.addWidget(self.show_grid_cb)  # NOVO: Checkbox do grid
        side.addWidget(btn_reset_view)
        side.addWidget(btn_deselect)
        side.addWidget(QHLine())
        
        side.addWidget(QtWidgets.QLabel("💾 PROJETO"))
        side.addWidget(self.btn_fullscreen)
        side.addWidget(btn_export)
        side.addWidget(btn_import)
        side.addWidget(QHLine())
        
        side.addWidget(btn_help)
        side.addWidget(btn_about)
        
        side.addStretch()
        
        if os.path.exists(ICON_PATH):
            icon_label = QtWidgets.QLabel()
            icon_pixmap = QtGui.QPixmap(ICON_PATH).scaled(40, 40, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
            icon_label.setPixmap(icon_pixmap)
            icon_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            side.addWidget(icon_label)
        
        author_label = QtWidgets.QLabel(
            f"<b>{PROGRAM_NAME} v{PROGRAM_VERSION}</b><br>"
            f"{PROGRAM_AUTHOR}<br>"
            f"<span style='color: #666;'>{PROGRAM_LICENSE}</span>"
        )
        author_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        author_label.setStyleSheet("padding: 5px; font-size: 8px;")
        side.addWidget(author_label)
        
        widget_side = QtWidgets.QWidget()
        widget_side.setLayout(side)
        widget_side.setFixedWidth(250)
        
        central = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(widget_side)
        layout.addWidget(self.view_edit)
        layout.setContentsMargins(0, 0, 0, 0)
        central.setLayout(layout)
        
        self.setCentralWidget(central)
    
    def _toggle_proj_grid(self, checked):
        """Ativa/desativa a exibição do grid na janela de projeção"""
        self.view_proj.show_grid_in_proj = checked
        self.view_proj.update()
        if checked:
            self.statusBar().showMessage("📐 Grid exibido na projeção", 1500)
        else:
            self.statusBar().showMessage("📐 Grid oculto na projeção", 1500)
    
    def _deselect_point(self):
        self.view_edit.selected = None
        self.view_edit.update()
        self.statusBar().showMessage("📍 Seleção cancelada", 1000)
    
    def _show_about(self):
        about_text = f"""
        <h2>🎓 {PROGRAM_NAME}</h2>
        <p><b>Ferramenta de Mapeamento de Projeção Educacional</b></p>
        <p>Versão {PROGRAM_VERSION}</p>
        <h3>👨‍🏫 Autor</h3>
        <p><b>{PROGRAM_AUTHOR}</b><br>{PROGRAM_AUTHOR_TITLE}</p>
        <h3>📜 Licença</h3>
        <p>{PROGRAM_COPYRIGHT}<br>{PROGRAM_LICENSE}</p>
        <h3>✨ Novidades v{PROGRAM_VERSION}</h3>
        <ul>
        <li>📐 Grid visível na projeção (linhas ciano)</li>
        <li>📐 Malha assimétrica (colunas ≠ linhas)</li>
        <li>🔄 Rotação de camadas (Q)</li>
        <li>📶 Reordenamento de camadas (Ctrl+↑↓)</li>
        <li>🎭 Chroma Key (máscara por cor)</li>
        </ul>
        """
        
        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle(f"Sobre o {PROGRAM_NAME}")
        if os.path.exists(ICON_PATH):
            msg.setWindowIcon(QtGui.QIcon(ICON_PATH))
        msg.setTextFormat(QtCore.Qt.TextFormat.RichText)
        msg.setText(about_text)
        msg.exec()
    
    def _show_help(self):
        help_text = f"""
        <h2>🎓 {PROGRAM_NAME} - Guia do Educador</h2>
        
        <h3>📐 Grid na Projeção (v{PROGRAM_VERSION})</h3>
        <ul>
        <li>Checkbox <b>"Mostrar Grid na Projeção"</b></li>
        <li>Exibe linhas ciano na janela de projeção</li>
        <li>Ajuda a calibrar a deformação na superfície real</li>
        </ul>
        
        <h3>📐 Malha Assimétrica</h3>
        <ul>
        <li>Sliders independentes para <b>Colunas</b> e <b>Linhas</b></li>
        <li>Ex: 6 colunas x 1 linha, 2 colunas x 5 linhas</li>
        </ul>
        
        <h3>⌨️ Atalhos</h3>
        <ul>
        <li><b>Q</b> - Rotação +5°</li>
        <li><b>Ctrl+↑↓</b> - Reordenar camadas</li>
        <li><b>V</b> - Visível/Invisível</li>
        <li><b>L</b> - Travar/Destravar</li>
        <li><b>R</b> - Resetar grid</li>
        <li><b>S</b> - Escala</li>
        <li><b>Ctrl+D</b> - Duplicar</li>
        <li><b>F11</b> - Tela cheia</li>
        <li><b>Ctrl+Z</b> - Desfazer</li>
        </ul>
        """
        
        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle(f"Ajuda do {PROGRAM_NAME}")
        if os.path.exists(ICON_PATH):
            msg.setWindowIcon(QtGui.QIcon(ICON_PATH))
        msg.setTextFormat(QtCore.Qt.TextFormat.RichText)
        msg.setText(help_text)
        msg.exec()
    
    def _move_layer_up(self, index):
        if index <= 0 or index >= len(self.layers):
            return
        
        self.layers[index], self.layers[index-1] = self.layers[index-1], self.layers[index]
        
        item = self.layer_items.pop(index)
        self.layer_items.insert(index - 1, item)
        self.list_layout.removeWidget(item)
        self.list_layout.insertWidget(index - 1, item)
        
        self._update_list_display()
        self._select_layer_by_index(index - 1)
        self._update_all()
        self.statusBar().showMessage("⬆️ Camada movida para frente", 1000)
    
    def _move_layer_down(self, index):
        if index < 0 or index >= len(self.layers) - 1:
            return
        
        self.layers[index], self.layers[index+1] = self.layers[index+1], self.layers[index]
        
        item = self.layer_items.pop(index)
        self.layer_items.insert(index + 1, item)
        self.list_layout.removeWidget(item)
        self.list_layout.insertWidget(index + 1, item)
        
        self._update_list_display()
        self._select_layer_by_index(index + 1)
        self._update_all()
        self.statusBar().showMessage("⬇️ Camada movida para trás", 1000)
    
    def _move_layer_to_top(self, index):
        if index <= 0 or index >= len(self.layers):
            return
        
        layer = self.layers.pop(index)
        self.layers.insert(0, layer)
        
        item = self.layer_items.pop(index)
        self.layer_items.insert(0, item)
        self.list_layout.removeWidget(item)
        self.list_layout.insertWidget(0, item)
        
        self._update_list_display()
        self._select_layer_by_index(0)
        self._update_all()
        self.statusBar().showMessage("⏫ Camada enviada para frente de tudo", 1000)
    
    def _move_layer_to_bottom(self, index):
        if index < 0 or index >= len(self.layers) - 1:
            return
        
        last_idx = len(self.layers) - 1
        
        layer = self.layers.pop(index)
        self.layers.append(layer)
        
        item = self.layer_items.pop(index)
        self.layer_items.append(item)
        self.list_layout.removeWidget(item)
        self.list_layout.insertWidget(last_idx, item)
        
        self._update_list_display()
        self._select_layer_by_index(last_idx)
        self._update_all()
        self.statusBar().showMessage("⏬ Camada enviada para trás de tudo", 1000)
    
    def _enable_chroma_key(self, index):
        if index < 0 or index >= len(self.layers):
            return
        layer = self.layers[index]
        layer.set_chroma_key(True, (0, 0, 0), 30)
        self._update_list_display()
        self._update_all()
        self.statusBar().showMessage("🎭 Chroma Key ativado (preto transparente)", 2000)
    
    def _disable_chroma_key(self, index):
        if index < 0 or index >= len(self.layers):
            return
        layer = self.layers[index]
        layer.set_chroma_key(False)
        self._update_list_display()
        self._update_all()
        self.statusBar().showMessage("🎭 Chroma Key desativado", 2000)
    
    def _configure_chroma_key(self, index):
        if index < 0 or index >= len(self.layers):
            return
        
        layer = self.layers[index]
        
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Configurar Chroma Key")
        dialog.setMinimumWidth(400)
        
        layout = QtWidgets.QVBoxLayout()
        
        layout.addWidget(QtWidgets.QLabel("Cor a ser removida:"))
        
        color_group = QtWidgets.QButtonGroup(dialog)
        color_layout = QtWidgets.QHBoxLayout()
        
        colors = [
            ("⬛ Preto", (0, 0, 0)),
            ("⬜ Branco", (255, 255, 255)),
            ("🟩 Verde", (0, 255, 0)),
            ("🟦 Azul", (0, 0, 255)),
            ("🟥 Vermelho", (255, 0, 0)),
        ]
        
        self.chroma_color = layer.chroma_color
        
        for i, (name, color) in enumerate(colors):
            btn = QtWidgets.QRadioButton(name)
            if color == self.chroma_color:
                btn.setChecked(True)
            btn.toggled.connect(lambda checked, c=color: setattr(self, 'chroma_color', c) if checked else None)
            color_group.addButton(btn)
            color_layout.addWidget(btn)
        
        layout.addLayout(color_layout)
        layout.addSpacing(10)
        
        layout.addWidget(QtWidgets.QLabel("Tolerância:"))
        tolerance_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        tolerance_slider.setMinimum(0)
        tolerance_slider.setMaximum(100)
        tolerance_slider.setValue(layer.chroma_tolerance)
        layout.addWidget(tolerance_slider)
        
        tolerance_label = QtWidgets.QLabel(f"{layer.chroma_tolerance}")
        tolerance_slider.valueChanged.connect(lambda v: tolerance_label.setText(str(v)))
        layout.addWidget(tolerance_label)
        layout.addSpacing(10)
        
        enable_cb = QtWidgets.QCheckBox("Ativar Chroma Key")
        enable_cb.setChecked(layer.chroma_enabled)
        layout.addWidget(enable_cb)
        layout.addSpacing(10)
        
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | 
                                              QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            layer.set_chroma_key(
                enable_cb.isChecked(),
                self.chroma_color,
                tolerance_slider.value()
            )
            self._update_list_display()
            self._update_all()
            if enable_cb.isChecked():
                self.statusBar().showMessage(f"🎭 Chroma Key configurado (tolerância: {tolerance_slider.value()})", 2000)
            else:
                self.statusBar().showMessage("🎭 Chroma Key desativado", 2000)
    
    def _add_media(self):
        paths, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, "Selecionar mídia", self.last_media_folder,
            "Mídias suportadas (*.mp4 *.avi *.mov *.jpg *.png *.bmp);;Todos (*.*)"
        )
        
        if paths:
            self.last_media_folder = os.path.dirname(paths[0])
            self._save_settings()
        
        for path in paths:
            try:
                layer = Layer(path)
                self.layers.insert(0, layer)
                self._add_layer_item_at_index(layer, 0)
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Erro", str(e))
        
        if self.layers:
            self._select_layer_by_index(0)
            self._update_all()
    
    def _add_layer_item(self, layer):
        index = len(self.layer_items)
        self._add_layer_item_at_index(layer, index)
    
    def _add_layer_item_at_index(self, layer, index):
        item = LayerListItem(layer, self, index)
        self.layer_items.insert(index, item)
        self.list_layout.insertWidget(index, item)
        
        for i, item in enumerate(self.layer_items):
            item.index = i
        
        item.update_display()
    
    def _update_list_display(self):
        for i, item in enumerate(self.layer_items):
            item.index = i
            item.update_display()
    
    def _update_grid_sliders(self):
        if not self.layers:
            return
        layer = self.layers[self.view_edit.active]
        self.cols_slider.blockSignals(True)
        self.rows_slider.blockSignals(True)
        self.cols_slider.setValue(layer.grid_cols)
        self.rows_slider.setValue(layer.grid_rows)
        self.cols_slider.blockSignals(False)
        self.rows_slider.blockSignals(False)
        self.lbl_grid_full.setText(f"Malha: {layer.grid_cols}x{layer.grid_rows}")
    
    def _select_layer_by_index(self, i):
        if i >= 0 and i < len(self.layers):
            self.view_edit.active = i
            self.view_proj.active = i
            layer = self.layers[i]
            
            self.cols_slider.blockSignals(True)
            self.rows_slider.blockSignals(True)
            self.opacity_slider.blockSignals(True)
            self.btn_fit.blockSignals(True)
            
            self.cols_slider.setValue(layer.grid_cols)
            self.rows_slider.setValue(layer.grid_rows)
            self.opacity_slider.setValue(int(layer.opacity*100))
            self.btn_fit.setChecked(layer.fit_mode)
            
            self.cols_slider.blockSignals(False)
            self.rows_slider.blockSignals(False)
            self.opacity_slider.blockSignals(False)
            self.btn_fit.blockSignals(False)
            
            self._update_lock_button()
            self.lbl_grid_full.setText(f"Malha: {layer.grid_cols}x{layer.grid_rows}")
            self.lbl_opacity_value.setText(f"{int(layer.opacity*100)}%")
            
            self._update_list_display()
            self.statusBar().showMessage(f"📌 Camada selecionada: {os.path.basename(layer.path)}", 1500)
    
    def _duplicate_layer(self, index):
        if index < 0 or index >= len(self.layers):
            return
        
        original = self.layers[index]
        
        try:
            new_layer = Layer(original.path)
            new_layer.points = original.points.copy()
            new_layer.grid_cols = original.grid_cols
            new_layer.grid_rows = original.grid_rows
            new_layer.opacity = original.opacity
            new_layer.visible = original.visible
            new_layer.locked = False
            new_layer.fit_mode = original.fit_mode
            new_layer.rotation = original.rotation
            
            new_layer.chroma_enabled = original.chroma_enabled
            new_layer.chroma_color = original.chroma_color
            new_layer.chroma_tolerance = original.chroma_tolerance
            new_layer._process_frame()
            
            insert_idx = index + 1
            self.layers.insert(insert_idx, new_layer)
            self._add_layer_item_at_index(new_layer, insert_idx)
            self._select_layer_by_index(insert_idx)
            self._update_all()
            
            self.statusBar().showMessage(f"📋 Camada duplicada: {os.path.basename(new_layer.path)}", 2000)
            
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Erro", f"Não foi possível duplicar a camada:\n{str(e)}")
    
    def _replace_media(self, index):
        if index < 0 or index >= len(self.layers):
            return
        
        layer = self.layers[index]
        
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Selecionar nova mídia", self.last_media_folder,
            "Mídias suportadas (*.mp4 *.avi *.mov *.jpg *.png *.bmp);;Todos (*.*)"
        )
        
        if not path:
            return
        
        try:
            old_points = layer.points.copy()
            old_grid_cols = layer.grid_cols
            old_grid_rows = layer.grid_rows
            old_opacity = layer.opacity
            old_visible = layer.visible
            old_fit_mode = layer.fit_mode
            old_rotation = layer.rotation
            old_chroma_enabled = layer.chroma_enabled
            old_chroma_color = layer.chroma_color
            old_chroma_tolerance = layer.chroma_tolerance
            
            layer.cleanup()
            if layer.texture_edit:
                glDeleteTextures([layer.texture_edit])
                layer.texture_edit = None
            if layer.texture_proj:
                glDeleteTextures([layer.texture_proj])
                layer.texture_proj = None
            
            layer.__init__(path)
            
            layer.points = old_points
            layer.grid_cols = old_grid_cols
            layer.grid_rows = old_grid_rows
            layer.opacity = old_opacity
            layer.visible = old_visible
            layer.fit_mode = old_fit_mode
            layer.rotation = old_rotation
            layer.chroma_enabled = old_chroma_enabled
            layer.chroma_color = old_chroma_color
            layer.chroma_tolerance = old_chroma_tolerance
            layer._process_frame()
            
            h_old, w_old = old_points.shape[:2]
            h_new, w_new = layer.points.shape[:2]
            
            aspect_old = w_old / h_old if h_old > 0 else 1
            aspect_new = w_new / h_new if h_new > 0 else 1
            
            if abs(aspect_old - aspect_new) > 0.1:
                reply = QtWidgets.QMessageBox.question(
                    self, "Proporção Diferente",
                    f"⚠️ O novo arquivo tem proporção diferente do original.\n\n"
                    f"Deseja ajustar o grid automaticamente?",
                    QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
                )
                
                if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                    layer.rebuild_grid()
            
            self._update_list_display()
            self._update_all()
            
            self.statusBar().showMessage(f"🔄 Arquivo substituído: {os.path.basename(path)}", 2000)
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Erro", f"Não foi possível substituir o arquivo:\n{str(e)}")
    
    def _remove_layer(self):
        if not self.layers:
            return
        
        idx = self.view_edit.active
        
        layer = self.layers[idx]
        layer.cleanup()
        
        if layer.texture_edit:
            glDeleteTextures([layer.texture_edit])
        if layer.texture_proj:
            glDeleteTextures([layer.texture_proj])
        
        del self.layers[idx]
        
        item = self.layer_items[idx]
        self.list_layout.removeWidget(item)
        item.deleteLater()
        del self.layer_items[idx]
        
        if self.layers:
            new_idx = min(idx, len(self.layers)-1)
            self._select_layer_by_index(new_idx)
        else:
            self.view_edit.selected = None
        
        self._update_all()
    
    def _update_lock_button(self):
        if not self.layers:
            return
        layer = self.layers[self.view_edit.active]
        self.btn_lock.setChecked(layer.locked)
        self.btn_lock.setText("🔒 Travado" if layer.locked else "🔓 Destravar")
    
    def _toggle_lock(self, checked):
        if not self.layers:
            return
        layer = self.layers[self.view_edit.active]
        layer.locked = checked
        self.btn_lock.setText("🔒 Travado" if checked else "🔓 Destravar")
        self._update_list_display()
        self.view_edit.update()
    
    def _change_grid(self):
        if not self.layers:
            return
        layer = self.layers[self.view_edit.active]
        if not layer.locked and layer.visible:
            cols = self.cols_slider.value()
            rows = self.rows_slider.value()
            self.view_edit.undo_manager.save_state(self.layers)
            layer.set_grid(cols, rows)
            self.lbl_grid_full.setText(f"Malha: {cols}x{rows}")
            self._update_all()
    
    def _change_opacity(self, v):
        if not self.layers:
            return
        layer = self.layers[self.view_edit.active]
        layer.opacity = v/100.0
        self.lbl_opacity_value.setText(f"{v}%")
        self._update_all()
        self.statusBar().showMessage(f"💧 Opacidade: {v}%", 1000)
    
    def _toggle_fit_mode(self):
        if not self.layers:
            return
        layer = self.layers[self.view_edit.active]
        if not layer.locked and layer.visible:
            self.view_edit.undo_manager.save_state(self.layers)
            layer.fit_mode = self.btn_fit.isChecked()
            layer.rebuild_grid()
            self._update_all()
    
    def _toggle_fullscreen(self):
        if self.view_proj.isFullScreen():
            self.view_proj.showNormal()
            self.btn_fullscreen.setText("🖥️ Tela Cheia (F11)")
        else:
            self.view_proj.showFullScreen()
            self.btn_fullscreen.setText("⬛ Sair Tela Cheia")
    
    def _export_project(self):
        if not self.layers:
            QtWidgets.QMessageBox.information(self, "Aviso", "Nenhuma mídia carregada.")
            return
        
        default_name = f"projeto_mappeduc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mep"
        default_path = os.path.join(self.last_project_folder, default_name)
        
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Salvar Projeto", default_path,
            "Projeto MappEduc (*.mep);;Todos (*.*)"
        )
        if not filename:
            return
        
        if not filename.endswith('.mep'):
            filename += '.mep'
        
        self.last_project_folder = os.path.dirname(filename)
        self._save_settings()
        
        data = {'layers': []}
        for layer in self.layers:
            data['layers'].append({
                'path': layer.path,
                'grid_cols': layer.grid_cols,
                'grid_rows': layer.grid_rows,
                'points': layer.points.tolist(),
                'opacity': layer.opacity,
                'visible': layer.visible,
                'locked': layer.locked,
                'fit_mode': layer.fit_mode,
                'rotation': layer.rotation,
                'chroma_enabled': layer.chroma_enabled,
                'chroma_color': layer.chroma_color,
                'chroma_tolerance': layer.chroma_tolerance
            })
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.statusBar().showMessage(f"✅ Projeto salvo: {os.path.basename(filename)}", 5000)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Erro", f"Não foi possível salvar:\n{str(e)}")
    
    def _import_project(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Abrir Projeto", self.last_project_folder,
            "Projeto MappEduc (*.mep);;Todos (*.*)"
        )
        if not filename:
            return
        
        if not os.path.exists(filename):
            QtWidgets.QMessageBox.critical(self, "Erro", f"Arquivo não encontrado:\n{filename}")
            return
        
        self.last_project_folder = os.path.dirname(filename)
        self._save_settings()
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if self.layers:
                reply = QtWidgets.QMessageBox.question(
                    self, "Confirmar", "Substituir projeto atual?",
                    QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
                )
                if reply != QtWidgets.QMessageBox.StandardButton.Yes:
                    return
            
            for layer in self.layers:
                layer.cleanup()
            self.layers.clear()
            
            for item in self.layer_items:
                self.list_layout.removeWidget(item)
                item.deleteLater()
            self.layer_items.clear()
            
            for ld in data['layers']:
                try:
                    layer = Layer(ld['path'])
                    if 'grid' in ld and 'grid_cols' not in ld:
                        layer.grid_cols = ld['grid']
                        layer.grid_rows = ld['grid']
                    else:
                        layer.grid_cols = ld.get('grid_cols', 1)
                        layer.grid_rows = ld.get('grid_rows', 1)
                    layer.points = np.array(ld['points'], dtype=np.float32)
                    layer.opacity = ld['opacity']
                    layer.visible = ld.get('visible', True)
                    layer.locked = ld.get('locked', False)
                    layer.fit_mode = ld.get('fit_mode', True)
                    layer.rotation = ld.get('rotation', 0.0)
                    layer.chroma_enabled = ld.get('chroma_enabled', False)
                    layer.chroma_color = tuple(ld.get('chroma_color', (0, 0, 0)))
                    layer.chroma_tolerance = ld.get('chroma_tolerance', 30)
                    layer._process_frame()
                    
                    self.layers.append(layer)
                    self._add_layer_item(layer)
                except Exception as e:
                    print(f"Erro ao carregar: {e}")
            
            if self.layers:
                self._select_layer_by_index(0)
                self._update_list_display()
            
            self.view_edit.undo_manager = UndoManager()
            self.view_edit.selected = None
            self._update_all()
            self.statusBar().showMessage(f"✅ Projeto carregado: {os.path.basename(filename)}", 5000)
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Erro", f"Erro ao carregar:\n{str(e)}")
    
    def _update_all(self):
        self.view_edit.update()
        self.view_proj.update()
    
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key.Key_F11:
            self._toggle_fullscreen()
            return
        elif event.key() == QtCore.Qt.Key.Key_F1:
            self._show_help()
            return
        elif event.key() == QtCore.Qt.Key.Key_Escape:
            self._deselect_point()
            return
        
        if self.layers:
            if event.key() == QtCore.Qt.Key.Key_D and event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier:
                self._duplicate_layer(self.view_edit.active)
                return
            elif event.key() == QtCore.Qt.Key.Key_Up and event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier:
                if event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier:
                    self._move_layer_to_top(self.view_edit.active)
                else:
                    self._move_layer_up(self.view_edit.active)
                return
            elif event.key() == QtCore.Qt.Key.Key_Down and event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier:
                if event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier:
                    self._move_layer_to_bottom(self.view_edit.active)
                else:
                    self._move_layer_down(self.view_edit.active)
                return
        
        self.view_edit.keyPressEvent(event)
    
    def closeEvent(self, event):
        self._save_settings()
        for layer in self.layers:
            layer.cleanup()
        self.view_proj.close()
        event.accept()


# =============================================================================
# PONTO DE ENTRADA
# =============================================================================
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setApplicationName(PROGRAM_NAME)
    app.setApplicationDisplayName(f"{PROGRAM_NAME} - Mapeamento de Projeção Educacional")
    
    if os.path.exists(ICON_PATH):
        app.setWindowIcon(QtGui.QIcon(ICON_PATH))
    
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
