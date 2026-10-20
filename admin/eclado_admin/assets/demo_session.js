// Only an opaque preview token is stored. No password or customer data.
export default function(component) {
    const { data, setStateValue, setTriggerValue } = component;
    const storageKey = "eclado.preview.session.v1";
    let session = null;
    let timer;
    try {
        if (data.mode === "clear") {
            sessionStorage.removeItem(storageKey);
        } else if (data.mode === "write") {
            session = {token: data.token, expires: data.expires};
            sessionStorage.setItem(storageKey, JSON.stringify(session));
        } else {
            session = JSON.parse(sessionStorage.getItem(storageKey) || "null");
        }
        if (session && (typeof session.token !== "string" ||
            !Number.isFinite(session.expires) || session.expires <= Date.now())) {
            sessionStorage.removeItem(storageKey);
            session = null;
        }
    } catch {
        // Login still works if storage is blocked, but cannot survive refresh.
        session = data.mode === "write" ? {token: data.token, expires: data.expires} : null;
    }
    const stored = session ? session.token : null;
    const report = JSON.stringify([data.request_id, stored]);
    if (window.__ecladoReportedSession !== report) {
        window.__ecladoReportedSession = report;
        setStateValue("stored", stored);
    }
    if (session) {
        timer = setTimeout(() => {
            try { sessionStorage.removeItem(storageKey); } catch { /* blocked storage */ }
            window.__ecladoReportedSession = JSON.stringify([data.request_id, null]);
            setStateValue("stored", null);
            setTriggerValue("expired", true);
        }, Math.max(0, session.expires - Date.now()));
    }
    return () => { if (timer !== undefined) clearTimeout(timer); };
}
