import { useEffect, useState } from "react";
import LabPanel from "./components/LabPanel";
import ReactiveButton from "./components/ReactiveButton";
import ScenarioGrid from "./components/ScenarioGrid";
import { MagneticCursor } from "./components/ui/magnetic-cursor";

export default function App() {
  const [route, setRoute] = useState(() => (window.location.pathname === "/start" ? "start" : "home"));
  const [transitionKey, setTransitionKey] = useState(0);

  useEffect(() => {
    function handlePopState() {
      setRoute(window.location.pathname === "/start" ? "start" : "home");
      setTransitionKey((k) => k + 1);
    }

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  function navigate(nextRoute) {
    const nextPath = nextRoute === "start" ? "/start" : "/";
    if (window.location.pathname !== nextPath) {
      window.history.pushState({}, "", nextPath);
    }
    setRoute(nextRoute);
    setTransitionKey((k) => k + 1);
  }

  return (
    <MagneticCursor cursorColor="#ffffff" blendMode="exclusion" cursorSize={30} routeKey={route}>
      <div className="page-shell">
        <div className="noise-layer" aria-hidden="true" />
        {route === "home" ? (
          <div className="page-enter" key={transitionKey}>
            <header className="hero" id="home">
              <div className="hero-motion" aria-hidden="true">
                <span className="hero-orbit hero-orbit-a" />
                <span className="hero-orbit hero-orbit-b" />
                <span className="hero-core" />
              </div>
              <p className="kicker">PhysicsLens / deterministic diagrams</p>
              <h1>
                PhysicsLens
                <br />
                <span>Diagram Atlas</span>
              </h1>
              <p className="hero-copy">
                Explore supported scenarios below. When you're ready, move into
                the workspace to input your problem and generate precise force diagrams.
              </p>
              <div className="hero-pills" aria-label="Project highlights">
                <span data-magnetic className="hero-pill">Deterministic</span>
                <span data-magnetic className="hero-pill">Local API</span>
                <span data-magnetic className="hero-pill">SVG output</span>
              </div>
              <div className="hero-actions">
                <ReactiveButton className="start-btn" variant="primary" onClick={() => navigate("start")}>
                  Get Started
                </ReactiveButton>
              </div>
            </header>

            <main className="home-main">
              <ScenarioGrid />
            </main>
          </div>
        ) : (
          <div className="page-enter" key={transitionKey}>
            <header className="page-head page-head-minimal">
              <ReactiveButton className="text-nav" variant="subtle" onClick={() => navigate("home")}>
                {"<- Back to Atlas"}
              </ReactiveButton>
              <h1>
                <span>Generate Your Diagram</span>
              </h1>
            </header>

            <main className="start-main">
              <LabPanel />
            </main>
          </div>
        )}
      </div>
    </MagneticCursor>
  );
}
