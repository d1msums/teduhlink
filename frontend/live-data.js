(() => {
  const streams = {
    weather: {
      url: "/api/stops/A/weather",
      data: null,
      receivedAt: 0
    },
    crowding: {
      url: "/api/stops/A/occupancy",
      data: null,
      receivedAt: 0
    }
  };

  function setText(id, text) {
    const element = document.getElementById(id);
    if (element) element.textContent = text;
  }

  function isFresh(stream) {
    if (!stream.data || stream.data.status === "unknown") {
      return false;
    }

    return (
      performance.now() - stream.receivedAt <
      Number(stream.data.valid_for_ms || 0)
    );
  }

  function ageText(stream) {
    const age = stream.data?.observation_age_ms;

    if (typeof age !== "number") {
      return "No recent observation";
    }

    const elapsed = performance.now() - stream.receivedAt;
    const seconds = Math.floor((age + elapsed) / 1000);

    return `Observation age: ${seconds} seconds`;
  }

  function render() {
    const weather = streams.weather;
    const crowding = streams.crowding;

    if (isFresh(weather)) {
      setText(
        "live-weather",
        weather.data.status === "wet"
          ? "💧 Wet detected"
          : "Dry detected"
      );
    } else {
      setText("live-weather", "Wetness unavailable");
    }

    setText("live-weather-age", ageText(weather));

    if (
      isFresh(crowding) &&
      Number.isInteger(crowding.data.estimated_count)
    ) {
      const count = crowding.data.estimated_count;

      const category =
        count === 0
          ? "No people detected"
          : count < 3
            ? "Some people detected"
            : "Busy";

      setText(
        "live-crowding",
        `${category} · Estimated people: ${count}`
      );
    } else {
      setText("live-crowding", "Crowding unavailable");
    }

    setText("live-crowding-age", ageText(crowding));
  }

  async function poll(stream) {
    try {
      const response = await fetch(stream.url, {
        cache: "no-store",
        signal: AbortSignal.timeout(4000)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      stream.data = await response.json();
      stream.receivedAt = performance.now();
    } catch (error) {
      console.warn("Reading unavailable:", stream.url, error);
      stream.data = null;
    }

    render();
    setTimeout(() => poll(stream), 2000);
  }

  poll(streams.weather);
  poll(streams.crowding);

  // Expire old observations even if no new response arrives.
  setInterval(render, 500);
})();