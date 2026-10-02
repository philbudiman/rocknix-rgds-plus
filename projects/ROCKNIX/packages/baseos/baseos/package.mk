# SPDX-License-Identifier: GPL-2.0
# RG DS Plus BaseOS (https://github.com/philbudiman/rg-ds-plus-baseos)

PKG_NAME="baseos"
PKG_VERSION="1"
PKG_LICENSE="GPL"
PKG_SITE="https://github.com/philbudiman/rg-ds-plus-baseos"
PKG_URL=""
PKG_SECTION="baseos" # Not "virtual", or makeinstall_target will not run.
PKG_LONGDESC="BaseOS: a small ROCKNIX build that boots straight into its own launcher."
PKG_TOOLCHAIN="manual"

# Added to a BASE_ONLY image when BASEOS=yes (see virtual/image). BASE_ONLY
# leaves out the compositor and sound server, so they are listed here.
PKG_DEPENDS_TARGET="toolchain sway wlr-randr alsa pulseaudio pipewire wireplumber \
                    SDL2 ${VULKAN} dsperate-sa"

makeinstall_target() {
  mkdir -p ${INSTALL}/usr/bin
    cp ${PKG_DIR}/scripts/baseos-launch ${INSTALL}/usr/bin
    chmod 0755 ${INSTALL}/usr/bin/baseos-launch
  mkdir -p ${INSTALL}/usr/share/sway ${INSTALL}/usr/lib/modules-load.d
    cp ${PKG_DIR}/config/sway.config ${INSTALL}/usr/share/sway/config
    echo panfrost > ${INSTALL}/usr/lib/modules-load.d/baseos.conf
}

post_install() {
  enable_service baseos-launcher.service
}
