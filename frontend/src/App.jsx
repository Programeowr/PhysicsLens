import { useEffect, useState } from "react";
import LabPanel from "./components/LabPanel";
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
              <div className="hero-actions">
                <button
                  className="start-btn"
                  type="button"
                  data-magnetic
                  onClick={() => navigate("start")}
                >
                  Get Started
                </button>
              </div>
            </header>

            <main className="home-main">
              <ScenarioGrid />
            </main>
          </div>
        ) : (
          <div className="page-enter" key={transitionKey}>
            <header className="page-head page-head-minimal">
              <button className="text-nav" type="button" data-magnetic onClick={() => navigate("home")}>
                ← Back to Atlas
              </button>
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
