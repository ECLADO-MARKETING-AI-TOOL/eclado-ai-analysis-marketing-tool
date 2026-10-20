import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
const source = readFileSync("admin/eclado_admin/assets/demo_session.js", "utf8");
const {default: render} = await import(`data:text/javascript;base64,${Buffer.from(source).toString("base64")}`);
const values = new Map();
globalThis.sessionStorage = {
    getItem: key => values.get(key) ?? null,
    setItem: (key,value) => values.set(key,value),
    removeItem: key => values.delete(key),
};
globalThis.window = {};
let now = 1000000;
Date.now = () => now;
let timeout;
globalThis.setTimeout = (callback, delay) => {timeout = {callback, delay}; return 1;};
globalThis.clearTimeout = () => {};
const state = {};
const props = data => ({data,
    setStateValue: (key,value) => {state[key] = value;},
    setTriggerValue: (key,value) => {state[key] = value;},
});
const deadline = now + 3600000;
render(props({mode:"write",token:"opaque-test-token",expires:deadline}));
assert.equal(state.stored,"opaque-test-token");
assert.equal(timeout.delay,3600000);
globalThis.window = {}; // Full refresh drops frontend memory, retaining tab storage.
now += 120000;
render(props({mode:"read"}));
assert.equal(state.stored,"opaque-test-token");
assert.equal(timeout.delay,3480000);
assert.equal(JSON.parse([...values.values()][0]).expires,deadline);
// A new Streamlit session may reconnect without reloading the JS window.
delete state.stored;
render(props({mode:"read",request_id:"new-websocket-session"}));
assert.equal(state.stored,"opaque-test-token");
now = deadline;
timeout.callback();
assert.equal(state.stored,null);
assert.equal(state.expired,true);
assert.equal(values.size,0);
render(props({mode:"write",token:"second",expires:now+3600000}));
render(props({mode:"clear"}));
assert.equal(values.size,0);
globalThis.window = {};
render(props({mode:"read"}));
assert.equal(state.stored,null);
values.set("eclado.preview.session.v1",JSON.stringify({token:"expired",expires:now-1}));
render(props({mode:"read"}));
assert.equal(values.size,0);
globalThis.sessionStorage = {
    getItem: () => {throw new Error("blocked");},
    setItem: () => {throw new Error("blocked");},
    removeItem: () => {throw new Error("blocked");},
};
render(props({mode:"read"})); // Storage failures fail closed and never crash the UI.
console.log("refresh, fixed expiry, timeout, logout, blocked storage passed");
