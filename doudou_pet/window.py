from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QActionGroup, QCursor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QMenu, QSystemTrayIcon, QWidget


class PetWindow(QWidget):
    def __init__(self, skins, settings, on_change=None):
        self.on_top = settings.get('always_on_top', True)
        super().__init__(None, self.flags_for(self.on_top))
        self.skins = skins
        self.on_change = on_change
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle('豆豆桌宠')
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setFixedSize(168, 152)
        self._pixmaps = {}
        self._press = None
        self._dragging = False
        self._index = 0
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._next_frame)
        self.bubble = QLabel(self)
        self._bubble_timer = QTimer(self)
        self._bubble_timer.setSingleShot(True)
        self._bubble_timer.timeout.connect(self.bubble.hide)
        self.bubble.setTextFormat(Qt.TextFormat.PlainText)
        self.bubble.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.bubble.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bubble.setWordWrap(True)
        self.bubble.setGeometry(3, 2, 162, 37)
        self.bubble.setStyleSheet('background:#fffdf5;color:#382e27;border:2px solid #614839;border-radius:6px;font-weight:bold;')
        self.pet_menu = QMenu(self)
        self.wardrobe = self.pet_menu.addMenu('豆豆衣柜')
        self._wardrobe_group = QActionGroup(self)
        self._choices = {}
        for ident in sorted(skins, key=lambda k: (['classic','doctor','programmer','chef'].index(k) if k in ('classic','doctor','programmer','chef') else 4)):
            skin = skins[ident]
            action = self.wardrobe.addAction(skin.name)
            action.setCheckable(True)
            self._wardrobe_group.addAction(action)
            action.triggered.connect(lambda checked, key=ident: self.set_skin(key))
            self._choices[ident] = action
        self.top_action = self.pet_menu.addAction('保持置顶')
        self.top_action.setCheckable(True)
        self.top_action.setChecked(self.on_top)
        self.top_action.toggled.connect(self.set_top)
        self.relocate_action = self.pet_menu.addAction('找回到主屏幕', self.relocate)
        self.visibility_action = self.pet_menu.addAction('隐藏豆豆', self.toggle_visible)
        self.pet_menu.addSeparator()
        self.exit_action = self.pet_menu.addAction('退出豆豆', self.quit)
        self.tray = QSystemTrayIcon(self)
        self.tray.setContextMenu(self.pet_menu)
        self.tray.setToolTip('豆豆桌宠')
        self.tray.activated.connect(self._tray_activated)
        ident = settings.get('skin')
        if ident not in skins:
            ident = 'classic' if 'classic' in skins else next(iter(skins))
        self.set_skin(ident, persist=False)
        position = settings.get('position')
        self.move(self.clamp(QPoint(*position)) if position else self.home())
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()
        else:
            self.visibility_action.setEnabled(False)

    @staticmethod
    def flags_for(on_top):
        result = Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint
        return result | Qt.WindowType.WindowStaysOnTopHint if on_top else result

    def home(self):
        rect = QApplication.primaryScreen().availableGeometry()
        return QPoint(rect.right() + 1 - self.width() - 16, rect.bottom() + 1 - self.height() - 12)

    def clamp(self, pos):
        screen = QApplication.screenAt(pos + self.rect().center()) or QApplication.primaryScreen()
        rect = screen.availableGeometry()
        return QPoint(max(rect.left(), min(pos.x(), rect.right() + 1 - self.width())),
                      max(rect.top(), min(pos.y(), rect.bottom() + 1 - self.height())))

    def remember(self):
        if self.on_change:
            self.on_change(dict(skin=self.skin.id, position=[self.x(), self.y()], always_on_top=self.on_top))

    def _pixmap(self, path):
        if path not in self._pixmaps:
            original = QPixmap(str(path))
            image = original.toImage()
            if not original.isNull():
                # Use one anchor per costume, so a moving prop never shifts the pet.
                result = original
            else:
                result = QPixmap()
            self._pixmaps[path] = result
        return self._pixmaps[path]

    def set_skin(self, ident, persist=True):
        self.skin = self.skins[ident]
        self._choices[ident].setChecked(True)
        pixmap = self._pixmap(self.skin.idle)
        self.tray.setIcon(QIcon(pixmap))
        self.setWindowIcon(QIcon(pixmap))
        self._reset_animation()
        if persist:
            self.remember()

    def _reset_animation(self):
        self._timer.stop()
        self.frame_path = self.skin.idle
        self._bubble_timer.stop()
        self.bubble.hide()
        self.update()

    def _interact(self):
        self._index = -1
        self.bubble.setText(self.skin.bubble)
        self.bubble.setVisible(bool(self.skin.bubble))
        self._bubble_timer.start(max(1500, sum(frame.ms for frame in self.skin.interact)))
        self._next_frame()

    def _next_frame(self):
        self._index += 1
        if self._index == len(self.skin.interact):
            self.frame_path = self.skin.idle
            self.update()
            return
        frame = self.skin.interact[self._index]
        self.frame_path = frame.path
        self.update()
        self._timer.start(frame.ms)

    def paintEvent(self, event):
        pixmap = self._pixmap(self.frame_path)
        if pixmap.isNull():
            return
        painter = QPainter(self)
        factor = min(1.0, self.width() / pixmap.width(), 113 / pixmap.height())
        if pixmap.width() >= 320:
            factor = 0.4
        w, h = round(pixmap.width() * factor), round(pixmap.height() * factor)
        anchor = round((224 if pixmap.height() == 272 else 208) * factor) if pixmap.width() == 320 else h // 2 + 14
        scaled = pixmap.scaled(w, h, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.FastTransformation)
        y = self.height() - 14 - anchor if pixmap.width() == 320 else self.height() // 2 - h // 2
        painter.drawPixmap((self.width() - w) // 2, y, scaled)
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._press = (event.globalPosition().toPoint(), self.pos())
            self._dragging = False
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._press is None:
            return
        start, origin = self._press
        delta = event.globalPosition().toPoint() - start
        if self._dragging or delta.manhattanLength() >= QApplication.startDragDistance():
            self._dragging = True
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self.move(origin + delta)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.pet_menu.popup(event.globalPosition().toPoint())
        if event.button() != Qt.MouseButton.LeftButton or self._press is None:
            return
        self._press = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        if self._dragging:
            self.move(self.clamp(self.pos()))
            self.remember()
        else:
            self._interact()

    def set_top(self, checked):
        visible = self.isVisible()
        point = self.pos()
        self.on_top = checked
        self.setWindowFlags(self.flags_for(checked))
        self.move(point)
        if visible:
            self.show()
        self.remember()

    def toggle_visible(self):
        if self.isVisible():
            self.hide()
            self.visibility_action.setText('显示豆豆')
        else:
            self.show()
            self.visibility_action.setText('隐藏豆豆')

    def relocate(self):
        self.move(self.home())
        if not self.isVisible():
            self.toggle_visible()
        self.remember()

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.toggle_visible()

    def quit(self):
        self.close()
        QApplication.quit()

    def closeEvent(self, event):
        self._timer.stop()
        self.tray.hide()
        super().closeEvent(event)
