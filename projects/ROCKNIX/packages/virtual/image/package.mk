# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2019-present Team LibreELEC (https://libreelec.tv)

PKG_NAME="image"
PKG_LICENSE="GPL"
PKG_SITE="https://libreelec.tv"

PKG_SECTION="virtual"
PKG_LONGDESC="Root package used to build and create complete image"

PKG_DEPENDS_TARGET="toolchain squashfs-tools:host dosfstools:host fakeroot:host kmod:host \
                    mtools:host populatefs:host libc gcc linux linux-drivers linux-firmware \
                    ${BOOTLOADER} busybox lsof umtprd util-linux usb-modeswitch jq socat \
                    p7zip file initramfs grep util-linux btrfs-progs zstd lz4 empty lzo libzip \
                    bash coreutils system-utils autostart quirks powerstate sdl2notify \
                    gzip six xmlstarlet pyudev dialog network mako-osd rocknix"

PKG_UI="emulationstation es-themes textviewer lowerdeck"

PKG_UI_TOOLS="fbgrab grim"

PKG_GRAPHICS="imagemagick"

PKG_FONTS="corefonts noto-sans-cjk"

PKG_MULTIMEDIA="ffmpeg vlc mpv gmu m8c"

PKG_SOUND="espeak libao"

PKG_SYNC="synctools"

PKG_TOOLS="patchelf i2c-tools evtest"

PKG_DEBUG="debug"

if [ "${DS_ONLY}" = "true" ] && [ "${DEVICE}" = "RK3566" ]; then
  PKG_FONTS="noto-sans-cjk"
  PKG_GRAPHICS=""
  PKG_MULTIMEDIA=""
  PKG_SOUND=""
  PKG_SYNC=""
  PKG_TOOLS="i2c-tools evtest"
fi

if [ "${BASE_ONLY}" = "true" ]
then
  EMULATION_DEVICE=no
  ENABLE_32BIT=no
  PKG_DEPENDS_TARGET+=" ${PKG_TOOLS} ${PKG_FONTS} misc-packages"
elif [ "${DS_ONLY}" = "true" ] && [ "${DEVICE}" = "RK3566" ]
then
  PKG_DEPENDS_TARGET+=" ${PKG_TOOLS} ${PKG_FONTS} ${PKG_UI} ${PKG_UI_TOOLS} misc-packages rgds-launcher"
  [ "${PIPEWIRE_SUPPORT}" = "yes" ] && PKG_DEPENDS_TARGET+=" alsa pulseaudio pipewire wireplumber"
else
  PKG_DEPENDS_TARGET+=" ${PKG_TOOLS} ${PKG_FONTS} ${PKG_SOUND} ${PKG_SYNC} ${PKG_GRAPHICS} ${PKG_UI} ${PKG_UI_TOOLS} ${PKG_MULTIMEDIA} misc-packages"

  # GL demos and tools
  [[ ! -z "${OPENGL_SUPPORT}" ]] && PKG_DEPENDS_TARGET+=" mesa-demos"

  # GLmark2
  [[ ! -z "${OPENGLES_SUPPORT}" ]] && PKG_DEPENDS_TARGET+=" glmark2"

  # Vulkan demos and tools
  [ "${VULKAN_SUPPORT}" = "yes" ] && PKG_DEPENDS_TARGET+=" vkmark"

  # Weston kiosk shell dpms support.
  [ "${WINDOWMANAGER}" = "weston" ] && PKG_DEPENDS_TARGET+=" weston-kiosk-shell-dpms"

  # Sound support
  [ "${PIPEWIRE_SUPPORT}" = "yes" ] && PKG_DEPENDS_TARGET+=" alsa pulseaudio pipewire wireplumber"

fi

# Device is an emulation focused device
if [ "${BASE_ONLY}" != "true" ] && { [ "${EMULATION_DEVICE}" = "yes" ] || { [ "${DS_ONLY}" = "true" ] && [ "${DEVICE}" = "RK3566" ]; }; }; then
  PKG_DEPENDS_TARGET+=" emulators gamesupport"
fi

# Add support for containers
if [ "${DS_ONLY}" != "true" ] || [ "${DEVICE}" != "RK3566" ]; then
  [ "${CONTAINER_SUPPORT}" = "yes" ] && PKG_DEPENDS_TARGET+=" ${PKG_TOOLS} docker"
fi

[ "${DEBUG_PACKAGES}" = "yes" ] && PKG_DEPENDS_TARGET+=" ${PKG_DEBUG}"

# 32Bit package support
[ "${ENABLE_32BIT}" == true ] && PKG_DEPENDS_TARGET+=" lib32"

# Architecture specific tools
[ "${ARCH}" = "x86_64" ] && PKG_DEPENDS_TARGET+=" ryzenadj lm_sensors dmidecode"

# Automounter support
[ "${UDEVIL}" = "yes" ] && PKG_DEPENDS_TARGET+=" udevil"

# EXFAT support
[ "${EXFAT}" = "yes" ] && PKG_DEPENDS_TARGET+=" exfatprogs"

# NFS support
if [ "${DS_ONLY}" != "true" ] || [ "${DEVICE}" != "RK3566" ]; then
  [ "${NFS_SUPPORT}" = "yes" ] && PKG_DEPENDS_TARGET+=" nfs-utils"
fi

# NTFS 3G support
[ "${NTFS3G}" = "yes" ] && PKG_DEPENDS_TARGET+=" ntfs-3g_ntfsprogs"

# Installer support
if { [ "${DS_ONLY}" != "true" ] || [ "${DEVICE}" != "RK3566" ]; } && [ "${INSTALLER_SUPPORT}" = "yes" ]; then
  PKG_DEPENDS_TARGET+=" installer"
fi

# Devtools... (not for Release)
if { [ "${DS_ONLY}" != "true" ] || [ "${DEVICE}" != "RK3566" ]; } && [ "${TESTING}" = "yes" ]; then
  PKG_DEPENDS_TARGET+=" testing"
fi

# OEM packages
if { [ "${DS_ONLY}" != "true" ] || [ "${DEVICE}" != "RK3566" ]; } && [ "${OEM_SUPPORT}" = "yes" ]; then
  PKG_DEPENDS_TARGET+=" oem"
fi

# htop
[ "${HTOP_TOOL}" = "yes" ] && PKG_DEPENDS_TARGET+=" htop"

# btop
[ "${BTOP_TOOL}" = "yes" ] && PKG_DEPENDS_TARGET+=" btop"

# modules packages
[ "${MODULES_PKG}" = "yes" ] && PKG_DEPENDS_TARGET+=" modules"

# Batteryplus voltage-based battery percentage daemon
[ "${BATTERYPLUS_SUPPORT}" = "yes" ] && PKG_DEPENDS_TARGET+=" batteryplus"

# Entware support
if [ "${DS_ONLY}" != "true" ] || [ "${DEVICE}" != "RK3566" ]; then
  mkdir -p ${INSTALL}
  ln -sf /storage/.opt ${INSTALL}/opt
  PKG_DEPENDS_TARGET+=" entware"
fi

true
