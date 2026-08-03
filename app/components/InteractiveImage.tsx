"use client";

import { useEffect, useState } from "react";

type Props = {
  src: string;
  previewSrc?: string;
  alt: string;
  sizes?: string;
};

export function InteractiveImage({ src, previewSrc, alt, sizes }: Props) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const close = (event: KeyboardEvent) => event.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", close);
    return () => {
      document.body.style.overflow = previous;
      window.removeEventListener("keydown", close);
    };
  }, [open]);

  return (
    <>
      <button className="image-open-button" type="button" onClick={() => setOpen(true)} aria-label={`打开大图：${alt}`}>
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
        <div className="lightbox" role="dialog" aria-modal="true" aria-label={alt} onClick={() => setOpen(false)}>
          <div className="lightbox-toolbar">
            <span>{alt}</span>
            <a href={src} target="_blank" rel="noreferrer" onClick={(event) => event.stopPropagation()}>单独打开原图</a>
            <button type="button" onClick={() => setOpen(false)} aria-label="关闭大图">关闭 ×</button>
          </div>
          <img src={src} alt={alt} onClick={(event) => event.stopPropagation()} />
        </div>
      )}
    </>
  );
}
