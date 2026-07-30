import { useMemo, useRef, useState } from "react";
import "./ReactiveButton.css";

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

const DEFAULT_COLORS = ["#ffffff", "#dce7ff", "#c7d5ff", "#a7bcff", "#5b7cff"];

function randomNoise(amount = 1) {
  return amount / 2 - Math.random() * amount;
}

function getXY(distance, pointIndex, totalPoints) {
  const angle = ((360 + randomNoise(8)) / totalPoints) * pointIndex * (Math.PI / 180);
  return [distance * Math.cos(angle), distance * Math.sin(angle)];
}

function createParticle(index, totalPoints, animationTime, particleDistances, particleRadius, timeVariance) {
  const rotateNoise = randomNoise(particleRadius / 10);

  return {
    start: getXY(particleDistances[0], totalPoints - index, totalPoints),
    end: getXY(particleDistances[1] + randomNoise(7), totalPoints - index, totalPoints),
    time: animationTime * 2 + randomNoise(timeVariance * 2),
    scale: 1 + randomNoise(0.2),
    color: DEFAULT_COLORS[Math.floor(Math.random() * DEFAULT_COLORS.length)],
    rotate:
      rotateNoise > 0
        ? (rotateNoise + particleRadius / 20) * 10
        : (rotateNoise - particleRadius / 20) * 10,
  };
}

export default function ReactiveButton({
  children,
  onClick,
  disabled,
  className = "",
  variant = "primary",
  magnetic = true,
  type = "button",
}) {
  const ref = useRef(null);
  const filterRef = useRef(null);
  const timersRef = useRef([]);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [isActive, setIsActive] = useState(false);
  const [isTriggered, setIsTriggered] = useState(false);

  const style = useMemo(
    () => ({
      transform: `translate(${offset.x}px, ${offset.y}px)`,
      transition: "transform 120ms ease-out",
    }),
    [offset.x, offset.y]
  );

  function handleMove(event) {
    if (!ref.current || disabled) {
      return;
    }
    const rect = ref.current.getBoundingClientRect();
    const x = event.clientX - (rect.left + rect.width / 2);
    const y = event.clientY - (rect.top + rect.height / 2);
    setOffset({ x: clamp(x * 0.08, -8, 8), y: clamp(y * 0.08, -8, 8) });
  }

  function reset() {
    setOffset({ x: 0, y: 0 });
  }

  function clearTimers() {
    timersRef.current.forEach((timer) => window.clearTimeout(timer));
    timersRef.current = [];
  }

  function clearParticles() {
    filterRef.current?.querySelectorAll(".gooey-particle").forEach((particle) => particle.remove());
  }

  function triggerGooey() {
    if (!filterRef.current || disabled) {
      return;
    }

    clearTimers();
    clearParticles();
    setIsActive(false);
    setIsTriggered(false);

    void filterRef.current.offsetWidth;

    const particleCount = 12;
    const animationTime = 340;
    const particleDistances = [70, 10];
    const particleRadius = 90;
    const timeVariance = 140;

    setIsActive(true);
    setIsTriggered(true);

    for (let index = 0; index < particleCount; index += 1) {
      const particleData = createParticle(
        index,
        particleCount,
        animationTime,
        particleDistances,
        particleRadius,
        timeVariance
      );

      const spawnTimer = window.setTimeout(() => {
        if (!filterRef.current) {
          return;
        }

        const particle = document.createElement("span");
        const point = document.createElement("span");

        particle.className = "gooey-particle";
        particle.style.setProperty("--start-x", `${particleData.start[0]}px`);
        particle.style.setProperty("--start-y", `${particleData.start[1]}px`);
        particle.style.setProperty("--end-x", `${particleData.end[0]}px`);
        particle.style.setProperty("--end-y", `${particleData.end[1]}px`);
        particle.style.setProperty("--time", `${particleData.time}ms`);
        particle.style.setProperty("--scale", `${particleData.scale}`);
        particle.style.setProperty("--particle-color", particleData.color);
        particle.style.setProperty("--rotate", `${particleData.rotate}deg`);

        point.className = "gooey-point";
        particle.appendChild(point);
        filterRef.current.appendChild(particle);

        const removeTimer = window.setTimeout(() => {
          particle.remove();
        }, particleData.time);

        timersRef.current.push(removeTimer);
      }, 24);

      timersRef.current.push(spawnTimer);
    }

    const resetTimer = window.setTimeout(() => {
      setIsActive(false);
      setIsTriggered(false);
      clearParticles();
    }, animationTime + timeVariance + 220);

    timersRef.current.push(resetTimer);
  }

  function handleClick(event) {
    triggerGooey();
    onClick?.(event);
  }

  return (
    <button
      ref={ref}
      className={`reactive-btn gooey-btn gooey-btn-${variant} ${isActive ? "is-active" : ""} ${className}`.trim()}
      style={style}
      type={type}
      disabled={disabled}
      data-magnetic={magnetic ? true : undefined}
      onMouseMove={handleMove}
      onMouseLeave={reset}
      onMouseEnter={triggerGooey}
      onFocus={triggerGooey}
      onClick={handleClick}
    >
      <span className={`gooey-surface ${isTriggered ? "is-triggered" : ""}`} ref={filterRef} aria-hidden="true" />
      <span className="gooey-label">{children}</span>
    </button>
  );
}
