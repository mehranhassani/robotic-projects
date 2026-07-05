(() => {
  const wsUrl = `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`;
  let ws;
  let speed = 0.6;
  let activeDir = null;
  let reconnectTimer;

  const $ = (id) => document.getElementById(id);

  function connect() {
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      $("conn-status").textContent = "Online";
      $("conn-status").className = "badge online";
      send({ action: "status" });
    };

    ws.onclose = () => {
      $("conn-status").textContent = "Offline";
      $("conn-status").className = "badge offline";
      clearTimeout(reconnectTimer);
      reconnectTimer = setTimeout(connect, 2000);
    };

    ws.onmessage = (ev) => {
      const data = JSON.parse(ev.data);
      updateUI(data);
    };
  }

  function send(msg) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(msg));
    }
  }

  function updateUI(data) {
    if (data.battery_v != null) $("battery").textContent = `${data.battery_v} V`;
    if (data.mock) {
      $("mock-badge").classList.remove("hidden");
    }
    if (data.distance_cm != null) $("distance").textContent = `${data.distance_cm} cm`;
    if (data.light) {
      $("light").textContent = `${data.light.left} / ${data.light.right}`;
    }
    if (data.line) {
      const l = data.line;
      $("line").textContent = `${l.left} / ${l.center} / ${l.right}`;
    }
  }

  function drive(direction) {
    if (direction === "stop") {
      send({ action: "stop" });
      return;
    }
    send({ action: "drive", direction, speed });
  }

  document.querySelectorAll(".dpad-btn").forEach((btn) => {
    const dir = btn.dataset.dir;

    const start = (e) => {
      e.preventDefault();
      btn.classList.add("active");
      activeDir = dir;
      drive(dir);
    };

    const end = () => {
      btn.classList.remove("active");
      if (activeDir === dir && dir !== "stop") {
        send({ action: "stop" });
      }
      activeDir = null;
    };

    btn.addEventListener("mousedown", start);
    btn.addEventListener("mouseup", end);
    btn.addEventListener("mouseleave", end);
    btn.addEventListener("touchstart", start, { passive: false });
    btn.addEventListener("touchend", end);
    btn.addEventListener("touchcancel", end);
  });

  $("speed").addEventListener("input", (e) => {
    speed = parseFloat(e.target.value);
  });

  document.querySelectorAll(".mode-buttons button").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".mode-buttons button").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      send({ action: "mode", mode: btn.dataset.mode });
    });
  });

  $("servo").addEventListener("input", (e) => {
    send({ action: "servo", channel: "0", angle: parseInt(e.target.value, 10) });
  });

  let buzzerOn = false;
  $("buzzer").addEventListener("click", () => {
    buzzerOn = !buzzerOn;
    $("buzzer").classList.toggle("on", buzzerOn);
    send({ action: "buzzer", on: buzzerOn });
  });

  connect();

  setInterval(() => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      send({ action: "status" });
    }
  }, 1000);
})();
