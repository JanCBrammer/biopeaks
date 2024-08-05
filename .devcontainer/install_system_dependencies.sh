#!/bin/bash

# Install missing dependencies for PySide6.
# https://doc.qt.io/qt-6/linux-requirements.html
# https://doc.qt.io/qt-6/linux.html
apt-get update
apt-get install -y build-essential \
libgl1-mesa-dev \
libfontconfig1-dev \
libfreetype-dev \
libx11-dev \
libx11-xcb-dev \
libxext-dev \
libxfixes-dev \
libxi-dev \
libxrender-dev \
libxcb1-dev \
libxcb-cursor-dev \
libxcb-glx0-dev \
libxcb-keysyms1-dev \
libxcb-image0-dev \
libxcb-shm0-dev \
libxcb-icccm4-dev \
libxcb-sync-dev \
libxcb-xfixes0-dev \
libxcb-shape0-dev \
libxcb-randr0-dev \
libxcb-render-util0-dev \
libxcb-util-dev \
libxcb-xinerama0-dev \
libxcb-xkb-dev \
libxkbcommon-dev \
libxkbcommon-x11-dev \
libdbus-glib-1-2
# Install xvfb for headless testing.
apt-get install -y xvfb
