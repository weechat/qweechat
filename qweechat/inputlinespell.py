# -*- coding: utf-8 -*-
#
# inputlinespell.py - single line edit with spellcheck for qweechat
#
# Copyright (C) Ricky Brent <ricky@rickybrent.com>
# Copyright for auto-resizing portions of code are held by Kamil Śliwak as
# part of git@github.com:cameel/auto-resizing-text-edit.git and for
# spellcheck portions by John Schember, both under the MIT license.
#
# This file is part of QWeeChat, a Qt remote GUI for WeeChat.
#
# QWeeChat is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# QWeeChat is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with QWeeChat.  If not, see <http://www.gnu.org/licenses/>.
#

import qt_compat
QtCore = qt_compat.import_module('QtCore')
QtGui = qt_compat.import_module('QtGui')
import config
import re
import weechat.color as color

# Spell checker support
try:
    import enchant
except ImportError:
    enchant = None

class InputLineSpell(QtGui.QTextEdit):
    """Chat area."""

    def __init__(self, debug, *args):
        QtGui.QTextEdit.__init__(*(self,) + args)
        self.debug = debug
        self.setFontFamily('monospace')

        self._textcolor = self.textColor()
        self._bgcolor = QtGui.QColor('#FFFFFF')
        self._setcolorcode = {
            'F': (self.setTextColor, self._textcolor),
            'B': (self.setTextBackgroundColor, self._bgcolor)
        }
        self._setfont = {
            '*': self.setFontWeight,
            '_': self.setFontUnderline,
            '/': self.setFontItalic
        }
        self._fontvalues = {
            False: {
                '*': QtGui.QFont.Normal,
                '_': False,
                '/': False
            },
            True: {
                '*': QtGui.QFont.Bold,
                '_': True,
                '/': True
            }
        }
        self._color = color.Color(config.color_options(), self.debug)
        self.initDict()
        # Set height to one line:
        fm = QtGui.QFontMetrics(self.currentFont())
        self.setMinimumHeight(fm.height() + 8)
        size_policy = self.sizePolicy()
        size_policy.setHeightForWidth(True)
        size_policy.setVerticalPolicy(QtGui.QSizePolicy.Preferred)
        self.setSizePolicy(size_policy)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textChanged.connect(lambda: self.updateGeometry())

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        margins = self.contentsMargins()

        if width >= margins.left() + margins.right():
            document_width = width - margins.left() - margins.right()
        else:
            # If specified width can't even fit the margin, no space left.
            document_width = 0
        # Cloning seems wasteful but is the preferred way to in Qt >= 4.
        document = self.document().clone()
        document.setTextWidth(document_width)

        return margins.top() + document.size().height() + margins.bottom()

    def sizeHint(self):
        original_hint = super(InputLineSpell, self).sizeHint()
        return QtCore.QSize(original_hint.width(),
            self.heightForWidth(original_hint.width()))

    def scroll_bottom(self):
        bar = self.verticalScrollBar()
        bar.setValue(bar.maximum())

    def initDict(self, lang=None):
        if enchant:
            if lang == None:
                # Default dictionary based on the current locale.
                try:
                    self.spelldict = enchant.Dict()
                except enchant.DictNotFoundError:
                    self.spelldict = None
            else:
                self.spelldict = enchant.Dict(lang)
        else:
            self.spelldict = None
        self.highlighter = SpellHighlighter(self.document())
        if self.spelldict:
            self.highlighter.setDict(self.spelldict)
            self.highlighter.rehighlight()

    def killDict(self):
        self.highlighter.setDocument(None)
        self.spelldict = None

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.RightButton:
            # Rewrite the mouse event to a left button event so the cursor
            # is moved to the location of the pointer.
            event = QtGui.QMouseEvent(QtCore.QEvent.MouseButtonPress,
                event.pos(), QtCore.Qt.LeftButton, QtCore.Qt.LeftButton,
                QtCore.Qt.NoModifier)
        QtGui.QTextEdit.mousePressEvent(self, event)

    def contextMenuEvent(self, event):
        popup_menu = self.createStandardContextMenu()
        pal = QtGui.QApplication.instance().palette()
        # This fixes Issue 20
        menu_style = """ * { background-color: %s;
                                      color: %s;}
                  """%(unicode(pal.color(QtGui.QPalette.Button).name()),
                      unicode(pal.color(QtGui.QPalette.WindowText).name()))
        popup_menu.setStyleSheet(menu_style)

        # Select the word under the cursor.
        cursor = self.textCursor()
        cursor.select(QtGui.QTextCursor.WordUnderCursor)
        self.setTextCursor(cursor)

        # Check if the selected word is misspelled and offer spelling
        # suggestions if it is.
        if enchant and self.spelldict:
            if self.textCursor().hasSelection():
                text = unicode(self.textCursor().selectedText())
                #Add to dictionary
                #Spell-checker options
                if not self.spelldict.check(text):
                    suggestions = self.spelldict.suggest(text)
                    if len(suggestions) != 0:
                        popup_menu.insertSeparator(popup_menu.actions()[0])
                    topAction = popup_menu.actions()[0]
                    for word in suggestions:
                        action = SpellAction(word, popup_menu)
                        action.correct.connect(self.correctWord)
                        popup_menu.insertAction(topAction, action)
                    popup_menu.insertSeparator(topAction)
                    add = SpellAddAction(text, popup_menu)
                    add.add.connect(self.addWord)
                    popup_menu.insertAction(topAction, add)

        # FIXME: add change dict and disable spellcheck options

        popup_menu.exec_(event.globalPos())

    def addWord(self, word):
        self.spelldict.add(word)
        self.highlighter.rehighlight()

    def correctWord(self, word):
        '''
        Replaces the selected text with word.
        '''
        cursor = self.textCursor()
        cursor.beginEditBlock()

        cursor.removeSelectedText()
        cursor.insertText(word)

        cursor.endEditBlock()

    def killDict(self):
        self.highlighter.setDocument(None)
        self.spelldict = None


class SpellHighlighter(QtGui.QSyntaxHighlighter):

    WORDS = u'(?iu)[\w\']+'

    def __init__(self, *args):
        QtGui.QSyntaxHighlighter.__init__(self, *args)

        self.spelldict = None

    def setDict(self, spelldict):
        self.spelldict = spelldict

    def highlightBlock(self, text):
        if not self.spelldict:
            return

        text = unicode(text)

        format = QtGui.QTextCharFormat()
        format.setUnderlineColor(QtGui.QColor('red'))
        format.setUnderlineStyle(QtGui.QTextCharFormat.DotLine)

        for word_object in re.finditer(self.WORDS, text):
            if not self.spelldict.check(word_object.group()):
                self.setFormat(word_object.start(),
                    word_object.end() - word_object.start(), format)

class SpellAction(QtGui.QAction):

    '''
    A special QAction that returns the text in a signal.
    '''

    correct = qt_compat.Signal(unicode)

    def __init__(self, *args):
        QtGui.QAction.__init__(self, *args)

        self.triggered.connect(lambda x: self.correct.emit(
            unicode(self.text())))

class SpellAddAction(QtGui.QAction):

    '''
    An action to add the given word to a dictionary.
    '''

    add = qt_compat.Signal(unicode)

    def __init__(self, word, *args):
        QtGui.QAction.__init__(self, "Add to dictionary", *args)
        self._word = word
        self.triggered.connect(lambda x: self.add.emit(
            unicode(self._word)))

