FROM archlinux:latest

RUN pacman -Syu --noconfirm \
    && pacman -S --noconfirm openrgb \
    && rm -rf /var/cache/pacman/pkg/* /var/lib/pacman/sync/*

ENV QT_QPA_PLATFORM=offscreen

EXPOSE 6742

CMD ["openrgb", "--server", "--server-port", "6742"]
