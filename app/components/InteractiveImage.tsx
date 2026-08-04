"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useLanguage } from "../i18n";

export type GalleryItem = {
  src: string;
  alt: string;
};

type Props = {
  src: string;
  previewSrc?: string;
  videoSrc?: string;
  alt: string;
  sizes?: string;
  gallery?: GalleryItem[];
  initialIndex?: number;
};

export function InteractiveImage({ src, previewSrc, videoSrc, alt, sizes, gallery, initialIndex = 0 }: Props) {
  const { text } = useLanguage();
  const [open, setOpen] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(initialIndex);
  const [zoom, setZoom] = useState(1);
  const [previewPlaying, setPreviewPlaying] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const stageRef = useRef<HTMLDivElement>(null);
  const pendingViewRef = useRef<{ x: number; y: number } | null>(null);
  const items = gallery?.length ? gallery : [{ src, alt }];
  const current = items[currentIndex] ?? items[0];
  const hasMultiple = items.length > 1;

  const startPreview = () => {
    const video = videoRef.current;
    if (!video) return;
    video.currentTime = 0;
    void video.play().then(() => setPreviewPlaying(true)).catch(() => setPreviewPlaying(false));
  };

  const stopPreview = () => {
    const video = videoRef.current;
    if (!video) return;
    video.pause();
    video.currentTime = 0;
    setPreviewPlaying(false);
  };

  const rememberView = useCallback(() => {
    const stage = stageRef.current;
    const image = stage?.querySelector("img");
    if (!stage || !image || zoom === 1) {
      pendingViewRef.current = null;
      return;
    }
    const stageRect = stage.getBoundingClientRect();
    const imageRect = image.getBoundingClientRect();
    pendingViewRef.current = {
      x: (stageRect.left + stage.clientWidth / 2 - imageRect.left) / imageRect.width,
      y: (stageRect.top + stage.clientHeight / 2 - imageRect.top) / imageRect.height,
    };
  }, [zoom]);

  const restoreView = () => {
    const saved = pendingViewRef.current;
    if (!saved) return;
    requestAnimationFrame(() => requestAnimationFrame(() => {
      const stage = stageRef.current;
      const image = stage?.querySelector("img");
      if (!stage || !image) return;
      const stageRect = stage.getBoundingClientRect();
      const imageRect = image.getBoundingClientRect();
      const visibleX = stageRect.left + stage.clientWidth / 2 - imageRect.left;
      const visibleY = stageRect.top + stage.clientHeight / 2 - imageRect.top;
      stage.scrollLeft += saved.x * imageRect.width - visibleX;
      stage.scrollTop += saved.y * imageRect.height - visibleY;
      pendingViewRef.current = null;
    }));
  };

  const move = useCallback((step: number) => {
    rememberView();
    setCurrentIndex((index) => (index + step + items.length) % items.length);
  }, [items.length, rememberView]);

  useEffect(() => {
    if (!open) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const navigate = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
      if (event.key === "ArrowLeft" && hasMultiple) {
        event.preventDefault();
        move(-1);
      }
      if (event.key === "ArrowRight" && hasMultiple) {
        event.preventDefault();
        move(1);
      }
      if (event.key === "+" || event.key === "=") setZoom((value) => value === 1 ? 2 : 4);
      if (event.key === "-") setZoom((value) => value === 4 ? 2 : 1);
      if (event.key === "0") setZoom(1);
    };
    window.addEventListener("keydown", navigate);
    return () => {
      document.body.style.overflow = previous;
      window.removeEventListener("keydown", navigate);
    };
  }, [open, hasMultiple, move]);

  const cycleZoom = () => setZoom((value) => value === 1 ? 2 : value === 2 ? 4 : 1);

  return (
    <>
      <button
        className="image-open-button"
        type="button"
        onMouseEnter={startPreview}
        onMouseLeave={stopPreview}
        onClick={() => { stopPreview(); pendingViewRef.current = null; setCurrentIndex(initialIndex); setZoom(1); setOpen(true); }}
        aria-label={text(`打开大图：${alt}`, `Open full-size image: ${alt}`)}
      >
        {videoSrc ? (
          <>
            <img
              src={previewSrc ?? src}
              srcSet={previewSrc ? `${previewSrc} 800w, ${src} 2560w` : undefined}
              sizes={sizes}
              loading="lazy"
              decoding="async"
              alt={alt}
            />
            <video
              ref={videoRef}
              className={`hover-preview ${previewPlaying ? "is-playing" : ""}`}
              src={videoSrc}
              poster={previewSrc ?? src}
              muted
              loop
              playsInline
              preload="metadata"
              aria-hidden="true"
              tabIndex={-1}
            />
          </>
        ) : (
          <img
            src={previewSrc ?? src}
            srcSet={previewSrc ? `${previewSrc} 800w, ${src} 2560w` : undefined}
            sizes={sizes}
            loading="lazy"
            decoding="async"
            alt={alt}
          />
        )}
        <span className="image-open-hint" aria-hidden="true">{text("查看大图 ↗", "VIEW FULL SIZE ↗")}</span>
      </button>
      {open && (
        <div className="lightbox" role="dialog" aria-modal="true" aria-label={current.alt} onClick={() => setOpen(false)}>
          <div className="lightbox-toolbar">
            <span className="lightbox-title">{current.alt}</span>
            {hasMultiple && <span className="lightbox-counter" aria-live="polite">{currentIndex + 1} / {items.length}</span>}
            <button className="lightbox-zoom" type="button" onClick={(event) => { event.stopPropagation(); cycleZoom(); }} aria-label={text(`放大图片，当前${zoom}倍`, `Magnify image, currently ${zoom}×`)}>⌕ {zoom}×</button>
            <a href={current.src} target="_blank" rel="noreferrer" onClick={(event) => event.stopPropagation()}>{text("单独打开原图", "OPEN ORIGINAL")}</a>
            <button type="button" onClick={() => setOpen(false)} aria-label={text("关闭大图", "Close full-size image")}>{text("关闭 ×", "CLOSE ×")}</button>
          </div>
          {hasMultiple && <button className="lightbox-nav lightbox-prev" type="button" aria-label={text("上一张图片", "Previous image")} onClick={(event) => { event.stopPropagation(); move(-1); }}><span aria-hidden="true">‹</span></button>}
          <div ref={stageRef} className={`lightbox-stage ${zoom > 1 ? "is-zoomed" : ""}`} onClick={() => setOpen(false)}>
            <img key={current.src} src={current.src} alt={current.alt} style={zoom > 1 ? { width: `${zoom * 100}vw` } : undefined} onLoad={restoreView} onClick={(event) => { event.stopPropagation(); cycleZoom(); }} />
          </div>
          {hasMultiple && <button className="lightbox-nav lightbox-next" type="button" aria-label={text("下一张图片", "Next image")} onClick={(event) => { event.stopPropagation(); move(1); }}><span aria-hidden="true">›</span></button>}
        </div>
      )}
    </>
  );
}
