# SPDX-License-Identifier: GPL-2.0

PKG_NAME="rgds-launcher"
PKG_VERSION="1"
PKG_LICENSE="GPLv2"
PKG_SITE="https://github.com/ROCKNIX"
PKG_URL=""
PKG_DEPENDS_TARGET="toolchain SDL2 SDL2_ttf"
PKG_LONGDESC="RG DS Plus launcher preview"
PKG_TOOLCHAIN="make"

makeinstall_target() {
  mkdir -p ${INSTALL}/usr/bin
  cp -a ${PKG_BUILD}/rgds-launcher ${INSTALL}/usr/bin
}
