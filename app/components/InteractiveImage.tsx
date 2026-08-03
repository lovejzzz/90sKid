"use client";

import { useEffect, useState } from "react";

export type GalleryItem = {
  src: string;
  alt: string;
};

type Props = {
  src: string;
  previewSrc?: string;
  alt: string;
  sizes?: string;
  gallery?: GalleryItem[];
  initialIndex?: number;
};

export function InteractiveImage({ src, previewSrc, alt, sizes, gallery, initialIndex = 0 }: Props) {
  const [open, setOpen] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(initialIndex);
  const [zoom, setZoom] = useState(1);
  const items = gallery?.length ? gallery : [{ src, alt }];
  const current = items[currentIndex] ?? items[0];
  const hasMultiple = items.length > 1;

  useEffect(() => {
    if (!open) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const navigate = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
      if (event.key === "ArrowLeft" && hasMultiple) {
        event.preventDefault();
        setZoom(1);
        setCurrentIndex((index) => (index - 1 + items.length) % items.length);
      }
      if (event.key === "ArrowRight" && hasMultiple) {
        event.preventDefault();
        setZoom(1);
        setCurrentIndex((index) => (index + 1) % items.length);
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
  }, [open, hasMultiple, items.length]);

  const move = (step: number) => {
    setZoom(1);
    setCurrentIndex((index) => (index + step + items.length) % items.length);
  };

  const cycleZoom = () => setZoom((value) => value === 1 ? 2 : value === 2 ? 4 : 1);

  return (
    <>
      <button className="image-open-button" type="button" onClick={() => { setCurrentIndex(initialIndex); setZoom(1); setOpen(true); }} aria-label={`打开大图：${alt}`}>
        <img
          src={previewSrc ?? src}
          srcSet={previewSrc ? `${previewSrc} 800w, ${src} 2560w` : undefined}
          sizes={sizes}
          loading="lazy"
          decoding="async"
          alt={alt}
        />
        <span className="image-open-hint" aria-hidden="true">查看大图 ↗</span>
      </button>
      {open && (
        <div className="lightbox" role="dialog" aria-modal="true" aria-label={current.alt} onClick={() => setOpen(false)}>
          <div className="lightbox-toolbar">
            <span className="lightbox-title">{current.alt}</span>
            {hasMultiple && <span className="lightbox-counter" aria-live="polite">{currentIndex + 1} / {items.length}</span>}
            <button className="lightbox-zoom" type="button" onClick={(event) => { event.stopPropagation(); cycleZoom(); }} aria-label={`放大图片，当前${zoom}倍`}>⌕ {zoom}×</button>
            <a href={current.src} target="_blank" rel="noreferrer" onClick={(event) => event.stopPropagation()}>单独打开原图</a>
            <button type="button" onClick={() => setOpen(false)} aria-label="关闭大图">关闭 ×</button>
          </div>
          {hasMultiple && <button className="lightbox-nav lightbox-prev" type="button" aria-label="上一张图片" onClick={(event) => { event.stopPropagation(); move(-1); }}><span aria-hidden="true">‹</span></button>}
          <div className={`lightbox-stage ${zoom > 1 ? "is-zoomed" : ""}`} onClick={() => setOpen(false)}>
            <img key={current.src} src={current.src} alt={current.alt} style={zoom > 1 ? { width: `${zoom * 100}vw` } : undefined} onClick={(event) => { event.stopPropagation(); cycleZoom(); }} />
          </div>
          {hasMultiple && <button className="lightbox-nav lightbox-next" type="button" aria-label="下一张图片" onClick={(event) => { event.stopPropagation(); move(1); }}><span aria-hidden="true">›</span></button>}
        </div>
      )}
    </>
  );
}
