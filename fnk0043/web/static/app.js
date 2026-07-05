(() => {
  const wsUrl = `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`;
  let ws;
  let speed = 0.6;
  let activeDir = null;
  let reconnectTimer;
  let drivePulseTimer = null;
  let servoDebounce = null;
  let lastPanAngle = null;
  let lastTiltAngle = null;

  const DRIVE_PULSE_MS = 120;
  const SERVO_DEBOUNCE_MS = 80;
  const STATUS_INTERVAL_MS = 2500;

  const $ = (id) => document.getElementById(id);

  function connect() {
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      $("conn-status").textContent = "Online";
      $("conn-status").className = "badge online";
      send({ action: "status" });
      setServo("0", parseInt($("servo-pan").value, 10), true);
      setServo("1", parseInt($("servo-tilt").value, 10), true);
    };

    ws.onclose = () => {
      $("conn-status").textContent = "Offline";
      $("conn-status").className = "badge offline";
      stopDrivePulse();
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

  function setServo(channel, angle, immediate = false) {
    angle = Math.max(30, Math.min(150, angle));
    const isPan = channel === "0";
    if (isPan && lastPanAngle === angle && !immediate) return;
    if (!isPan && lastTiltAngle === angle && !immediate) return;

    const slider = isPan ? $("servo-pan") : $("servo-tilt");
    const label = isPan ? $("pan-angle") : $("tilt-angle");
    slider.value = String(angle);
    label.textContent = `${angle} deg`;

    if (isPan) lastPanAngle = angle;
    else lastTiltAngle = angle;

    const dispatch = () => {
      send({ action: "servo", channel, angle });
    };

    if (immediate) {
      dispatch();
      return;
    }

    clearTimeout(servoDebounce);
    servoDebounce = setTimeout(dispatch, SERVO_DEBOUNCE_MS);
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

  function sendDrive(direction) {
    if (direction === "stop") {
      send({ action: "stop" });
      return;
    }
    send({ action: "drive", direction, speed });
  }

  function stopDrivePulse() {
    if (drivePulseTimer) {
      clearInterval(drivePulseTimer);
      drivePulseTimer = null;
    }
  }

  function startDrivePulse(direction) {
    stopDrivePulse();
    sendDrive(direction);
    drivePulseTimer = setInterval(() => sendDrive(direction), DRIVE_PULSE_MS);
  }

  document.querySelectorAll(".dpad-btn").forEach((btn) => {
    const dir = btn.dataset.dir;

    btn.addEventListener("pointerdown", (e) => {
      e.preventDefault();
      btn.setPointerCapture(e.pointerId);
      btn.classList.add("active");
      activeDir = dir;
      if (dir === "stop") {
        stopDrivePulse();
        sendDrive("stop");
      } else {
        startDrivePulse(dir);
      }
    });

    btn.addEventListener("pointerup", (e) => {
      e.preventDefault();
      btn.classList.remove("active");
      if (activeDir === dir && dir !== "stop") {
        stopDrivePulse();
        sendDrive("stop");
      }
      activeDir = null;
    });

    btn.addEventListener("pointercancel", () => {
      btn.classList.remove("active");
      stopDrivePulse();
      if (activeDir && activeDir !== "stop") {
        sendDrive("stop");
      }
      activeDir = null;
    });
  });

  $("speed").addEventListener("input", (e) => {
    speed = parseFloat(e.target.value);
    if (activeDir && activeDir !== "stop") {
      sendDrive(activeDir);
    }
  });

  document.querySelectorAll(".mode-buttons button").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".mode-buttons button").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      stopDrivePulse();
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

  $("servo-pan").addEventListener("input", (e) => setServo("0", parseInt(e.target.value, 10)));
  $("servo-tilt").addEventListener("input", (e) => setServo("1", parseInt(e.target.value, 10)));

  $("camera-reload").addEventListener("click", () => {
    $("camera").src = `/stream?ts=${Date.now()}`;
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
  }, STATUS_INTERVAL_MS);
})();
