(() => {
  const wsUrl = `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`;
  let ws;
  let speed = 0.6;
  let activeDir = null;
  let reconnectTimer;
  let servoTimer;

  const $ = (id) => document.getElementById(id);

  function connect() {
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      $("conn-status").textContent = "Online";
      $("conn-status").className = "badge online";
      send({ action: "status" });
      setServo("0", parseInt($("servo-pan").value, 10), false);
      setServo("1", parseInt($("servo-tilt").value, 10), false);
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

  async function setServo(channel, angle, useRestFallback = true) {
    angle = Math.max(30, Math.min(150, angle));
    const isPan = channel === "0";
    const slider = isPan ? $("servo-pan") : $("servo-tilt");
    const label = isPan ? $("pan-angle") : $("tilt-angle");
    slider.value = String(angle);
    label.textContent = `${angle} deg`;

    send({ action: "mode", mode: "manual" });
    send({ action: "servo", channel, angle });

    if (useRestFallback) {
      clearTimeout(servoTimer);
      servoTimer = setTimeout(async () => {
        try {
          await fetch("/api/servo", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ channel, angle }),
          });
        } catch (_) {
          /* ws path is primary */
        }
      }, 80);
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
    if (data.pan_angle != null) {
      $("pan-angle").textContent = `${data.pan_angle} deg`;
    }
    if (data.tilt_angle != null) {
      $("tilt-angle").textContent = `${data.tilt_angle} deg`;
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

  document.querySelectorAll(".pan-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      setServo("0", parseInt(btn.dataset.pan, 10));
    });
  });

  document.querySelectorAll(".tilt-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      setServo("1", parseInt(btn.dataset.tilt, 10));
    });
  });

  const onPanInput = (e) => setServo("0", parseInt(e.target.value, 10));
  $("servo-pan").addEventListener("input", onPanInput);
  $("servo-pan").addEventListener("change", onPanInput);

  const onTiltInput = (e) => setServo("1", parseInt(e.target.value, 10));
  $("servo-tilt").addEventListener("input", onTiltInput);
  $("servo-tilt").addEventListener("change", onTiltInput);

  $("camera-reload").addEventListener("click", () => {
    const img = $("camera");
    img.src = `/stream?ts=${Date.now()}`;
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
