import { useMemo, useRef, useState } from "react";

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

export default function ReactiveButton({ children, onClick, disabled }) {
  const ref = useRef(null);
  const [offset, setOffset] = useState({ x: 0, y: 0 });

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

  return (
    <button
      ref={ref}
      className="reactive-btn"
      style={style}
      type="button"
      disabled={disabled}
      onMouseMove={handleMove}
      onMouseLeave={reset}
      onClick={onClick}
    >
      {children}
    </button>
  );
}
