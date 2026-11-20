from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QActionGroup, QFontMetrics, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QMenu, QSystemTrayIcon, QWidget


class PetWindow(QWidget):
    # Asset contract: sprites are 320 px wide and leave a transparent margin under the
    # feet, so the baseline sits at y=208 (240 px tall) or y=224 (272 px tall).
    SPRITE_WIDTH = 320
    SPRITE_SCALE = 0.4
    SPRITE_FIT_HEIGHT = 113
    PET_MARGIN_BOTTOM = 14
    WIDTH = 168
    # Room reserved under the bubble; the pet is painted against the window bottom, so
    # growing the bubble pushes the top edge up and leaves the hamster where it was.
    PET_AREA_HEIGHT = 115
    BUBBLE_MARGIN = 3
    BUBBLE_TOP = 2
    BUBBLE_PADDING = 6
    BUBBLE_MIN_HEIGHT = 37
    BUBBLE_MAX_HEIGHT = 190

    def __init__(self, skins, settings, on_change=None, tray_available=None):
        self.on_top = settings.get('always_on_top', True)
        super().__init__(None, self.flags_for(self.on_top))
        self.skins = skins
        self.on_change = on_change
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle('豆豆桌宠')
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setFixedSize(self.width_for_bubble(), self.height_for_bubble(self.BUBBLE_MIN_HEIGHT))
        self._pixmaps = {}
        self._press = None
        self._dragging = False
        self._index = 0
        self._anchor_bottom = None
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._next_frame)
        self.bubble = QLabel(self)
        self._bubble_timer = QTimer(self)
        self._bubble_timer.setSingleShot(True)
        self._bubble_timer.timeout.connect(self._hide_bubble)
        self.bubble.setTextFormat(Qt.TextFormat.PlainText)
        self.bubble.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.bubble.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bubble.setWordWrap(True)
        self.bubble.setStyleSheet('background:#fffdf5;color:#382e27;border:2px solid #614839;border-radius:6px;font-weight:bold;')
        self._layout_bubble('')
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
        self._sync_anchor()
        self.tray_available = (QSystemTrayIcon.isSystemTrayAvailable()
                               if tray_available is None else bool(tray_available))
        if self.tray_available:
            self.tray.show()
        else:
            # 没有托盘就得靠隐藏菜单之外的办法找回豆豆，所以直接禁掉隐藏
            self.visibility_action.setEnabled(False)

    @classmethod
    def width_for_bubble(cls):
        return cls.WIDTH

    @classmethod
    def height_for_bubble(cls, bubble_height):
        return cls.PET_AREA_HEIGHT + bubble_height

    def bubble_height_for(self, text):
        """Height the bubble needs for `text`, clamped to the layout limits."""
        if not text:
            return self.BUBBLE_MIN_HEIGHT
        width = self.WIDTH - 2 * self.BUBBLE_MARGIN - 2 * self.BUBBLE_PADDING
        needed = QFontMetrics(self.bubble.font()).boundingRect(
            0, 0, width, 10_000, Qt.TextFlag.TextWordWrap, text).height() + 2 * self.BUBBLE_PADDING
        return max(self.BUBBLE_MIN_HEIGHT, min(self.BUBBLE_MAX_HEIGHT, needed))

    def _layout_bubble(self, text):
        """Fit the bubble to its text, keeping the pet's resting place on screen."""
        height = self.bubble_height_for(text)
        width = self.WIDTH - 2 * self.BUBBLE_MARGIN
        self.bubble.setGeometry(self.BUBBLE_MARGIN, self.BUBBLE_TOP, width, height)
        total = self.height_for_bubble(height)
        collapsed = height == self.BUBBLE_MIN_HEIGHT
        if self._anchor_bottom is None:
            self._anchor_bottom = self.y() + self.height()
        if self.height() == total:
            if collapsed:
                # Resting: the pet's baseline is the current bottom edge.
                self._anchor_bottom = self.y() + total
            return
        self.setFixedSize(self.WIDTH, total)
        self.move(self.clamp(QPoint(self.x(), self._anchor_bottom - total)))
        if collapsed:
            self._anchor_bottom = self.y() + total

    def collapsed_position(self):
        """Top-left corner the window takes when no bubble is showing."""
        if self._anchor_bottom is None:
            return self.pos()
        return QPoint(self.x(), self._anchor_bottom - self.height_for_bubble(self.BUBBLE_MIN_HEIGHT))

    def _hide_bubble(self):
        self.bubble.hide()
        self._layout_bubble('')

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
            # Save the collapsed position: a bubble may have grown the window upwards,
            # and that offset must not leak into the next launch.
            point = self.collapsed_position()
            self.on_change(dict(skin=self.skin.id, position=[point.x(), point.y()], always_on_top=self.on_top))

    def _pixmap(self, path):
        if path not in self._pixmaps:
            self._pixmaps[path] = QPixmap(str(path))
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
        self._hide_bubble()
        self.update()

    def _interact(self):
        self._index = -1
        text = self.skin.bubble
        self.bubble.setText(text)
        self._layout_bubble(text)
        self.bubble.setVisible(bool(text))
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
        factor = min(1.0, self.width() / pixmap.width(), self.SPRITE_FIT_HEIGHT / pixmap.height())
        tall_sprite = pixmap.width() >= self.SPRITE_WIDTH
        if tall_sprite:
            factor = self.SPRITE_SCALE
        w, h = round(pixmap.width() * factor), round(pixmap.height() * factor)
        if tall_sprite:
            # Anchor the feet to the baseline instead of the canvas bottom.
            baseline = 224 if pixmap.height() > 240 else 208
            anchor = round(baseline * factor)
            y = self.height() - self.PET_MARGIN_BOTTOM - anchor
        else:
            y = self.height() // 2 - h // 2
        scaled = pixmap.scaled(w, h, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.FastTransformation)
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
            self._sync_anchor()
            self.remember()
        else:
            self._interact()

    def _sync_anchor(self):
        """The pet is painted against the window bottom, so that edge follows the user."""
        self._anchor_bottom = self.y() + self.height()

    def set_top(self, checked):
        visible = self.isVisible()
        point = self.pos()
        self.on_top = checked
        self.setWindowFlags(self.flags_for(checked))
        self.move(point)
        self._sync_anchor()
        if visible:
            self.show()
        self.remember()

    def toggle_visible(self):
        if self.isVisible():
            if not self.tray_available:
                return  # 没有托盘图标，藏起来就再也点不到了
            self.hide()
            self.visibility_action.setText('显示豆豆')
        else:
            self.show()
            self.visibility_action.setText('隐藏豆豆')

    def relocate(self):
        self.move(self.home())
        self._sync_anchor()
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
