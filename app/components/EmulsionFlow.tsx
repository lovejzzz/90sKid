"use client";

import { useEffect, useRef } from "react";

type Particle = {
  x: number;
  y: number;
  px: number;
  py: number;
  speed: number;
  radius: number;
  tone: number;
  life: number;
};

function seeded(index: number, salt: number) {
  const value = Math.sin(index * 127.1 + salt * 311.7) * 43758.5453;
  return value - Math.floor(value);
}

export function EmulsionFlow() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const context = canvas.getContext("2d", { alpha: true });
    if (!context) return;

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    let animationFrame = 0;
    let previous = 0;
    let visible = !document.hidden;
    let width = 360;
    let height = 210;
    const count = window.innerWidth < 680 ? 82 : 138;
    const particles: Particle[] = Array.from({ length: count }, (_, index) => ({
      x: seeded(index, 1) * width,
      y: seeded(index, 2) * height,
      px: 0,
      py: 0,
      speed: 0.26 + seeded(index, 3) * 0.62,
      radius: 0.35 + seeded(index, 4) * 1.7,
      tone: seeded(index, 5),
      life: seeded(index, 6),
    }));

    const resize = () => {
      const bounds = canvas.getBoundingClientRect();
      width = Math.max(280, Math.round(bounds.width / 4));
      height = Math.max(160, Math.round(bounds.height / 4));
      canvas.width = width;
      canvas.height = height;
      context.fillStyle = "#11120f";
      context.fillRect(0, 0, width, height);
      particles.forEach((particle, index) => {
        particle.x = seeded(index, 1) * width;
        particle.y = seeded(index, 2) * height;
        particle.px = particle.x;
        particle.py = particle.y;
      });
    };

    const reset = (particle: Particle, index: number, time: number) => {
      const edge = seeded(index + Math.floor(time * 0.001), 8);
      particle.x = edge < 0.58 ? -4 : seeded(index, 9) * width;
      particle.y = edge < 0.58 ? seeded(index + Math.floor(time), 10) * height : height + 4;
      particle.px = particle.x;
      particle.py = particle.y;
      particle.life = 0;
    };

    const draw = (time: number) => {
      const seconds = time * 0.001;
      context.globalCompositeOperation = "source-over";
      context.fillStyle = reducedMotion.matches ? "rgba(13,14,12,.14)" : "rgba(13,14,12,.045)";
      context.fillRect(0, 0, width, height);

      context.globalCompositeOperation = "screen";
      particles.forEach((particle, index) => {
        particle.px = particle.x;
        particle.py = particle.y;
        const nx = particle.x / width;
        const ny = particle.y / height;
        const field =
          1.45 * Math.sin(ny * 8.2 + seconds * 0.17) +
          0.82 * Math.cos(nx * 6.4 - seconds * 0.11) +
          0.48 * Math.sin((nx + ny) * 13.0 + seconds * 0.07);
        const angle = field + 0.38 * Math.sin(seconds * 0.13 + index);
        particle.x += (0.72 + Math.cos(angle) * 0.58) * particle.speed;
        particle.y += (Math.sin(angle) * 0.66 - 0.10) * particle.speed;
        particle.life += 0.0025 * particle.speed;

        if (
          particle.x > width + 7 || particle.y < -7 || particle.y > height + 7 ||
          particle.life > 1.2
        ) reset(particle, index, time);

        const alpha = 0.055 + 0.16 * Math.sin(Math.min(particle.life, 1) * Math.PI);
        const color = particle.tone < 0.78
          ? `rgba(217,151,49,${alpha})`
          : particle.tone < 0.91
            ? `rgba(57,130,139,${alpha * 0.55})`
            : `rgba(151,65,77,${alpha * 0.48})`;
        context.strokeStyle = color;
        context.lineWidth = particle.radius;
        context.beginPath();
        context.moveTo(particle.px, particle.py);
        context.lineTo(particle.x, particle.y);
        context.stroke();

        if (index % 11 === 0) {
          context.fillStyle = color;
          context.beginPath();
          context.arc(particle.x, particle.y, particle.radius * 0.72, 0, Math.PI * 2);
          context.fill();
        }
      });
      context.globalCompositeOperation = "source-over";
    };

    const animate = (time: number) => {
      if (visible && (time - previous > 1000 / 24 || reducedMotion.matches)) {
        draw(time);
        previous = time;
      }
      if (!reducedMotion.matches) animationFrame = requestAnimationFrame(animate);
    };

    const visibility = () => {
      visible = !document.hidden;
    };
    const motionChange = () => {
      cancelAnimationFrame(animationFrame);
      draw(performance.now());
      if (!reducedMotion.matches) animationFrame = requestAnimationFrame(animate);
    };

    resize();
    draw(0);
    window.addEventListener("resize", resize);
    document.addEventListener("visibilitychange", visibility);
    reducedMotion.addEventListener("change", motionChange);
    if (!reducedMotion.matches) animationFrame = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(animationFrame);
      window.removeEventListener("resize", resize);
      document.removeEventListener("visibilitychange", visibility);
      reducedMotion.removeEventListener("change", motionChange);
    };
  }, []);

  return <canvas ref={canvasRef} className="emulsion-flow" aria-hidden="true" />;
}
