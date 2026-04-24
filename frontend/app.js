const config = {
  apiBaseUrl: "https://REPLACE_WITH_API_DOMAIN",
  cognitoDomain: "REPLACE_WITH_COGNITO_DOMAIN_PREFIX.auth.REGION.amazoncognito.com",
  clientId: "REPLACE_WITH_COGNITO_APP_CLIENT_ID",
  redirectUri: "https://REPLACE_WITH_UI_DOMAIN",
  region: "REPLACE_WITH_REGION",
  scope: "openid email profile"
};

const statusEl = document.getElementById("status");
const resultsEl = document.getElementById("results");
const loginBtn = document.getElementById("loginBtn");
const logoutBtn = document.getElementById("logoutBtn");
const form = document.getElementById("searchForm");

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.style.color = isError ? "#c1121f" : "#1b1f2a";
}

function getTokenFromHash() {
  if (!window.location.hash) return null;
  const hash = new URLSearchParams(window.location.hash.substring(1));
  return hash.get("id_token");
}

function storeToken(token) {
  localStorage.setItem("id_token", token);
}

function getStoredToken() {
  return localStorage.getItem("id_token");
}

function clearToken() {
  localStorage.removeItem("id_token");
}

function login() {
  const loginUrl =
    `https://${config.cognitoDomain}/login?client_id=${encodeURIComponent(config.clientId)}` +
    `&response_type=token&scope=${encodeURIComponent(config.scope)}` +
    `&redirect_uri=${encodeURIComponent(config.redirectUri)}`;
  window.location.assign(loginUrl);
}

function logout() {
  clearToken();
  const logoutUrl =
    `https://${config.cognitoDomain}/logout?client_id=${encodeURIComponent(config.clientId)}` +
    `&logout_uri=${encodeURIComponent(config.redirectUri)}`;
  window.location.assign(logoutUrl);
}

function parseLocalDateTime(date, time) {
  return new Date(`${date}T${time}:00`);
}

function renderResults(items) {
  resultsEl.innerHTML = "";
  if (!items.length) {
    resultsEl.innerHTML = "<p>No media found for selected filters.</p>";
    return;
  }

  items.forEach((item) => {
    const card = document.createElement("article");
    card.className = "result-card";
    const mediaTag = item.mediaType === "video"
      ? `<video controls src="${item.url}"></video>`
      : `<img src="${item.url}" alt="${item.objectKey}">`;

    card.innerHTML =
      `${mediaTag}
      <div class="result-meta">
        <div><strong>Camera:</strong> ${item.cameraId}</div>
        <div><strong>Location:</strong> ${item.locationId}</div>
        <div><strong>Timestamp:</strong> ${new Date(item.captureTime).toLocaleString()}</div>
        <div><strong>Object:</strong> ${item.objectKey}</div>
        <div><a href="${item.url}" target="_blank" rel="noreferrer">Open in new tab</a></div>
      </div>`;
    resultsEl.appendChild(card);
  });
}

async function searchMedia(payload, token) {
  const response = await fetch(`${config.apiBaseUrl}/search`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    throw new Error(errorBody.message || `API error ${response.status}`);
  }
  return response.json();
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const token = getStoredToken();
  if (!token) {
    setStatus("Please sign in first.", true);
    return;
  }

  const cameraId = document.getElementById("cameraId").value.trim();
  const locationId = document.getElementById("locationId").value.trim();
  const date = document.getElementById("date").value;
  const startTime = document.getElementById("startTime").value;
  const endTime = document.getElementById("endTime").value;
  const mediaType = document.getElementById("mediaType").value;

  const start = parseLocalDateTime(date, startTime);
  const end = parseLocalDateTime(date, endTime);
  if (start >= end) {
    setStatus("End time must be greater than start time.", true);
    return;
  }

  const payload = {
    cameraId,
    locationId,
    startTimeIso: start.toISOString(),
    endTimeIso: end.toISOString(),
    mediaType
  };

  setStatus("Searching...");
  try {
    const data = await searchMedia(payload, token);
    renderResults(data.items || []);
    setStatus(`Found ${data.items?.length || 0} item(s).`);
  } catch (err) {
    setStatus(err.message, true);
  }
});

document.getElementById("clearBtn").addEventListener("click", () => {
  form.reset();
  resultsEl.innerHTML = "";
  setStatus("");
});

loginBtn.addEventListener("click", login);
logoutBtn.addEventListener("click", logout);

const tokenFromHash = getTokenFromHash();
if (tokenFromHash) {
  storeToken(tokenFromHash);
  history.replaceState(null, document.title, window.location.pathname);
}

setStatus(getStoredToken() ? "Authenticated. Ready to search." : "Sign in with Microsoft SSO.");
